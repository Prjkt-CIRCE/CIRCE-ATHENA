import secrets
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.services.auth_service import authenticate, has_any_operator, create_operator, get_operator_by_username
from app.services.audit_service import log_action

# ATHENA_DEV_AUTH_BYPASS_V1
LOCAL_DEV_HOSTS = {"127.0.0.1", "::1", "localhost"}
DEV_OPERATOR_USERNAME = "dev-local"


def _dev_bypass_allowed(request: Request) -> bool:
    if not settings.dev_auth_bypass:
        return False

    if not request.client:
        return False

    return request.client.host.strip().lower() in LOCAL_DEV_HOSTS


def _session_payload(operator) -> dict:
    return {
        "id": operator.id,
        "username": operator.username,
        "full_name": operator.full_name,
        "role": operator.role,
    }


def _get_or_create_dev_operator(db: Session):
    operator = get_operator_by_username(
        db,
        DEV_OPERATOR_USERNAME,
    )

    if operator:
        if not operator.is_active:
            return None
        return operator

    return create_operator(
        db,
        username=DEV_OPERATOR_USERNAME,
        full_name="ATHENA Desenvolvimento Local",
        password=secrets.token_urlsafe(48),
        role="admin",
    )


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    db: Session = Depends(get_db),
):
    if request.session.get("operator"):
        return RedirectResponse(url="/", status_code=302)

    if _dev_bypass_allowed(request):
        operator = _get_or_create_dev_operator(db)

        if operator is None:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": None,
                },
            )

        request.session["operator"] = _session_payload(operator)

        ip = request.client.host if request.client else None

        log_action(
            db=db,
            action="dev_auth_bypass",
            description=(
                "Sessao local de desenvolvimento iniciada "
                "por DEV_AUTH_BYPASS."
            ),
            operator_id=operator.id,
            operator_username=operator.username,
            entity_type="operator",
            entity_id=str(operator.id),
            ip_address=ip,
        )

        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
        },
    )


@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    operator = authenticate(db, username, password, ip_address=ip)
    if not operator:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario ou senha invalidos. Tente novamente."},
            status_code=401,
        )
    request.session["operator"] = {
        "id": operator.id,
        "username": operator.username,
        "full_name": operator.full_name,
        "role": operator.role,
    }
    return RedirectResponse(url="/", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request, db: Session = Depends(get_db)):
    if has_any_operator(db):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("setup.html", {"request": request, "error": None})


@router.post("/setup")
async def setup_post(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    if has_any_operator(db):
        return RedirectResponse(url="/login", status_code=302)

    if password != password_confirm:
        return templates.TemplateResponse(
            "setup.html",
            {"request": request, "error": "As senhas nao coincidem."},
            status_code=400,
        )
    if len(password) < 12:
        return templates.TemplateResponse(
            "setup.html",
            {"request": request, "error": "A senha deve ter no minimo 12 caracteres."},
            status_code=400,
        )

    create_operator(db, username=username, full_name=full_name,
                    password=password, role="admin")
    return RedirectResponse(url="/login", status_code=302)
