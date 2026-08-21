from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models.platea import SharedCase
from app.models.workspace import InvestigativeBlock, InvestigativeWorkspace
from app.services.audit_service import log_action
from app.services.workspace_service import (
    create_block,
    discard_block,
    list_blocks,
    open_workspace,
    remove_block_source,
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
async def workspace_detail(request: Request, case_ref: str, block: int | None = None):
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
        links = list(case.links)
        annotations = list(case.annotations)
        blocks = list_blocks(db, workspace.id)
        active_block = next((item for item in blocks if item.id == block), None)

        return templates.TemplateResponse("workspace.html", {
            "request": request,
            "operator": operator,
            "case": case,
            "workspace": workspace,
            "persons": persons,
            "documents": documents,
            "links": links,
            "annotations": annotations,
            "blocks": blocks,
            "active_block": active_block,
        })
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
