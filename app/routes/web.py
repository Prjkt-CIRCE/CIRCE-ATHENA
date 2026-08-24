from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timezone
import httpx

from app.config import settings
from app.database import SessionLocal
from app.models.operator import AuditLog, SyncQueue, AssistantExecutionPreference
from app.models.platea import SharedCase
from app.services.assistant_context_service import build_investigative_context
from app.services.workspace_service import build_block_context
from app.services.audit_service import log_action
from app.services.assistant_action_service import (
    parse_annotation_command,
    build_pending_annotation,
    create_case_annotation,
)
from app.services.assistant_action_planner import (
    may_contain_write_intent,
    plan_user_action,
)
from app.services.assistant_execution_policy import (
    normalize_execution_mode,
    decide_execution,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def _assistant_execution_mode(db, operator_id):
    if not operator_id:
        return "safe"
    pref = (
        db.query(AssistantExecutionPreference)
        .filter(AssistantExecutionPreference.operator_id == operator_id)
        .first()
    )
    return normalize_execution_mode(pref.mode if pref else None)


def _set_assistant_execution_mode(db, operator_id, mode):
    normalized = normalize_execution_mode(mode)
    pref = (
        db.query(AssistantExecutionPreference)
        .filter(AssistantExecutionPreference.operator_id == operator_id)
        .first()
    )
    if pref:
        pref.mode = normalized
        pref.updated_at = datetime.now(timezone.utc)
    else:
        pref = AssistantExecutionPreference(
            operator_id=operator_id,
            mode=normalized,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(pref)
    db.flush()
    return normalized


@router.get("/health")
async def health():
    return {"status": "ok", "system": "CIRCE Athena"}


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    operator = request.session.get("operator", {})
    db = SessionLocal()
    try:
        active_cases = (
            db.query(SharedCase)
            .filter(SharedCase.status == "aberto")
            .order_by(SharedCase.last_updated_at.desc(), SharedCase.published_at.desc())
            .limit(6)
            .all()
        )
        recent_logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.desc())
            .limit(8)
            .all()
        )
        sync_pending = (
            db.query(SyncQueue)
            .filter(SyncQueue.status == "pending")
            .count()
        )

        sync_errors = (
            db.query(SyncQueue)
            .filter(SyncQueue.status.in_(["error", "failed"]))
            .count()
        )

        operational_pending = {
            "sync_pending": sync_pending,
            "sync_errors": sync_errors,
            "total": sync_pending + sync_errors,
        }
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "operator": operator,
            "active_cases": active_cases,
            "recent_logs": recent_logs,
            "operational_pending": operational_pending,
        })
    finally:
        db.close()


@router.get("/assistant", response_class=HTMLResponse)
async def assistant_page(request: Request):
    operator = request.session.get("operator", {})
    return templates.TemplateResponse("assistant.html", {
        "request": request,
        "operator": operator,
    })


@router.post("/api/assistant/query")
async def assistant_query(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    recent_history = body.get("history") or []
    if not isinstance(recent_history, list):
        recent_history = []

    active_case_ref = body.get("active_case_ref")
    if isinstance(active_case_ref, str):
        active_case_ref = active_case_ref.strip() or None
    else:
        active_case_ref = None

    active_block_id = body.get("active_block_id")
    try:
        active_block_id = int(active_block_id) if active_block_id is not None else None
    except (TypeError, ValueError):
        active_block_id = None

    recent_action = body.get("recent_action")
    if not isinstance(recent_action, dict):
        recent_action = None
    if not question:
        return JSONResponse({"answer": "Pergunta vazia."}, status_code=400)

    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None
    planned_authorship_mode = "literal"
    write_command = parse_annotation_command(question)

    # A interface é conversacional. O parser rígido fica só como fallback técnico.
    if write_command is None and may_contain_write_intent(question):
        planned = await plan_user_action(
            message=question,
            active_case_ref=active_case_ref,
            recent_history=recent_history,
            recent_action=recent_action,
        )

        if planned.action_type == "add_case_annotation":
            from app.services.assistant_action_service import AnnotationCommand
            planned_authorship_mode = planned.authorship_mode or "literal"
            write_command = AnnotationCommand(
                case_ref=planned.case_ref,
                content=planned.content,
            )

        elif planned.action_type == "unsupported_write":
            return JSONResponse({
                "answer": (
                    planned.explanation
                    or "Entendi o pedido de alteração, mas essa ação ainda não está habilitada com segurança."
                ),
                "context_mode": "unsupported_write",
            })

    if write_command:
        db = SessionLocal()
        try:
            pending_action, action_error = build_pending_annotation(
                db,
                write_command,
                authorship_mode=planned_authorship_mode,
            )
            if action_error:
                return JSONResponse({
                    "answer": action_error,
                    "context_mode": "action_not_prepared",
                }, status_code=404)

            execution_mode = _assistant_execution_mode(
                db,
                operator.get("id"),
            )
            decision = decide_execution(
                action_type=pending_action["type"],
                mode=execution_mode,
            )

            # LOW/MEDIUM no SAFE e ações no AGENT executam sem confirmação.
            if not decision.requires_confirmation:
                annotation = create_case_annotation(
                    db,
                    case_ref=pending_action["case_ref"],
                    content=pending_action["content"],
                    operator_id=operator.get("id"),
                    operator_username=operator.get("username"),
                    authorship_mode=pending_action.get("authorship_mode", "literal"),
                )
                if not annotation:
                    db.rollback()
                    return JSONResponse({
                        "answer": f"O caso {pending_action['case_ref']} não foi encontrado.",
                        "context_mode": "action_not_completed",
                    }, status_code=404)

                log_action(
                    db,
                    action="assistant_case_annotation_created",
                    description=(
                        "Anotação criada por solicitação explícita do usuário. "
                        f"Modo: {execution_mode}; risco: {decision.risk}; "
                        f"caso: {pending_action['case_ref']}; anotação: {annotation.id}."
                    ),
                    operator_id=operator.get("id"),
                    operator_username=operator.get("username"),
                    entity_type="case_annotation",
                    entity_id=str(annotation.id),
                    ip_address=ip,
                    manage_transaction=False,
                )
                db.commit()

                return JSONResponse({
                    "answer": (
                        f"Feito. Registrei a anotação no caso {pending_action['case_ref']}. "
                        f"[CASE:{pending_action['case_ref']}] [ANOTACAO:{annotation.id}]"
                    ),
                    "context_mode": "authorized_write_completed",
                    "execution_mode": execution_mode,
                    "risk": decision.risk,
                    "source": f"CASE:{pending_action['case_ref']}",
                    "annotation_id": annotation.id,
                    "written_content": pending_action["content"],
                    "authorship_mode": pending_action.get("authorship_mode", "literal"),
                    "case_ref": pending_action["case_ref"],
                })

            # SAFE para ação high/critical: preserva confirmação contextual.
            request.session["assistant_pending_action"] = pending_action
            log_action(
                db,
                action="assistant_action_proposed",
                description=(
                    "Assistente preparou ação para confirmação humana. "
                    f"Modo: {execution_mode}; risco: {decision.risk}; "
                    f"caso: {pending_action['case_ref']}."
                ),
                operator_id=operator.get("id"),
                operator_username=operator.get("username"),
                entity_type="shared_case",
                entity_id=pending_action["case_ref"],
                ip_address=ip,
            )

            return JSONResponse({
                "answer": (
                    f"A ação foi classificada como {decision.risk} no Safe Mode. "
                    "Revise antes de confirmar."
                ),
                "pending_action": pending_action,
                "context_mode": "action_confirmation",
                "execution_mode": execution_mode,
                "risk": decision.risk,
            })
        finally:
            db.close()

    db = SessionLocal()
    try:
        context = build_investigative_context(
            db,
            question,
            active_case_ref=active_case_ref,
            operator_username=operator.get("username"),
        )
        block_context = build_block_context(
            db,
            case_ref=active_case_ref,
            block_id=active_block_id,
        )
        context_text = context.text
        context_sources = list(context.sources)
        if block_context:
            context_text += "\n\n" + block_context.text
            context_sources.extend(
                source for source in block_context.sources if source not in context_sources
            )
        context_mode = (
            "workspace_block"
            if block_context
            else ("workspace_case" if active_case_ref else "local_read_only")
        )
        source_summary = ", ".join(context_sources) if context_sources else "nenhuma"
        log_action(
            db,
            action="assistant_context_query",
            description=(
                "Assistente consultou contexto investigativo local em modo somente leitura. "
                f"Fontes: {source_summary}"
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="assistant_context",
            entity_id=context.case_refs[0] if len(context.case_refs) == 1 else None,
            ip_address=ip,
        )
    except Exception as e:
        return JSONResponse(
            {"answer": f"Erro ao consultar contexto investigativo local: {str(e)}"},
            status_code=500,
        )
    finally:
        db.close()

    system_prompt = (
        "Voce e Athena, a implementacao atual do Assistente de Inteligencia do CIRCE Athena. "
        "Responda de forma tecnica, objetiva e em portugues brasileiro. "
        "Voce recebeu abaixo um CONTEXTO INVESTIGATIVO LOCAL, obtido da base investigativa local em modo somente leitura. "
        "Para qualquer afirmacao especifica sobre casos, pessoas, documentos ou vinculos locais, "
        "use exclusivamente esse contexto. Nunca complete lacunas por suposicao. "
        "Quando a informacao pedida nao estiver presente, diga claramente que ela nao consta "
        "no contexto local disponibilizado. "
        "Ao usar dados de um caso, indique a fonte no formato [CASE:REFERENCIA]. "
        "Diferencie fatos registrados de inferencias ou hipoteses analiticas. "
        "Ações de escrita suportadas são executadas por uma camada governada antes desta resposta. "
        "Nunca afirme que uma alteração ocorreu sem confirmação retornada pelo backend. "
        "Quando houver BLOCO INVESTIGATIVO ativo, trate-o como organização de fontes e raciocínio, "
        "sem elevar inferências, hipóteses ou texto assistido ao status de fato. "
        "Quando houver ACHADOS INVESTIGATIVOS VALIDADOS, respeite rigorosamente seu tipo epistemológico: "
        "fato, declaração, anotação, inferência, hipótese ou pendência. Validação humana não transforma "
        "inferência ou hipótese em fato. "
        "Para perguntas gerais que nao dependam de dados de casos, responda normalmente. "
        "Nunca invente dados de casos, pessoas ou investigacoes reais.\n\n"
        + context_text
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                json={
                    "model": settings.llm_model,
                    "messages": (
                        [{"role": "system", "content": system_prompt}]
                        + [
                            {
                                "role": item.get("role"),
                                "content": str(item.get("content") or "")[:1500],
                            }
                            for item in recent_history[-8:]
                            if item.get("role") in {"user", "assistant"}
                            and item.get("content")
                        ]
                        + [{"role": "user", "content": question}]
                    ),
                    "temperature": 0.2,
                    "max_tokens": 1200,
                },
                headers={"Authorization": "Bearer lm-studio"},
            )
            resp.raise_for_status()

        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        return JSONResponse({
            "answer": answer,
            "sources": context_sources,
            "context_mode": context_mode,
            "active_block_id": block_context.block_id if block_context else None,
        })
    except Exception as e:
        return JSONResponse(
            {
                "answer": f"Erro ao contactar modelo local: {str(e)}",
                "sources": context_sources,
                "context_mode": context_mode,
            },
            status_code=503,
        )


@router.post("/api/assistant/action/confirm")
async def assistant_action_confirm(request: Request):
    body = await request.json()
    action_id = body.get("action_id", "")
    pending = request.session.get("assistant_pending_action")
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None

    if not pending or pending.get("action_id") != action_id:
        return JSONResponse(
            {"answer": "Não há uma ação pendente válida para confirmar."},
            status_code=400,
        )

    try:
        created_at = datetime.fromisoformat(pending["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created_at).total_seconds()
        if age > 600:
            request.session.pop("assistant_pending_action", None)
            return JSONResponse(
                {"answer": "A confirmação expirou. Solicite a anotação novamente."},
                status_code=400,
            )
    except Exception:
        request.session.pop("assistant_pending_action", None)
        return JSONResponse(
            {"answer": "A ação pendente está inválida. Solicite novamente."},
            status_code=400,
        )

    if pending.get("type") != "add_case_annotation":
        return JSONResponse(
            {"answer": "Tipo de ação não suportado nesta etapa."},
            status_code=400,
        )

    db = SessionLocal()
    try:
        annotation = create_case_annotation(
            db,
            case_ref=pending["case_ref"],
            content=pending["content"],
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            authorship_mode=pending.get("authorship_mode", "literal"),
        )
        if not annotation:
            db.rollback()
            request.session.pop("assistant_pending_action", None)
            return JSONResponse(
                {"answer": f"O caso {pending['case_ref']} não foi encontrado."},
                status_code=404,
            )

        log_action(
            db,
            action="assistant_case_annotation_created",
            description=(
                "Anotação criada por solicitação e confirmação explícita do usuário. "
                f"Caso: {pending['case_ref']}; anotação: {annotation.id}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="case_annotation",
            entity_id=str(annotation.id),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()

        request.session.pop("assistant_pending_action", None)

        return JSONResponse({
            "answer": (
                f"Anotação registrada no caso {pending['case_ref']} "
                f"com confirmação do usuário. "
                f"Fonte local: [CASE:{pending['case_ref']}] "
                f"[ANOTACAO:{annotation.id}]"
            ),
            "context_mode": "authorized_write_completed",
            "source": f"CASE:{pending['case_ref']}",
            "annotation_id": annotation.id,
            "written_content": pending["content"],
            "authorship_mode": pending.get("authorship_mode", "literal"),
            "case_ref": pending["case_ref"],
        })
    except Exception as exc:
        db.rollback()
        return JSONResponse(
            {"answer": f"Não foi possível registrar a anotação: {str(exc)}"},
            status_code=500,
        )
    finally:
        db.close()


@router.post("/api/assistant/action/cancel")
async def assistant_action_cancel(request: Request):
    body = await request.json()
    action_id = body.get("action_id", "")
    pending = request.session.get("assistant_pending_action")
    operator = request.session.get("operator", {})
    ip = request.client.host if request.client else None

    if not pending or pending.get("action_id") != action_id:
        return JSONResponse(
            {"answer": "Não há uma ação pendente válida para cancelar."},
            status_code=400,
        )

    request.session.pop("assistant_pending_action", None)

    db = SessionLocal()
    try:
        log_action(
            db,
            action="assistant_action_cancelled",
            description=(
                "Usuário cancelou ação proposta pelo Assistente. "
                f"Caso: {pending.get('case_ref')}."
            ),
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="shared_case",
            entity_id=pending.get("case_ref"),
            ip_address=ip,
        )
    finally:
        db.close()

    return JSONResponse({
        "answer": "Ação cancelada. Nenhuma alteração foi realizada.",
        "context_mode": "authorized_write_cancelled",
    })

@router.get("/api/assistant/execution-mode")
async def assistant_execution_mode_get(request: Request):
    operator = request.session.get("operator", {})
    db = SessionLocal()
    try:
        mode = _assistant_execution_mode(db, operator.get("id"))
        return JSONResponse({"mode": mode})
    finally:
        db.close()


@router.post("/api/assistant/execution-mode")
async def assistant_execution_mode_set(request: Request):
    operator = request.session.get("operator", {})
    if not operator.get("id"):
        return JSONResponse({"error": "Operador não autenticado."}, status_code=401)

    body = await request.json()
    requested = str(body.get("mode") or "").lower()
    if requested not in {"safe", "agent"}:
        return JSONResponse({"error": "Modo inválido."}, status_code=400)

    ip = request.client.host if request.client else None
    db = SessionLocal()
    try:
        previous = _assistant_execution_mode(db, operator.get("id"))
        mode = _set_assistant_execution_mode(db, operator.get("id"), requested)

        log_action(
            db,
            action="assistant_execution_mode_changed",
            description=f"Modo de execução do Assistente alterado de {previous} para {mode}.",
            operator_id=operator.get("id"),
            operator_username=operator.get("username"),
            entity_type="assistant_execution_mode",
            entity_id=str(operator.get("id")),
            ip_address=ip,
            manage_transaction=False,
        )
        db.commit()
        return JSONResponse({"mode": mode})
    except Exception as exc:
        db.rollback()
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        db.close()

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
