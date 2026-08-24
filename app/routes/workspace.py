from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models.platea import SharedCase, SharedDocument
from app.models.workspace import InvestigativeBlock, InvestigativeWorkspace
from app.services.audit_service import log_action
from app.services.case_intake_service import (
    CaseIntakeError,
    cleanup_stored_paths,
    ingest_case_uploads,
    resolve_document_storage_path,
)
from app.services.investigative_analysis_service import (
    create_excerpt_draft,
    discard_excerpt,
    list_excerpt_drafts,
    list_findings,
    propose_analysis,
    resolve_excerpt_sources,
    validate_finding,
)
from app.services.report_header_service import (
    confirm_workspace_header,
    create_header_template,
    get_or_create_workspace_header,
    header_payload,
    header_source_tokens,
    header_template_payload,
    list_header_templates,
    update_workspace_header,
)
from app.services.report_header_extraction_service import (
    field_sources_payload,
    propose_header_extraction,
    store_header_extraction,
)
from app.services.report_archive_service import sync_report_archive
from app.services.report_topic_composition_service import (
    composition_payload,
    confirm_topic_composition,
    get_or_create_topic_composition,
    get_topic_composition,
    propose_fact_map,
    propose_narrative_blocks,
    save_fact_map,
    save_narrative_blocks,
    store_fact_map,
    store_narrative_blocks,
)
from app.services.work_topic_service import (
    bootstrap_mobile_analysis_topics,
    choose_active_topic,
    get_work_topic,
    list_work_topics,
    next_incomplete_topic,
    update_work_topic_status,
)
from app.services.workspace_service import (
    add_block_sources,
    create_block,
    discard_block,
    list_blocks,
    open_workspace,
    remove_block_source,
    resolve_case_source_token,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/workspace/open/{case_ref:path}")
async def workspace_open(request: Request, case_ref: str):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    db = SessionLocal()
    try:
        workspace, created = open_workspace(
            db,
            case_ref=case_ref,
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
        )
        if not workspace:
            db.rollback()
            return RedirectResponse(url="/platea", status_code=303)

        log_action(
            db,
            action="workspace_created" if created else "workspace_opened",
            description=(
                f"Workspace investigativo {'criado' if created else 'aberto'} "
                f"para o caso {case_ref}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="investigative_workspace",
            entity_id=str(workspace.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return RedirectResponse(
            url=f"/workspace/{quote(case_ref, safe='/._-')}",
            status_code=303,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.get("/workspace/{case_ref:path}", response_class=HTMLResponse)
async def workspace_detail(
    request: Request,
    case_ref: str,
    block: int | None = None,
    topic: int | None = None,
    pane: str | None = None,
):
    operator = request.session.get("operator", {})
    db = SessionLocal()
    try:
        case = db.query(SharedCase).filter(SharedCase.case_ref == case_ref).first()
        if not case:
            return RedirectResponse(url="/platea", status_code=302)

        workspace = (
            db.query(InvestigativeWorkspace)
            .filter(InvestigativeWorkspace.shared_case_id == case.id)
            .first()
        )
        if not workspace:
            return RedirectResponse(
                url=f"/platea/{quote(case_ref, safe='/._-')}",
                status_code=302,
            )

        persons = list(case.persons)
        documents = list(case.documents)
        intake_documents = [item for item in documents if getattr(item, "intake_bin", None) == "inbox"]
        links = list(case.links)
        annotations = list(case.annotations)
        blocks = list_blocks(db, workspace.id)
        active_block = next((item for item in blocks if item.id == block), None)
        excerpt_drafts = list_excerpt_drafts(db, workspace.id)
        findings = list_findings(db, workspace.id)
        work_topics = list_work_topics(db, workspace.id)
        active_topic = choose_active_topic(work_topics, topic)
        next_topic = next_incomplete_topic(work_topics, active_topic.id) if active_topic else None
        pane_mode = pane if pane in {"pool", "work", "athena"} else None

        report_header = get_or_create_workspace_header(
            db,
            workspace=workspace,
            case=case,
            operator_username=operator.get("username"),
        )
        header_templates = list_header_templates(db)
        report_header_payload = header_payload(report_header)
        header_template_payloads = [header_template_payload(item) for item in header_templates]
        sync_report_archive(
            db,
            workspace=workspace,
            case=case,
            header=report_header,
            operator_username=operator.get("username"),
        )
        report_header_field_sources = field_sources_payload(report_header)

        topic_composition = None
        if active_topic and active_topic.topic_key == "facts":
            topic_composition = get_or_create_topic_composition(
                db,
                workspace=workspace,
                work_topic=active_topic,
                operator_username=operator.get("username"),
            )
        topic_composition_payload = composition_payload(topic_composition)
        db.commit()
        topic_excerpt_drafts = [item for item in excerpt_drafts if not active_topic or item.work_topic_id == active_topic.id]
        topic_findings = [item for item in findings if not active_topic or item.work_topic_id == active_topic.id]
        excerpt_draft_payloads = [
            {
                "id": item.id,
                "title": item.title,
                "analyst_note": item.analyst_note,
                "objective_summary": item.proposed_summary,
                "interpretation": item.proposed_interpretation or "",
                "suggested_type": item.suggested_type,
                "support_gaps": __import__("json").loads(item.support_gaps or "[]"),
                "source_count": len(item.sources),
                "sources": [source.source_label_snapshot for source in item.sources],
                "work_topic_id": item.work_topic_id,
            }
            for item in topic_excerpt_drafts
        ]

        # AT06B61_SMART_BIN_PROVENANCE_V1
        used_source_identities: set[tuple[str, str]] = set()
        if active_topic:
            if active_topic.topic_key == "header":
                used_source_identities.update(
                    (source.source_type, source.source_key)
                    for source in report_header.sources
                )
            if topic_composition:
                used_source_identities.update(
                    (source.source_type, source.source_key)
                    for source in topic_composition.sources
                )
            for excerpt in topic_excerpt_drafts:
                used_source_identities.update(
                    (source.source_type, source.source_key)
                    for source in excerpt.sources
                )
            for finding in topic_findings:
                if finding.excerpt:
                    used_source_identities.update(
                        (source.source_type, source.source_key)
                        for source in finding.excerpt.sources
                    )

        active_topic_used_source_tokens: list[str] = []
        candidate_tokens = (
            [f"person:{item.id}" for item in persons]
            + [f"document:{item.id}" for item in documents]
            + [f"link:{item.id}" for item in links]
            + [f"annotation:{item.id}" for item in annotations]
        )
        if used_source_identities:
            for source_token in candidate_tokens:
                resolved = resolve_case_source_token(db, case, source_token)
                if resolved and (resolved["source_type"], resolved["source_key"]) in used_source_identities:
                    active_topic_used_source_tokens.append(source_token)

        return templates.TemplateResponse("workspace.html", {
            "request": request,
            "operator": operator,
            "case": case,
            "workspace": workspace,
            "persons": persons,
            "documents": documents,
            "intake_documents": intake_documents,
            "links": links,
            "annotations": annotations,
            "blocks": blocks,
            "active_block": active_block,
            "excerpt_drafts": topic_excerpt_drafts,
            "excerpt_draft_payloads": excerpt_draft_payloads,
            "findings": topic_findings,
            "work_topics": work_topics,
            "active_topic": active_topic,
            "next_topic": next_topic,
            "pane_mode": pane_mode,
            "report_header": report_header,
            "report_header_payload": report_header_payload,
            "report_header_source_tokens": header_source_tokens(report_header),
            "header_templates": header_templates,
            "header_template_payloads": header_template_payloads,
            "report_header_field_sources": report_header_field_sources,
            "active_topic_used_source_tokens": active_topic_used_source_tokens,
            "topic_composition": topic_composition,
            "topic_composition_payload": topic_composition_payload,
        })
    finally:
        db.close()


# AT06B52_POOL_PREVIEW_REPORT_HEADER_V1
@router.get("/api/workspaces/{workspace_id}/documents/{document_id}/content")
async def workspace_document_content(
    request: Request,
    workspace_id: int,
    document_id: int,
):
    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)

        document = (
            db.query(SharedDocument)
            .filter(
                SharedDocument.id == document_id,
                SharedDocument.shared_case_id == workspace.shared_case_id,
            )
            .first()
        )
        if not document:
            return JSONResponse({"error": "Documento não encontrado neste caso."}, status_code=404)

        path = resolve_document_storage_path(document)
        if not path:
            return JSONResponse(
                {"error": "Este material não possui original local disponível para preview."},
                status_code=404,
            )

        return FileResponse(
            path=str(path),
            media_type=document.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{quote(document.filename)}"
            },
        )
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/report-header")
async def workspace_report_header_save(request: Request, workspace_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    raw_sources = payload.get("source_tokens", []) if isinstance(payload, dict) else []
    source_tokens = [str(item) for item in raw_sources if isinstance(item, (str, int))]

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        header = update_workspace_header(
            db,
            workspace=workspace,
            case=case,
            payload=payload if isinstance(payload, dict) else {},
            source_tokens=source_tokens,
            operator_username=operator.get("username"),
        )
        product = sync_report_archive(
            db, workspace=workspace, case=case, header=header,
            operator_username=operator.get("username"),
        )

        log_action(
            db,
            action="report_header_updated",
            description=(
                f"Cabeçalho estruturado do caso {case.case_ref} atualizado por "
                f"{operator.get('username') or 'operador'} com {len(header.sources)} fonte(s)."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="workspace_report_header",
            entity_id=str(header.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({
            "ok": True,
            "header": header_payload(header),
            "source_count": len(header.sources),
            "review_status": header.review_status,
            "product_key": product.product_key,
        })
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()



@router.post("/api/workspaces/{workspace_id}/report-header/extract")
async def workspace_report_header_extract(request: Request, workspace_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    raw_sources = payload.get("source_tokens", []) if isinstance(payload, dict) else []
    source_tokens = [str(item) for item in raw_sources if isinstance(item, (str, int))]

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)
        header = get_or_create_workspace_header(
            db, workspace=workspace, case=case,
            operator_username=operator.get("username"),
        )

        if not source_tokens:
            source_tokens = header_source_tokens(header)
        document_ids: list[int] = []
        for token in source_tokens:
            if not str(token).startswith("document:"):
                continue
            try:
                document_ids.append(int(str(token).split(":", 1)[1]))
            except (TypeError, ValueError):
                continue
        document_ids = list(dict.fromkeys(document_ids))[:12]
        if not document_ids:
            return JSONResponse(
                {"error": "Selecione no Pool pelo menos um PDF para extrair o cabeçalho."},
                status_code=400,
            )

        documents = (
            db.query(SharedDocument)
            .filter(
                SharedDocument.shared_case_id == case.id,
                SharedDocument.id.in_(document_ids),
            )
            .order_by(SharedDocument.id)
            .all()
        )
        if not documents:
            return JSONResponse({"error": "Nenhum documento selecionado foi encontrado."}, status_code=404)

        try:
            fields, warnings, notes = await propose_header_extraction(documents=documents)
        except (ValueError, RuntimeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return JSONResponse(
                {"error": f"Não foi possível executar a extração local: {exc}"},
                status_code=503,
            )

        store_header_extraction(db, header=header, fields=fields)
        log_action(
            db,
            action="report_header_extraction_proposed",
            description=(
                f"Athena propôs campos do cabeçalho do caso {case.case_ref} a partir de "
                f"{len(documents)} documento(s). Nenhum campo foi confirmado automaticamente."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="workspace_report_header",
            entity_id=str(header.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({
            "ok": True,
            "fields": fields,
            "warnings": warnings,
            "notes": notes,
            "review_status": header.review_status,
        })
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/report-header/confirm")
async def workspace_report_header_confirm(request: Request, workspace_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    raw_sources = payload.get("source_tokens", []) if isinstance(payload, dict) else []
    source_tokens = [str(item) for item in raw_sources if isinstance(item, (str, int))]

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        header = confirm_workspace_header(
            db,
            workspace=workspace,
            case=case,
            payload=payload if isinstance(payload, dict) else {},
            source_tokens=source_tokens,
            operator_username=operator.get("username"),
        )
        product = sync_report_archive(
            db, workspace=workspace, case=case, header=header,
            operator_username=operator.get("username"),
            intake_bin=intake_bin,
        )
        log_action(
            db,
            action="report_header_confirmed",
            description=(
                f"Cabeçalho do caso {case.case_ref} confirmado por "
                f"{operator.get('username') or 'operador'}; produto indexado no acervo como {product.product_key}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="report_product",
            entity_id=product.product_key,
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({
            "ok": True,
            "header": header_payload(header),
            "review_status": header.review_status,
            "product_key": product.product_key,
        })
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/report-header-templates")
async def report_header_template_create(request: Request):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    db = SessionLocal()
    try:
        try:
            template = create_header_template(
                db,
                name=str(payload.get("name") or "") if isinstance(payload, dict) else "",
                payload=payload if isinstance(payload, dict) else {},
                operator_username=operator.get("username"),
                make_default=bool(payload.get("make_default")) if isinstance(payload, dict) else False,
            )
        except ValueError as exc:
            db.rollback()
            return JSONResponse({"error": str(exc)}, status_code=400)

        log_action(
            db,
            action="report_header_template_created",
            description=f"Template de cabeçalho '{template.name}' criado.",
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="report_header_template",
            entity_id=str(template.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({"ok": True, "template": header_template_payload(template)})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# AT06B5_NATIVE_CASE_INTAKE_V1
@router.post("/api/workspaces/{workspace_id}/intake/files")
async def workspace_intake_files(request: Request, workspace_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    form = await request.form()
    uploads = [item for item in form.getlist("files") if getattr(item, "filename", None)]
    requested_bin = str(form.get("bin_hint") or "").strip().lower()
    allowed_manual_bins = {"persons", "documents", "images", "audio", "video"}
    intake_bin = requested_bin if requested_bin in allowed_manual_bins else None
    created_paths: list[str] = []

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)
        if case.origin_type != "native" or not case.case_uuid:
            return JSONResponse(
                {"error": "Este caso ainda não possui armazenamento nativo do ATHENA. Crie novos casos pelo Gestor para adicionar materiais ao Pool."},
                status_code=400,
            )

        documents, created_paths, duplicates = await ingest_case_uploads(
            db,
            case=case,
            uploads=uploads,
            operator_username=operator.get("username"),
            intake_bin=intake_bin,
        )
        log_action(
            db,
            action="case_material_ingested",
            description=(
                f"{len(documents)} material(is) adicionado(s) ao Pool do caso {case.case_ref}; "
                f"duplicados ignorados: {duplicates}; destino manual: {intake_bin or 'automático'}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="case",
            entity_id=case.case_ref,
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({"ok": True, "added": len(documents), "duplicates": duplicates, "bin": intake_bin or "auto"})
    except CaseIntakeError as exc:
        db.rollback()
        cleanup_stored_paths(created_paths)
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception:
        db.rollback()
        cleanup_stored_paths(created_paths)
        raise
    finally:
        db.close()


# AT06B63_FACTS_TOPIC_COMPOSITION_V1
@router.post("/api/workspaces/{workspace_id}/topics/{topic_id}/facts/extract")
async def workspace_topic_facts_extract(request: Request, workspace_id: int, topic_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    payload = await request.json()
    source_tokens = payload.get("source_tokens") if isinstance(payload, dict) else []
    if not isinstance(source_tokens, list):
        source_tokens = []

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        topic = get_work_topic(db, workspace_id=workspace_id, topic_id=topic_id)
        if not topic or topic.topic_key != "facts":
            return JSONResponse({"error": "Este endpoint é exclusivo do tópico Dos fatos / introdução."}, status_code=400)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso não encontrado."}, status_code=404)

        composition = get_or_create_topic_composition(
            db, workspace=workspace, work_topic=topic,
            operator_username=operator.get("username"),
        )
        if not source_tokens and composition.sources:
            identities = {(item.source_type, item.source_key) for item in composition.sources}
            for document in case.documents:
                token = f"document:{document.id}"
                resolved = resolve_case_source_token(db, case, token)
                if resolved and (resolved["source_type"], resolved["source_key"]) in identities:
                    source_tokens.append(token)
        resolved_sources: list[dict] = []
        documents: list[SharedDocument] = []
        seen_docs: set[int] = set()
        for token in source_tokens:
            resolved = resolve_case_source_token(db, case, str(token))
            if not resolved:
                continue
            resolved_sources.append(resolved)
            if str(token).startswith("document:"):
                try:
                    document_id = int(str(token).split(":", 1)[1])
                except (TypeError, ValueError):
                    continue
                document = db.query(SharedDocument).filter(
                    SharedDocument.id == document_id,
                    SharedDocument.shared_case_id == case.id,
                ).first()
                if document and document.id not in seen_docs:
                    seen_docs.add(document.id)
                    documents.append(document)
        if not documents:
            return JSONResponse(
                {"error": "Adicione pelo menos um PDF/documento à Bandeja da Mesa para extrair o mapa factual."},
                status_code=400,
            )

        facts, warnings, notes = await propose_fact_map(documents=documents, topic=topic)
        store_fact_map(
            db, composition=composition,
            resolved_sources=resolved_sources,
            facts=facts,
            operator_username=operator.get("username"),
        )
        topic.status = "in_progress"
        log_action(
            db,
            action="topic_fact_map_extracted",
            description=f"Mapa factual proposto para {topic.title} com {len(documents)} documento(s).",
            operator_id=operator.get("id"), operator_username=operator.get("username"),
            entity_type="investigative_work_topic", entity_id=str(topic.id), ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        db.refresh(composition)
        return JSONResponse({
            "ok": True,
            "composition": composition_payload(get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic.id)),
            "warnings": warnings,
            "notes": notes,
        })
    except ValueError as exc:
        db.rollback()
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/topics/{topic_id}/facts/save")
async def workspace_topic_facts_save(request: Request, workspace_id: int, topic_id: int):
    operator = request.session.get("operator", {})
    payload = await request.json()
    db = SessionLocal()
    try:
        topic = get_work_topic(db, workspace_id=workspace_id, topic_id=topic_id)
        composition = get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic_id)
        if not topic or topic.topic_key != "facts" or not composition:
            return JSONResponse({"error": "Mapa factual não encontrado."}, status_code=404)
        facts = payload.get("facts") if isinstance(payload, dict) and isinstance(payload.get("facts"), list) else []
        save_fact_map(
            db, composition=composition,
            analyst_context=payload.get("analyst_context") if isinstance(payload, dict) else "",
            facts=facts,
            operator_username=operator.get("username"),
        )
        db.commit()
        return JSONResponse({"ok": True, "composition": composition_payload(get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic_id))})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/topics/{topic_id}/narrative/compose")
async def workspace_topic_narrative_compose(request: Request, workspace_id: int, topic_id: int):
    operator = request.session.get("operator", {})
    db = SessionLocal()
    try:
        topic = get_work_topic(db, workspace_id=workspace_id, topic_id=topic_id)
        composition = get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic_id)
        if not topic or topic.topic_key != "facts" or not composition:
            return JSONResponse({"error": "Mapa factual não encontrado."}, status_code=404)
        blocks = await propose_narrative_blocks(composition=composition, topic=topic)
        store_narrative_blocks(
            db, composition=composition, blocks=blocks,
            operator_username=operator.get("username"),
        )
        db.commit()
        return JSONResponse({"ok": True, "composition": composition_payload(get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic_id))})
    except ValueError as exc:
        db.rollback()
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/topics/{topic_id}/narrative/save")
async def workspace_topic_narrative_save(request: Request, workspace_id: int, topic_id: int):
    operator = request.session.get("operator", {})
    payload = await request.json()
    db = SessionLocal()
    try:
        topic = get_work_topic(db, workspace_id=workspace_id, topic_id=topic_id)
        composition = get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic_id)
        if not topic or topic.topic_key != "facts" or not composition:
            return JSONResponse({"error": "Composição do tópico não encontrada."}, status_code=404)
        blocks = payload.get("blocks") if isinstance(payload, dict) and isinstance(payload.get("blocks"), list) else []
        save_narrative_blocks(
            db, composition=composition, blocks=blocks,
            analyst_context=payload.get("analyst_context") if isinstance(payload, dict) else "",
            operator_username=operator.get("username"),
        )
        db.commit()
        return JSONResponse({"ok": True, "composition": composition_payload(get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic_id))})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/topics/{topic_id}/composition/confirm")
async def workspace_topic_composition_confirm(request: Request, workspace_id: int, topic_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        topic = get_work_topic(db, workspace_id=workspace_id, topic_id=topic_id)
        composition = get_topic_composition(db, workspace_id=workspace_id, work_topic_id=topic_id)
        if not workspace or not topic or topic.topic_key != "facts" or not composition:
            return JSONResponse({"error": "Composição do tópico não encontrada."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        header = get_or_create_workspace_header(
            db, workspace=workspace, case=case,
            operator_username=operator.get("username"),
        )
        confirm_topic_composition(
            db, composition=composition, topic=topic,
            operator_username=operator.get("username"),
        )
        sync_report_archive(
            db, workspace=workspace, case=case, header=header,
            operator_username=operator.get("username"),
        )
        log_action(
            db,
            action="topic_composition_confirmed",
            description=f"Tópico {topic.title} confirmado com narrativa estruturada.",
            operator_id=operator.get("id"), operator_username=operator.get("username"),
            entity_type="investigative_work_topic", entity_id=str(topic.id), ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({"ok": True, "status": "confirmed", "topic_status": topic.status})
    except ValueError as exc:
        db.rollback()
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# AT06B2_WORK_TOPICS_V1
@router.post("/api/workspaces/{workspace_id}/topics/bootstrap/mobile-analysis")
async def workspace_topics_bootstrap_mobile(request: Request, workspace_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        topics, created = bootstrap_mobile_analysis_topics(
            db, workspace=workspace, operator_id=operator.get("id"), operator_username=operator.get("username")
        )
        if created:
            log_action(
                db, action="investigative_work_topics_bootstrapped",
                description=f"Roteiro de análise de dispositivo móvel criado com {len(topics)} tópicos.",
                operator_id=operator.get("id"), operator_username=operator.get("username"),
                entity_type="investigative_workspace", entity_id=str(workspace.id), ip_address=ip,
                manage_transaction=False,
            )
        db.commit()
        return JSONResponse({"ok": True, "created": created, "first_topic_id": topics[0].id if topics else None})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/topics/{topic_id}/status")
async def workspace_topic_status(request: Request, workspace_id: int, topic_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    db = SessionLocal()
    try:
        topic, error = update_work_topic_status(
            db, workspace_id=workspace_id, topic_id=topic_id, status=str(payload.get("status") or "")
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)
        log_action(
            db, action="investigative_work_topic_status_changed",
            description=f"Tópico de trabalho {topic.id} ({topic.title}) alterado para {topic.status}.",
            operator_id=operator.get("id"), operator_username=operator.get("username"),
            entity_type="investigative_work_topic", entity_id=str(topic.id), ip_address=ip,
            manage_transaction=False,
        )
        topics = list_work_topics(db, workspace_id)
        nxt = next_incomplete_topic(topics, topic.id)
        db.commit()
        return JSONResponse({"ok": True, "topic_id": topic.id, "status": topic.status, "next_topic_id": nxt.id if nxt else None})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/blocks")
async def workspace_block_create(request: Request, workspace_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    form = await request.form()
    title = str(form.get("title") or "")
    summary = str(form.get("summary") or "")
    source_tokens = [str(value) for value in form.getlist("sources")]

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        new_block, error = create_block(
            db,
            workspace_id=workspace_id,
            title=title,
            summary=summary,
            source_tokens=source_tokens,
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)

        log_action(
            db,
            action="investigative_block_created",
            description=(
                f"Bloco investigativo {new_block.id} criado no caso {case.case_ref} "
                f"com {len(new_block.sources)} fonte(s)."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="investigative_block",
            entity_id=str(new_block.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return RedirectResponse(
            url=f"/workspace/{quote(case.case_ref, safe='/._-')}?block={new_block.id}",
            status_code=303,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# AT06B1_ANALYTICAL_CORE_V1
@router.post("/api/workspaces/{workspace_id}/analysis/propose")
async def workspace_analysis_propose(request: Request, workspace_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    analyst_note = str(payload.get("analyst_note") or "").strip() if isinstance(payload, dict) else ""
    raw_sources = payload.get("sources", []) if isinstance(payload, dict) else []
    source_tokens = [str(value) for value in raw_sources if isinstance(value, (str, int))]
    try:
        work_topic_id = int(payload.get("work_topic_id")) if isinstance(payload, dict) else 0
    except (TypeError, ValueError):
        work_topic_id = 0

    db = SessionLocal()
    try:
        workspace, case, resolved, error = resolve_excerpt_sources(
            db,
            workspace_id=workspace_id,
            source_tokens=source_tokens,
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)
        if not analyst_note:
            return JSONResponse({"error": "Registre a nota do analista antes de estruturar o recorte."}, status_code=400)

        work_topic = get_work_topic(db, workspace_id=workspace.id, topic_id=work_topic_id) if work_topic_id else None
        if not work_topic:
            db.rollback()
            return JSONResponse({"error": "Selecione um Tópico de Trabalho antes de estruturar a análise."}, status_code=400)

        proposal = await propose_analysis(
            case_ref=case.case_ref,
            analyst_note=analyst_note,
            sources=resolved,
            work_topic=work_topic,
        )
        excerpt = create_excerpt_draft(
            db,
            workspace=workspace,
            analyst_note=analyst_note,
            sources=resolved,
            proposal=proposal,
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            work_topic_id=work_topic.id,
        )
        log_action(
            db,
            action="investigative_excerpt_structured",
            description=(
                f"Recorte investigativo {excerpt.id} estruturado com Athena no caso {case.case_ref}; "
                f"{len(resolved)} fonte(s); aguardando validação humana."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="investigative_excerpt",
            entity_id=str(excerpt.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({
            "ok": True,
            "excerpt_id": excerpt.id,
            "title": proposal.title,
            "objective_summary": proposal.objective_summary,
            "interpretation": proposal.interpretation,
            "suggested_type": proposal.suggested_type,
            "support_gaps": proposal.support_gaps,
            "source_count": len(resolved),
            "sources": [item["label"] for item in resolved],
        })
    except Exception as exc:
        db.rollback()
        return JSONResponse({"error": f"Não foi possível estruturar o recorte: {exc}"}, status_code=503)
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/analysis/{excerpt_id}/validate")
async def workspace_analysis_validate(
    request: Request,
    workspace_id: int,
    excerpt_id: int,
):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        finding, error = validate_finding(
            db,
            workspace_id=workspace_id,
            excerpt_id=excerpt_id,
            title=str(payload.get("title") or ""),
            objective_summary=str(payload.get("objective_summary") or ""),
            interpretation=str(payload.get("interpretation") or ""),
            finding_type=str(payload.get("finding_type") or ""),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)

        log_action(
            db,
            action="investigative_finding_validated",
            description=(
                f"Achado investigativo {finding.id} validado explicitamente pelo operador no caso "
                f"{case.case_ref}; tipo: {finding.finding_type}; origem: recorte {excerpt_id}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="investigative_finding",
            entity_id=str(finding.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({
            "ok": True,
            "finding_id": finding.id,
            "excerpt_id": excerpt_id,
            "finding_type": finding.finding_type,
        })
    except Exception as exc:
        db.rollback()
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/analysis/{excerpt_id}/discard")
async def workspace_analysis_discard(
    request: Request,
    workspace_id: int,
    excerpt_id: int,
):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        excerpt, error = discard_excerpt(
            db,
            workspace_id=workspace_id,
            excerpt_id=excerpt_id,
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)

        log_action(
            db,
            action="investigative_excerpt_discarded",
            description=f"Recorte investigativo {excerpt.id} descartado no caso {case.case_ref}.",
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="investigative_excerpt",
            entity_id=str(excerpt.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({"ok": True, "excerpt_id": excerpt.id})
    except Exception as exc:
        db.rollback()
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        db.close()


# AT06A_POOL_DND_V1
@router.post("/api/workspaces/{workspace_id}/blocks/{block_id}/sources/add")
async def workspace_block_sources_add(
    request: Request,
    workspace_id: int,
    block_id: int,
):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    raw_sources = payload.get("sources", []) if isinstance(payload, dict) else []
    source_tokens = [str(value) for value in raw_sources if isinstance(value, (str, int))]

    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        block, added, error = add_block_sources(
            db,
            workspace_id=workspace_id,
            block_id=block_id,
            source_tokens=source_tokens,
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)

        if added:
            labels = ", ".join(item.source_label_snapshot for item in added[:4])
            if len(added) > 4:
                labels += f" e mais {len(added) - 4}"
            log_action(
                db,
                action="investigative_block_sources_added",
                description=(
                    f"{len(added)} fonte(s) adicionada(s) ao bloco investigativo {block_id} "
                    f"no caso {case.case_ref} por manipulação direta. {labels}"
                ),
                operator_id=operator.get("id"),
                operator_username=operator.get("username"),
                entity_type="investigative_block",
                entity_id=str(block_id),
                ip_address=ip,
                manage_transaction=False,
            )

        db.commit()
        return JSONResponse({
            "ok": True,
            "block_id": block.id,
            "added_count": len(added),
            "source_count": len(block.sources),
        })
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# AT06A_UNDO_V1
@router.post("/api/workspaces/{workspace_id}/blocks/{block_id}/sources/{source_id}/remove")
async def workspace_block_source_remove(
    request: Request,
    workspace_id: int,
    block_id: int,
    source_id: int,
):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        source, error = remove_block_source(
            db,
            workspace_id=workspace_id,
            block_id=block_id,
            source_id=source_id,
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)

        log_action(
            db,
            action="investigative_block_source_removed",
            description=(
                f"Fonte removida do bloco investigativo {block_id} no caso {case.case_ref}. "
                f"Tipo: {source.source_type}; chave: {source.source_key}; "
                f"rótulo: {source.source_label_snapshot}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="investigative_block",
            entity_id=str(block_id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return RedirectResponse(
            url=f"/workspace/{quote(case.case_ref, safe='/._-')}?block={block_id}",
            status_code=303,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/api/workspaces/{workspace_id}/blocks/{block_id}/undo")
async def workspace_block_undo(request: Request, workspace_id: int, block_id: int):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    db = SessionLocal()
    try:
        workspace = db.query(InvestigativeWorkspace).filter_by(id=workspace_id).first()
        if not workspace:
            return JSONResponse({"error": "Workspace não encontrado."}, status_code=404)
        case = db.query(SharedCase).filter_by(id=workspace.shared_case_id).first()
        if not case:
            return JSONResponse({"error": "Caso do Workspace não encontrado."}, status_code=404)

        block, error = discard_block(
            db,
            workspace_id=workspace_id,
            block_id=block_id,
        )
        if error:
            db.rollback()
            return JSONResponse({"error": error}, status_code=400)

        log_action(
            db,
            action="investigative_block_creation_undone",
            description=(
                f"Criação do bloco investigativo {block_id} desfeita no caso {case.case_ref}. "
                f"O bloco foi marcado como discarded; fontes originais não foram alteradas."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="investigative_block",
            entity_id=str(block_id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return RedirectResponse(
            url=f"/workspace/{quote(case.case_ref, safe='/._-')}",
            status_code=303,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
