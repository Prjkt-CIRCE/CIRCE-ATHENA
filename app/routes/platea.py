"""
platea.py — AT-03.5
Rotas web da Platea: listagem e detalhe de casos compartilhados.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.services.platea_service import (
    get_case_list, get_case_by_ref, count_cases, log_platea_access
)

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
        "request":     request,
        "operator":    operator,
        "cases":       cases,
        "total":       total,
        "page":        page,
        "total_pages": total_pages,
    })


@router.get("/platea/{case_ref:path}", response_class=HTMLResponse)
async def platea_detail(request: Request, case_ref: str):
    operator = request.session.get("operator", {})

    db = SessionLocal()
    try:
        case = get_case_by_ref(db, case_ref)
        if not case:
            return RedirectResponse(url="/platea", status_code=302)

        # Registra acesso no log (CA-AT03.5)
        log_platea_access(
            db=db,
            shared_case=case,
            operator_id=operator.get("id", 0),
            operator_login=operator.get("username", "desconhecido"),
            ip_address=request.client.host if request.client else None,
        )

        # Carrega listas enquanto sessao ainda esta aberta
        persons   = list(case.persons)
        documents = list(case.documents)
        links     = list(case.links)
    finally:
        db.close()

    return templates.TemplateResponse("platea_detail.html", {
        "request":   request,
        "operator":  operator,
        "case":      case,
        "persons":   persons,
        "documents": documents,
        "links":     links,
    })