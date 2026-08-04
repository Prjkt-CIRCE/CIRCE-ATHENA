from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import authenticate, has_any_operator, create_operator

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("operator"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


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
