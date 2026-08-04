from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.operator import AuditLog


GENESIS_HASH = "0" * 64


def get_last_hash(db: Session) -> str:
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    return last.current_hash if last else GENESIS_HASH


def log_action(
    db: Session,
    action: str,
    description: str,
    operator_id: int | None = None,
    operator_username: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    ip_address: str | None = None,
    manage_transaction: bool = True,
) -> AuditLog:
    now = datetime.now(timezone.utc)
    previous_hash = get_last_hash(db)
    current_hash = AuditLog.compute_hash(
        previous_hash=previous_hash,
        timestamp=now.isoformat(),
        operator_username=operator_username or "",
        action=action,
        description=description,
    )
    entry = AuditLog(
        timestamp=now,
        operator_id=operator_id,
        operator_username=operator_username,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.add(entry)
    if manage_transaction:
        db.commit()
        db.refresh(entry)
    return entry
