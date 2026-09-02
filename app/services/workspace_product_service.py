from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session, selectinload

from app.models.workspace import InvestigativeBlock, InvestigativeWorkspace
from app.models.workspace_product import ProductSection, ProductSectionBlock, WorkspaceProduct


MAX_TITLE_LENGTH = 256
MAX_SECTION_BODY_LENGTH = 50_000
MAX_SECTIONS_PER_PRODUCT = 50
MAX_BLOCKS_PER_SECTION = 100


class ProductServiceError(Exception):
    status_code = 422
    code = "validation_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ProductNotFound(ProductServiceError):
    status_code = 404
    code = "not_found"


class RevisionConflict(ProductServiceError):
    status_code = 409
    code = "revision_conflict"

    def __init__(self, current_revision: int):
        super().__init__("A revisão informada está desatualizada.")
        self.current_revision = current_revision


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clean_title(value: str) -> str:
    title = value.strip()
    if not title:
        raise ProductServiceError("O título é obrigatório.")
    if len(title) > MAX_TITLE_LENGTH:
        raise ProductServiceError(f"O título deve ter no máximo {MAX_TITLE_LENGTH} caracteres.")
    return title


def _validate_body(value: str) -> str:
    if len(value) > MAX_SECTION_BODY_LENGTH:
        raise ProductServiceError(
            f"O corpo da Seção deve ter no máximo {MAX_SECTION_BODY_LENGTH} caracteres."
        )
    return value


def _load_product(db: Session, workspace_id: int, product_id: int) -> WorkspaceProduct:
    product = (
        db.query(WorkspaceProduct)
        .options(
            selectinload(WorkspaceProduct.sections)
            .selectinload(ProductSection.block_links)
            .selectinload(ProductSectionBlock.block)
        )
        .filter(
            WorkspaceProduct.id == product_id,
            WorkspaceProduct.workspace_id == workspace_id,
        )
        .execution_options(populate_existing=True)
        .first()
    )
    if not product:
        raise ProductNotFound("Produto não encontrado.")
    return product


def _get_section(product: WorkspaceProduct, section_id: int) -> ProductSection:
    section = next((item for item in product.sections if item.id == section_id), None)
    if not section:
        raise ProductNotFound("Seção não encontrada.")
    return section


def _reserve_revision(
    db: Session,
    product: WorkspaceProduct,
    expected_revision: int,
    *,
    operator_id: int | None,
    operator_username: str,
) -> int:
    now = _utcnow()
    result = db.execute(
        update(WorkspaceProduct)
        .where(
            WorkspaceProduct.id == product.id,
            WorkspaceProduct.revision == expected_revision,
        )
        .values(
            revision=WorkspaceProduct.revision + 1,
            updated_by_operator_id=operator_id,
            updated_by_username=operator_username,
            updated_at=now,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.expire_all()
        current = db.query(WorkspaceProduct.revision).filter_by(id=product.id).scalar()
        if current is None:
            raise ProductNotFound("Produto não encontrado.")
        raise RevisionConflict(int(current))
    product.revision = expected_revision + 1
    product.updated_by_operator_id = operator_id
    product.updated_by_username = operator_username
    product.updated_at = now
    return product.revision


def _ensure_expected_revision(product: WorkspaceProduct, expected_revision: int) -> None:
    if product.revision != expected_revision:
        raise RevisionConflict(product.revision)


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_product(product: WorkspaceProduct) -> dict[str, Any]:
    sections = []
    for section in sorted(product.sections, key=lambda item: (item.position, item.id)):
        blocks = []
        for link in sorted(section.block_links, key=lambda item: (item.position, item.id)):
            blocks.append({
                "block_id": link.block_id,
                "position": link.position,
                "title": link.block.title,
                "availability": "discarded" if link.block.status == "discarded" else "available",
            })
        sections.append({
            "id": section.id,
            "title": section.title,
            "body": section.body,
            "position": section.position,
            "created_by_operator_id": section.created_by_operator_id,
            "created_by_username": section.created_by_username,
            "updated_by_operator_id": section.updated_by_operator_id,
            "updated_by_username": section.updated_by_username,
            "created_at": _timestamp(section.created_at),
            "updated_at": _timestamp(section.updated_at),
            "blocks": blocks,
        })
    return {
        "id": product.id,
        "workspace_id": product.workspace_id,
        "title": product.title,
        "revision": product.revision,
        "created_by_operator_id": product.created_by_operator_id,
        "created_by_username": product.created_by_username,
        "updated_by_operator_id": product.updated_by_operator_id,
        "updated_by_username": product.updated_by_username,
        "created_at": _timestamp(product.created_at),
        "updated_at": _timestamp(product.updated_at),
        "sections": sections,
    }


def list_products(db: Session, workspace_id: int) -> list[dict[str, Any]]:
    if not db.query(InvestigativeWorkspace.id).filter_by(id=workspace_id).first():
        raise ProductNotFound("Workspace não encontrado.")
    products = (
        db.query(WorkspaceProduct)
        .options(selectinload(WorkspaceProduct.sections))
        .filter_by(workspace_id=workspace_id)
        .order_by(WorkspaceProduct.created_at, WorkspaceProduct.id)
        .all()
    )
    return [{
        "id": item.id,
        "workspace_id": item.workspace_id,
        "title": item.title,
        "revision": item.revision,
        "section_count": len(item.sections),
        "created_at": _timestamp(item.created_at),
        "updated_at": _timestamp(item.updated_at),
    } for item in products]


def get_product(db: Session, workspace_id: int, product_id: int) -> dict[str, Any]:
    return serialize_product(_load_product(db, workspace_id, product_id))


def create_product(
    db: Session,
    *,
    workspace_id: int,
    title: str,
    section_titles: list[str],
    operator_id: int | None,
    operator_username: str,
) -> WorkspaceProduct:
    if not db.query(InvestigativeWorkspace.id).filter_by(id=workspace_id).first():
        raise ProductNotFound("Workspace não encontrado.")
    if len(section_titles) > MAX_SECTIONS_PER_PRODUCT:
        raise ProductServiceError(f"Um Produto aceita no máximo {MAX_SECTIONS_PER_PRODUCT} Seções.")
    clean_title = _clean_title(title)
    clean_sections = [_clean_title(item) for item in section_titles]
    now = _utcnow()
    product = WorkspaceProduct(
        workspace_id=workspace_id,
        title=clean_title,
        revision=1,
        created_by_operator_id=operator_id,
        created_by_username=operator_username,
        updated_by_operator_id=operator_id,
        updated_by_username=operator_username,
        created_at=now,
        updated_at=now,
    )
    db.add(product)
    db.flush()
    for position, section_title in enumerate(clean_sections):
        db.add(ProductSection(
            product_id=product.id,
            title=section_title,
            body="",
            position=position,
            created_by_operator_id=operator_id,
            created_by_username=operator_username,
            updated_by_operator_id=operator_id,
            updated_by_username=operator_username,
            created_at=now,
            updated_at=now,
        ))
    db.flush()
    return _load_product(db, workspace_id, product.id)


def create_section(
    db: Session,
    *, workspace_id: int, product_id: int, title: str, expected_revision: int,
    operator_id: int | None, operator_username: str,
) -> WorkspaceProduct:
    product = _load_product(db, workspace_id, product_id)
    if len(product.sections) >= MAX_SECTIONS_PER_PRODUCT:
        raise ProductServiceError(f"Um Produto aceita no máximo {MAX_SECTIONS_PER_PRODUCT} Seções.")
    clean_title = _clean_title(title)
    _reserve_revision(db, product, expected_revision, operator_id=operator_id, operator_username=operator_username)
    now = _utcnow()
    db.add(ProductSection(
        product_id=product.id, title=clean_title, body="", position=len(product.sections),
        created_by_operator_id=operator_id, created_by_username=operator_username,
        updated_by_operator_id=operator_id, updated_by_username=operator_username,
        created_at=now, updated_at=now,
    ))
    db.flush()
    return _load_product(db, workspace_id, product_id)


def update_section(
    db: Session,
    *, workspace_id: int, product_id: int, section_id: int, expected_revision: int,
    title: str | None, body: str | None, update_title: bool, update_body: bool,
    operator_id: int | None, operator_username: str,
) -> WorkspaceProduct:
    product = _load_product(db, workspace_id, product_id)
    section = _get_section(product, section_id)
    clean_title = _clean_title(title or "") if update_title else section.title
    clean_body = _validate_body(body or "") if update_body else section.body
    _reserve_revision(db, product, expected_revision, operator_id=operator_id, operator_username=operator_username)
    section.title = clean_title
    section.body = clean_body
    section.updated_by_operator_id = operator_id
    section.updated_by_username = operator_username
    section.updated_at = _utcnow()
    db.flush()
    return _load_product(db, workspace_id, product_id)


def reorder_sections(
    db: Session,
    *, workspace_id: int, product_id: int, section_ids: list[int], expected_revision: int,
    operator_id: int | None, operator_username: str,
) -> WorkspaceProduct:
    product = _load_product(db, workspace_id, product_id)
    # State-dependent permutation validation must not mask a stale client.
    # The conditioned UPDATE in _reserve_revision remains the final atomic gate.
    _ensure_expected_revision(product, expected_revision)
    existing_ids = [item.id for item in product.sections]
    if len(section_ids) != len(set(section_ids)) or set(section_ids) != set(existing_ids):
        raise ProductServiceError("section_ids deve ser a permutação completa das Seções do Produto.")
    _reserve_revision(db, product, expected_revision, operator_id=operator_id, operator_username=operator_username)
    sections = {item.id: item for item in product.sections}
    # Avoid transient UNIQUE(position) collisions while assigning the permutation.
    for offset, item in enumerate(product.sections, start=len(product.sections) + 1):
        item.position = offset
    db.flush()
    for position, section_id in enumerate(section_ids):
        sections[section_id].position = position
    db.flush()
    return _load_product(db, workspace_id, product_id)


def set_section_blocks(
    db: Session,
    *, workspace_id: int, product_id: int, section_id: int, block_ids: list[int],
    expected_revision: int, operator_id: int | None, operator_username: str,
) -> WorkspaceProduct:
    product = _load_product(db, workspace_id, product_id)
    section = _get_section(product, section_id)
    if len(block_ids) > MAX_BLOCKS_PER_SECTION:
        raise ProductServiceError(f"Uma Seção aceita no máximo {MAX_BLOCKS_PER_SECTION} blocos.")
    if len(block_ids) != len(set(block_ids)):
        raise ProductServiceError("block_ids não aceita IDs duplicados.")
    blocks = db.query(InvestigativeBlock).filter(InvestigativeBlock.id.in_(block_ids)).all() if block_ids else []
    by_id = {item.id: item for item in blocks}
    if set(by_id) != set(block_ids) or any(item.workspace_id != workspace_id for item in blocks):
        raise ProductServiceError("block_ids contém bloco inválido para este Workspace.")
    existing = {item.block_id: item for item in section.block_links}
    for block_id in block_ids:
        if by_id[block_id].status == "discarded" and block_id not in existing:
            raise ProductServiceError("Não é permitido criar associação com bloco descartado.")
    _reserve_revision(db, product, expected_revision, operator_id=operator_id, operator_username=operator_username)
    for link in list(section.block_links):
        if link.block_id not in block_ids:
            db.delete(link)
    # Move retained rows aside before restoring contiguous positions.
    for offset, link in enumerate(existing.values(), start=len(existing) + len(block_ids) + 1):
        if link.block_id in block_ids:
            link.position = offset
    db.flush()
    now = _utcnow()
    for position, block_id in enumerate(block_ids):
        link = existing.get(block_id)
        if link is None:
            link = ProductSectionBlock(
                section_id=section.id, block_id=block_id,
                created_by_operator_id=operator_id, created_by_username=operator_username,
                created_at=now,
            )
            db.add(link)
        link.position = position
    db.flush()
    return _load_product(db, workspace_id, product_id)
