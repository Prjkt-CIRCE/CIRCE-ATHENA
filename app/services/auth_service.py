from datetime import datetime, timezone, timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from sqlalchemy.orm import Session
from app.models.operator import Operator
from app.services.audit_service import log_action

ph = PasswordHasher()
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 30


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def get_operator_by_username(db: Session, username: str) -> Operator | None:
    return db.query(Operator).filter(
        Operator.username == username,
        Operator.is_active == True
    ).first()


def has_any_operator(db: Session) -> bool:
    return db.query(Operator).first() is not None


def create_operator(db: Session, username: str, full_name: str,
                    password: str, role: str = "operador") -> Operator:
    operator = Operator(
        username=username,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(operator)
    db.flush()
    log_action(
        db=db,
        action="operator_created",
        description=f"Operador '{username}' criado com papel '{role}'.",
        operator_username="sistema",
        entity_type="operator",
        entity_id=str(operator.id),
        manage_transaction=False,
    )
    db.commit()
    db.refresh(operator)
    return operator


def authenticate(db: Session, username: str, password: str,
                 ip_address: str | None = None) -> Operator | None:
    operator = db.query(Operator).filter(Operator.username == username).first()

    if not operator or not operator.is_active:
        log_action(db=db, action="login_failed",
                   description=f"Tentativa de login para usuario inexistente ou inativo: '{username}'.",
                   ip_address=ip_address)
        return None

    now = datetime.now(timezone.utc)
    if operator.locked_until and operator.locked_until > now:
        log_action(db=db, action="login_blocked",
                   description=f"Login bloqueado para '{username}' ate {operator.locked_until.isoformat()}.",
                   operator_id=operator.id, operator_username=username,
                   ip_address=ip_address)
        return None

    if not verify_password(password, operator.password_hash):
        operator.failed_attempts += 1
        if operator.failed_attempts >= MAX_ATTEMPTS:
            operator.locked_until = now + timedelta(seconds=LOCKOUT_SECONDS)
            operator.failed_attempts = 0
            db.commit()
            log_action(db=db, action="login_locked",
                       description=f"Conta '{username}' bloqueada por {LOCKOUT_SECONDS}s apos {MAX_ATTEMPTS} tentativas.",
                       operator_id=operator.id, operator_username=username,
                       ip_address=ip_address)
        else:
            db.commit()
            log_action(db=db, action="login_failed",
                       description=f"Senha incorreta para '{username}'. Tentativa {operator.failed_attempts}/{MAX_ATTEMPTS}.",
                       operator_id=operator.id, operator_username=username,
                       ip_address=ip_address)
        return None

    operator.failed_attempts = 0
    operator.locked_until = None
    operator.last_login = now
    db.commit()
    log_action(db=db, action="login_success",
               description=f"Login bem-sucedido para '{username}'.",
               operator_id=operator.id, operator_username=username,
               ip_address=ip_address)
    return operator
