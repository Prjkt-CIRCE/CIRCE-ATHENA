import os
import shutil
import tempfile
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.database import SessionLocal
from app.models.operator import Operator
from app.models.photo import Photo
from app.services.photo_service import cadastrar_foto, buscar_fotos, comparar_foto
from app.services.audit_service import log_action

router = APIRouter(prefix="/photos")
templates = Jinja2Templates(directory="app/templates")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _get_operator_obj(request: Request) -> Operator | None:
    op = request.session.get("operator")
    if not op:
        return None
    db = SessionLocal()
    try:
        return db.query(Operator).filter(Operator.id == op["id"]).first()
    finally:
        db.close()


# ── LISTAGEM ────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def photos_list(
    request: Request,
    nome: str = "",
    sexo: str = "",
    etnia_cor: str = "",
    grau_confiabilidade: str = "",
    sinais_particulares: str = "",
    page: int = 1,
):
    operator = request.session.get("operator", {})
    db = SessionLocal()
    try:
        limit = 20
        offset = (page - 1) * limit
        fotos, total = buscar_fotos(
            db=db,
            nome=nome or None,
            sexo=sexo or None,
            etnia_cor=etnia_cor or None,
            grau_confiabilidade=grau_confiabilidade or None,
            sinais_particulares=sinais_particulares or None,
            limit=limit,
            offset=offset,
        )
        total_pages = max(1, (total + limit - 1) // limit)
        return templates.TemplateResponse("photos_list.html", {
            "request": request,
            "operator": operator,
            "fotos": fotos,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "filtros": {
                "nome": nome,
                "sexo": sexo,
                "etnia_cor": etnia_cor,
                "grau_confiabilidade": grau_confiabilidade,
                "sinais_particulares": sinais_particulares,
            },
        })
    finally:
        db.close()


# ── CADASTRO ─────────────────────────────────────────────────────────────────

@router.get("/new", response_class=HTMLResponse)
async def photos_new_form(request: Request):
    operator = request.session.get("operator", {})
    return templates.TemplateResponse("photos_new.html", {
        "request": request,
        "operator": operator,
        "error": None,
        "success": None,
    })


@router.post("/new", response_class=HTMLResponse)
async def photos_new_submit(
    request: Request,
    foto: UploadFile = File(...),
    nome_completo: str = Form(...),
    sexo: str = Form(...),
    etnia_cor: str = Form(...),
    contexto_foto: str = Form(...),
    fonte: str = Form(...),
    grau_confiabilidade: str = Form(...),
    alcunhas: str = Form(""),
    cpf: str = Form(""),
    data_nascimento: str = Form(""),
    estatura: str = Form(""),
    compleicao: str = Form(""),
    sinais_particulares: str = Form(""),
    caso_vinculado: str = Form(""),
    observacoes: str = Form(""),
):
    operator_session = request.session.get("operator", {})

    def render_error(msg: str):
        return templates.TemplateResponse("photos_new.html", {
            "request": request,
            "operator": operator_session,
            "error": msg,
            "success": None,
        })

    ext = os.path.splitext(foto.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return render_error(f"Formato nao suportado: {ext}. Use JPG, PNG, BMP ou WEBP.")

    content = await foto.read()
    if len(content) > MAX_FILE_SIZE:
        return render_error("Arquivo muito grande. Limite: 20 MB.")
    if len(content) == 0:
        return render_error("Arquivo vazio.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(content)
    tmp.close()

    db = SessionLocal()
    try:
        operador = db.query(Operator).filter(
            Operator.id == operator_session.get("id")
        ).first()
        if not operador:
            return render_error("Sessao invalida. Faca login novamente.")

        photo = cadastrar_foto(
            db=db,
            temp_path=tmp.name,
            original_filename=foto.filename or f"foto{ext}",
            nome_completo=nome_completo.strip(),
            sexo=sexo,
            etnia_cor=etnia_cor,
            contexto_foto=contexto_foto,
            fonte=fonte.strip(),
            grau_confiabilidade=grau_confiabilidade,
            operador=operador,
            alcunhas=alcunhas.strip() or None,
            cpf=cpf.strip() or None,
            data_nascimento=data_nascimento or None,
            estatura=estatura or None,
            compleicao=compleicao or None,
            sinais_particulares=sinais_particulares.strip() or None,
            caso_vinculado=caso_vinculado.strip() or None,
            observacoes=observacoes.strip() or None,
        )
        embedding_msg = (
            "Embedding facial extraido."
            if photo.embedding_path
            else "Nenhuma face detectada — embedding nao gerado. Registro salvo."
        )
        return templates.TemplateResponse("photos_new.html", {
            "request": request,
            "operator": operator_session,
            "error": None,
            "success": f"Foto cadastrada com ID #{photo.id}. {embedding_msg}",
        })
    except Exception as e:
        return render_error(f"Erro ao cadastrar foto: {str(e)}")
    finally:
        db.close()
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


# ── MIDIA (serve arquivos de imagem do banco) ────────────────────────────────

@router.get("/media/{photo_id}")
async def photo_media(photo_id: int, request: Request):
    """Serve o arquivo de imagem de uma foto cadastrada."""
    db = SessionLocal()
    try:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo or not os.path.isfile(photo.caminho_foto):
            from fastapi.responses import Response
            return Response(status_code=404)
        ext = os.path.splitext(photo.caminho_foto)[1].lower()
        media_types = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".bmp": "image/bmp", ".webp": "image/webp",
        }
        return FileResponse(
            photo.caminho_foto,
            media_type=media_types.get(ext, "image/jpeg"),
        )
    finally:
        db.close()


# ── COMPARACAO ───────────────────────────────────────────────────────────────

@router.get("/compare", response_class=HTMLResponse)
async def photos_compare_form(request: Request):
    operator = request.session.get("operator", {})
    return templates.TemplateResponse("photos_compare.html", {
        "request": request,
        "operator": operator,
        "candidatos": None,
        "aviso": None,
        "error": None,
        "query_hash": None,
    })


@router.post("/compare", response_class=HTMLResponse)
async def photos_compare_submit(
    request: Request,
    foto_consulta: UploadFile = File(...),
):
    operator_session = request.session.get("operator", {})

    def render_error(msg: str):
        return templates.TemplateResponse("photos_compare.html", {
            "request": request,
            "operator": operator_session,
            "candidatos": None,
            "aviso": None,
            "error": msg,
            "query_hash": None,
        })

    ext = os.path.splitext(foto_consulta.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return render_error(f"Formato nao suportado: {ext}.")

    content = await foto_consulta.read()
    if len(content) > MAX_FILE_SIZE:
        return render_error("Arquivo muito grande. Limite: 20 MB.")
    if len(content) == 0:
        return render_error("Arquivo vazio.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(content)
    tmp.close()

    db = SessionLocal()
    try:
        operador = db.query(Operator).filter(
            Operator.id == operator_session.get("id")
        ).first()
        if not operador:
            return render_error("Sessao invalida.")

        candidatos, aviso = comparar_foto(
            db=db,
            temp_path=tmp.name,
            operador=operador,
            top_k=5,
            threshold=0.4,
        )

        import hashlib
        query_hash = hashlib.sha256(content).hexdigest()[:16]

        return templates.TemplateResponse("photos_compare.html", {
            "request": request,
            "operator": operator_session,
            "candidatos": candidatos,
            "aviso": aviso,
            "error": None,
            "query_hash": query_hash,
            "query_filename": foto_consulta.filename,
        })
    except Exception as e:
        return render_error(f"Erro ao processar comparacao: {str(e)}")
    finally:
        db.close()
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


# ── VALIDACAO DE CANDIDATO ───────────────────────────────────────────────────

@router.post("/compare/validate")
async def photos_compare_validate(request: Request):
    """
    Registra decisao de validacao/rejeicao de candidato no audit log.
    Body JSON: {photo_id, decisao, query_hash, score}
    decisao: "confirmado" | "rejeitado"
    """
    operator_session = request.session.get("operator", {})
    body = await request.json()

    photo_id = body.get("photo_id")
    decisao = body.get("decisao")
    query_hash = body.get("query_hash", "N/A")
    score = body.get("score", 0)

    if decisao not in ("confirmado", "rejeitado"):
        return JSONResponse({"ok": False, "error": "Decisao invalida."}, status_code=400)

    db = SessionLocal()
    try:
        operador = db.query(Operator).filter(
            Operator.id == operator_session.get("id")
        ).first()
        if not operador:
            return JSONResponse({"ok": False, "error": "Sessao invalida."}, status_code=401)

        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        nome_candidato = photo.nome_completo if photo else f"ID #{photo_id}"

        log_action(
            db=db,
            operator_id=operador.id,
            operator_username=operador.username,
            action="photo_validacao",
            entity_type="photo",
            entity_id=str(photo_id),
            description=(
                f"Validacao facial: {decisao.upper()} | "
                f"Candidato: {nome_candidato} (ID #{photo_id}) | "
                f"Score: {score:.3f} | "
                f"SHA256_query={query_hash}..."
            ),
            manage_transaction=True,
        )
        return JSONResponse({"ok": True, "decisao": decisao})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    finally:
        db.close()