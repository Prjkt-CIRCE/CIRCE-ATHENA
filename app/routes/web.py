from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timezone
import httpx
from app.config import settings
from app.database import SessionLocal
from app.models.operator import AuditLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/health")
async def health():
    return {"status": "ok", "system": "CIRCE Athena"}


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    operator = request.session.get("operator", {})
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "operator": operator,
    })


@router.post("/api/assistant/query")
async def assistant_query(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        return JSONResponse({"answer": "Pergunta vazia."}, status_code=400)

    system_prompt = (
        "Voce e Athena, assistente de inteligencia policial do CIRCE Athena. "
        "Responda de forma tecnica, objetiva e em portugues brasileiro. "
        "Nesta fase do sistema voce nao tem acesso a base de dados local de investigacoes — "
        "informe isso quando a pergunta exigir dados especificos de casos. "
        "Para perguntas gerais de inteligencia, analise criminal, tecnicas investigativas "
        "e elaboracao de textos tecnicos, responda normalmente. "
        "Nunca invente dados de casos, pessoas ou investigacoes reais."
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024,
                },
                headers={"Authorization": "Bearer lm-studio"},
            )
        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        return JSONResponse({"answer": answer})
    except Exception as e:
        return JSONResponse(
            {"answer": f"Erro ao contactar modelo local: {str(e)}"},
            status_code=503,
        )


@router.get("/api/system/llm-status")
async def llm_status():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.llm_base_url}/models",
                headers={"Authorization": "Bearer lm-studio"},
            )
        return JSONResponse({"ok": resp.status_code == 200})
    except Exception:
        return JSONResponse({"ok": False})


@router.get("/api/system/recent-activity")
async def recent_activity():
    db = SessionLocal()
    try:
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .limit(8)
            .all()
        )
        items = []
        now = datetime.now(timezone.utc)
        for log in logs:
            ts = log.timestamp
            # Normaliza para aware se vier naive do SQLite
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            diff = (now - ts).total_seconds()
            if diff < 60:
                time_str = "agora"
            elif diff < 3600:
                time_str = f"{int(diff//60)}min atras"
            elif diff < 86400:
                time_str = f"{int(diff//3600)}h atras"
            else:
                time_str = ts.strftime("%d/%m %H:%M")
            items.append({
                "action": log.action,
                "description": log.description[:80],
                "operator": log.operator_username or "sistema",
                "time": time_str,
            })
        return JSONResponse({"items": items})
    except Exception as e:
        return JSONResponse({"items": [], "error": str(e)})
    finally:
        db.close()
