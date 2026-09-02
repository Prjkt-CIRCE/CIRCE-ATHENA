import os
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.database import engine, Base
from app.models.operator import Operator, AuditLog, SyncQueue, AssistantExecutionPreference
from app.models.photo import Photo
from app.models.platea import SharedCase, SharedPerson, SharedDocument, SharedLink, SharedCaseAnnotation, PlateaAccessLog
from app.models.workspace_product import WorkspaceProduct, ProductSection, ProductSectionBlock
from app.middleware.auth_guard import AuthGuard
from app.routes.auth import router as auth_router
from app.routes.web import router as web_router
from app.routes.photos import router as photos_router
from app.routes.sync import router as sync_router
from app.routes.platea import router as platea_router
from app.routes.workspace import router as workspace_router
from app.routes.documents import router as documents_router
from app.routes.workspace_products import router as workspace_products_router

# Evolução de schema é responsabilidade do Alembic.
# Antes de iniciar uma versão nova da aplicação, execute: alembic upgrade head

app = FastAPI(title="CIRCE Athena", docs_url=None, redoc_url=None)
app.add_middleware(AuthGuard)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, max_age=settings.session_hours * 3600)
app.include_router(auth_router)
app.include_router(web_router)
app.include_router(photos_router)
app.include_router(sync_router)
app.include_router(platea_router)
app.include_router(workspace_router)
app.include_router(documents_router)
app.include_router(workspace_products_router)

if __name__ == "__main__":
    print("=" * 52)
    print("  CIRCE // ATHENA")
    print("  Servidor de Inteligencia Compartilhada")
    print("=" * 52)
    print(f"  Endereco : http://{settings.host}:{settings.port}")
    print(f"  Dados    : {os.path.abspath(settings.data_dir)}")
    print(f"  LLM      : {settings.llm_base_url}")
    print(f"  Modelo   : {settings.llm_model}")
    print("=" * 52)
    print("  Ctrl+C para encerrar")
    print()
    uvicorn.run(
        "run:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
