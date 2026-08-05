"""
sync.py — AT-03.4
Endpoints de sincronizacao Intel Desk -> Athena.

POST /api/sync/case   — recebe payload completo de caso, persiste na Platea
GET  /api/sync/status/{case_ref} — consulta se caso ja existe e qual versao
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.database import SessionLocal
from app.schemas.platea import SyncCasePayload, SyncResponse
from app.services.platea_service import receive_case_sync, get_case_by_ref

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/case", response_model=SyncResponse)
async def sync_case(request: Request, payload: SyncCasePayload):
    """
    Recebe caso publicado pelo Intel Desk e persiste na Platea.
    Autenticado via sessao (AuthGuard cobre todas as rotas nao-publicas).
    O operador logado no Athena e registrado como receptor no audit log.
    """
    operator = request.session.get("operator", {})
    operator_id       = operator.get("id", 0)
    operator_username = operator.get("username", "intel_desk")
    ip_address        = request.client.host if request.client else None

    db = SessionLocal()
    try:
        result = receive_case_sync(
            db=db,
            payload=payload,
            operator_id=operator_id,
            operator_username=operator_username,
            ip_address=ip_address,
        )
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar caso: {str(e)}")
    finally:
        db.close()


@router.get("/status/{case_ref}")
async def sync_status(case_ref: str):
    """
    Consulta se um caso ja existe na Platea e retorna versao atual.
    Usado pelo Intel Desk para verificar status antes de reenviar.
    """
    db = SessionLocal()
    try:
        case = get_case_by_ref(db, case_ref)
        if not case:
            return JSONResponse({
                "case_ref": case_ref,
                "exists": False,
                "published_version": None,
                "published_at": None,
            })
        return JSONResponse({
            "case_ref": case_ref,
            "exists": True,
            "published_version": case.published_version,
            "published_at": case.published_at.isoformat(),
        })
    finally:
        db.close()