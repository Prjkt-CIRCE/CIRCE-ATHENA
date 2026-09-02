from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from app.database import SessionLocal
from app.services.audit_service import log_action
from app.services.workspace_product_service import (
    ProductServiceError,
    RevisionConflict,
    create_product,
    create_section,
    get_product,
    list_products,
    reorder_sections,
    serialize_product,
    set_section_blocks,
    update_section,
)


router = APIRouter(prefix="/api/workspaces/{workspace_id}/products")
PositivePathId = Annotated[int, Path(ge=1)]
PositiveId = Annotated[StrictInt, Field(ge=1)]
Revision = Annotated[StrictInt, Field(ge=1)]


class StrictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProductCreate(StrictPayload):
    title: StrictStr
    section_titles: list[StrictStr] = Field(default_factory=list, max_length=50)


class SectionCreate(StrictPayload):
    title: StrictStr
    expected_revision: Revision


class SectionUpdate(StrictPayload):
    title: StrictStr | None = None
    body: StrictStr | None = None
    expected_revision: Revision


class SectionOrderUpdate(StrictPayload):
    section_ids: list[PositiveId] = Field(max_length=50)
    expected_revision: Revision


class SectionBlocksUpdate(StrictPayload):
    block_ids: list[PositiveId] = Field(max_length=100)
    expected_revision: Revision


def _operator(request: Request) -> tuple[int | None, str]:
    operator = request.session.get("operator")
    if not isinstance(operator, dict) or not operator.get("username"):
        raise ProductServiceError("Operador autenticado inválido.")
    return operator.get("id"), str(operator["username"])


def _error_response(error: ProductServiceError) -> JSONResponse:
    payload = {"code": error.code, "error": error.message}
    if isinstance(error, RevisionConflict):
        payload["current_revision"] = error.current_revision
    return JSONResponse(payload, status_code=error.status_code)


def _audit(
    db, request: Request, *, action: str, description: str,
    operator_id: int | None, operator_username: str, entity_type: str, entity_id: int,
) -> None:
    log_action(
        db,
        action=action,
        description=description,
        operator_id=operator_id,
        operator_username=operator_username,
        entity_type=entity_type,
        entity_id=str(entity_id),
        ip_address=request.client.host if request.client else None,
        manage_transaction=False,
    )


@router.get("")
async def product_list(request: Request, workspace_id: PositivePathId):
    db = SessionLocal()
    try:
        return {"products": list_products(db, workspace_id)}
    except ProductServiceError as error:
        db.rollback()
        return _error_response(error)
    except Exception:
        db.rollback()
        return JSONResponse({"code": "internal_error", "error": "Erro interno ao consultar Produtos."}, status_code=500)
    finally:
        db.close()


@router.post("", status_code=201)
async def product_create(request: Request, workspace_id: PositivePathId, payload: ProductCreate):
    db = SessionLocal()
    try:
        operator_id, username = _operator(request)
        product = create_product(
            db, workspace_id=workspace_id, title=payload.title,
            section_titles=payload.section_titles, operator_id=operator_id, operator_username=username,
        )
        _audit(
            db, request, action="workspace_product_created",
            description=f"Produto {product.id} criado no Workspace {workspace_id}; revisão 0→1; Seções iniciais: {[item.id for item in product.sections]}.",
            operator_id=operator_id, operator_username=username,
            entity_type="workspace_product", entity_id=product.id,
        )
        db.commit()
        return serialize_product(product)
    except ProductServiceError as error:
        db.rollback()
        return _error_response(error)
    except Exception:
        db.rollback()
        return JSONResponse({"code": "internal_error", "error": "Erro interno ao criar Produto."}, status_code=500)
    finally:
        db.close()


@router.get("/{product_id}")
async def product_detail(request: Request, workspace_id: PositivePathId, product_id: PositivePathId):
    db = SessionLocal()
    try:
        return get_product(db, workspace_id, product_id)
    except ProductServiceError as error:
        db.rollback()
        return _error_response(error)
    except Exception:
        db.rollback()
        return JSONResponse({"code": "internal_error", "error": "Erro interno ao consultar Produto."}, status_code=500)
    finally:
        db.close()


@router.post("/{product_id}/sections", status_code=201)
async def section_create(request: Request, workspace_id: PositivePathId, product_id: PositivePathId, payload: SectionCreate):
    db = SessionLocal()
    try:
        operator_id, username = _operator(request)
        product = create_section(
            db, workspace_id=workspace_id, product_id=product_id, title=payload.title,
            expected_revision=payload.expected_revision, operator_id=operator_id, operator_username=username,
        )
        section_id = max(product.sections, key=lambda item: item.position).id
        _audit(
            db, request, action="product_section_created",
            description=f"Seção {section_id} criada no Produto {product_id}; revisão {payload.expected_revision}→{product.revision}.",
            operator_id=operator_id, operator_username=username,
            entity_type="product_section", entity_id=section_id,
        )
        db.commit()
        return serialize_product(product)
    except ProductServiceError as error:
        db.rollback()
        return _error_response(error)
    except Exception:
        db.rollback()
        return JSONResponse({"code": "internal_error", "error": "Erro interno ao criar Seção."}, status_code=500)
    finally:
        db.close()


@router.patch("/{product_id}/sections/{section_id}")
async def section_update(
    request: Request, workspace_id: PositivePathId, product_id: PositivePathId,
    section_id: PositivePathId, payload: SectionUpdate,
):
    changed = payload.model_fields_set - {"expected_revision"}
    if not changed or any(getattr(payload, field) is None for field in changed):
        return JSONResponse({"code": "validation_error", "error": "PATCH exige title e/ou body válidos."}, status_code=422)
    db = SessionLocal()
    try:
        operator_id, username = _operator(request)
        product = update_section(
            db, workspace_id=workspace_id, product_id=product_id, section_id=section_id,
            expected_revision=payload.expected_revision, title=payload.title, body=payload.body,
            update_title="title" in changed, update_body="body" in changed,
            operator_id=operator_id, operator_username=username,
        )
        _audit(
            db, request, action="product_section_updated",
            description=f"Seção {section_id} atualizada; campos: {sorted(changed)}; revisão {payload.expected_revision}→{product.revision}.",
            operator_id=operator_id, operator_username=username,
            entity_type="product_section", entity_id=section_id,
        )
        db.commit()
        return serialize_product(product)
    except ProductServiceError as error:
        db.rollback()
        return _error_response(error)
    except Exception:
        db.rollback()
        return JSONResponse({"code": "internal_error", "error": "Erro interno ao atualizar Seção."}, status_code=500)
    finally:
        db.close()


@router.put("/{product_id}/sections/order")
async def section_order(request: Request, workspace_id: PositivePathId, product_id: PositivePathId, payload: SectionOrderUpdate):
    db = SessionLocal()
    try:
        operator_id, username = _operator(request)
        product = reorder_sections(
            db, workspace_id=workspace_id, product_id=product_id,
            section_ids=payload.section_ids, expected_revision=payload.expected_revision,
            operator_id=operator_id, operator_username=username,
        )
        _audit(
            db, request, action="product_sections_reordered",
            description=f"Seções do Produto {product_id} reordenadas para {payload.section_ids}; revisão {payload.expected_revision}→{product.revision}.",
            operator_id=operator_id, operator_username=username,
            entity_type="workspace_product", entity_id=product_id,
        )
        db.commit()
        return serialize_product(product)
    except ProductServiceError as error:
        db.rollback()
        return _error_response(error)
    except Exception:
        db.rollback()
        return JSONResponse({"code": "internal_error", "error": "Erro interno ao reordenar Seções."}, status_code=500)
    finally:
        db.close()


@router.put("/{product_id}/sections/{section_id}/blocks")
async def section_blocks(
    request: Request, workspace_id: PositivePathId, product_id: PositivePathId,
    section_id: PositivePathId, payload: SectionBlocksUpdate,
):
    db = SessionLocal()
    try:
        operator_id, username = _operator(request)
        product = set_section_blocks(
            db, workspace_id=workspace_id, product_id=product_id, section_id=section_id,
            block_ids=payload.block_ids, expected_revision=payload.expected_revision,
            operator_id=operator_id, operator_username=username,
        )
        _audit(
            db, request, action="product_section_blocks_updated",
            description=f"Blocos da Seção {section_id} substituídos por {payload.block_ids}; revisão {payload.expected_revision}→{product.revision}.",
            operator_id=operator_id, operator_username=username,
            entity_type="product_section", entity_id=section_id,
        )
        db.commit()
        return serialize_product(product)
    except ProductServiceError as error:
        db.rollback()
        return _error_response(error)
    except Exception:
        db.rollback()
        return JSONResponse({"code": "internal_error", "error": "Erro interno ao atualizar blocos da Seção."}, status_code=500)
    finally:
        db.close()
