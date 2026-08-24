"""Gestor de Investigações — listagem, criação nativa e detalhe de casos."""

from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.services.audit_service import log_action
from app.services.case_intake_service import (
    CaseIntakeError,
    cleanup_stored_paths,
    create_native_case,
    ingest_case_uploads,
)
from app.services.platea_service import (
    get_case_list, get_case_by_ref, count_cases, log_platea_access
)
from app.services.work_topic_service import bootstrap_mobile_analysis_topics
from app.services.workspace_service import open_workspace

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/platea", response_class=HTMLResponse)
async def platea_list(request: Request, page: int = 1):
    operator = request.session.get("operator", {})
    limit = 50
    skip = (page - 1) * limit

    db = SessionLocal()
    try:
        cases = get_case_list(db, skip=skip, limit=limit)
        total = count_cases(db)
        total_pages = max(1, (total + limit - 1) // limit)
    finally:
        db.close()

    return templates.TemplateResponse("platea_list.html", {
        "request": request,
        "operator": operator,
        "cases": cases,
        "total": total,
        "page": page,
        "total_pages": total_pages,
    })


@router.get("/cases/new", response_class=HTMLResponse)
async def native_case_new(request: Request):
    operator = request.session.get("operator", {})
    return templates.TemplateResponse("case_new.html", {
        "request": request,
        "operator": operator,
        "error": None,
        "values": {},
    })


@router.post("/cases", response_class=HTMLResponse)
async def native_case_create(request: Request):
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    form = await request.form()
    title = str(form.get("title") or "")
    classification = str(form.get("classification") or "")
    source_unit = str(form.get("source_unit") or operator.get("unit") or "")
    notes = str(form.get("notes") or "")
    product_template = str(form.get("product_template") or "mobile_analysis")
    uploads = [item for item in form.getlist("files") if getattr(item, "filename", None)]
    created_paths: list[str] = []

    db = SessionLocal()
    try:
        case = create_native_case(
            db,
            title=title,
            classification=classification,
            notes=notes,
            source_unit=source_unit,
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
        )
        documents, created_paths, duplicates = await ingest_case_uploads(
            db,
            case=case,
            uploads=uploads,
            operator_username=operator.get("username"),
        )
        workspace, _ = open_workspace(
            db,
            case_ref=case.case_ref,
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
        )
        if not workspace:
            raise CaseIntakeError("Não foi possível abrir o Workspace do novo caso.")

        first_topic_id = None
        if product_template == "mobile_analysis":
            topics, _ = bootstrap_mobile_analysis_topics(
                db,
                workspace=workspace,
                operator_id=operator.get("id"),
                operator_username=operator.get("username"),
            )
            first_topic_id = topics[0].id if topics else None

        log_action(
            db,
            action="native_case_created",
            description=(
                f"Caso nativo {case.case_ref} criado no ATHENA por {operator.get('username') or 'operador'}. "
                f"Materiais iniciais: {len(documents)}; duplicados ignorados: {duplicates}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="case",
            entity_id=case.case_ref,
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()

        target = f"/workspace/{quote(case.case_ref, safe='/._-')}"
        if first_topic_id:
            target += f"?topic={first_topic_id}"
        return RedirectResponse(url=target, status_code=303)
    except CaseIntakeError as exc:
        db.rollback()
        cleanup_stored_paths(created_paths)
        return templates.TemplateResponse("case_new.html", {
            "request": request,
            "operator": operator,
            "error": str(exc),
            "values": {
                "title": title,
                "classification": classification,
                "source_unit": source_unit,
                "notes": notes,
                "product_template": product_template,
            },
        }, status_code=400)
    except Exception:
        db.rollback()
        cleanup_stored_paths(created_paths)
        raise
    finally:
        db.close()


@router.get("/platea/{case_ref:path}", response_class=HTMLResponse)
async def platea_detail(request: Request, case_ref: str):
    operator = request.session.get("operator", {})

    db = SessionLocal()
    try:
        case = get_case_by_ref(db, case_ref)
        if not case:
            return RedirectResponse(url="/platea", status_code=302)

        log_platea_access(
            db=db,
            shared_case=case,
            operator_id=operator.get("id", 0),
            operator_login=operator.get("username", "desconhecido"),
            ip_address=request.client.host if request.client else None,
        )

        persons = list(case.persons)
        documents = list(case.documents)
        links = list(case.links)
    finally:
        db.close()

    return templates.TemplateResponse("platea_detail.html", {
        "request": request,
        "operator": operator,
        "case": case,
        "persons": persons,
        "documents": documents,
        "links": links,
    })
