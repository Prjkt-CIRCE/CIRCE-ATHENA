"""
photo_service.py — Servico de cadastro e busca do Banco de Fotos.
Pipeline: upload -> SHA-256 -> salvar arquivo -> extrair embedding -> persistir -> audit log.
"""
import hashlib
import logging
import numpy as np
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.photo import Photo
from app.models.operator import Operator
from app.services.audit_service import log_action
from app.services.face_service import extract_embedding, compare_embeddings

logger = logging.getLogger(__name__)

PHOTOS_DIR = Path(settings.data_dir) / "photos"
EMBEDDINGS_DIR = Path(settings.data_dir) / "embeddings"


def _ensure_dirs() -> None:
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _save_embedding(photo_id: int, embedding: np.ndarray) -> str:
    """Salva embedding como arquivo .npy e retorna o caminho relativo."""
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"photo_{photo_id}.npy"
    path = EMBEDDINGS_DIR / filename
    np.save(str(path), embedding)
    return str(path)


def cadastrar_foto(
    db: Session,
    temp_path: str,
    original_filename: str,
    nome_completo: str,
    sexo: str,
    etnia_cor: str,
    contexto_foto: str,
    fonte: str,
    grau_confiabilidade: str,
    operador: Operator,
    alcunhas: str | None = None,
    cpf: str | None = None,
    data_nascimento: str | None = None,
    estatura: str | None = None,
    compleicao: str | None = None,
    sinais_particulares: str | None = None,
    organizacao_id: int | None = None,
    caso_vinculado: str | None = None,
    observacoes: str | None = None,
) -> Photo:
    """
    Cadastra uma foto no banco institucional.

    Fluxo:
    1. Calcula SHA-256 do arquivo temporario
    2. Move arquivo para data/photos/ com nome canonico
    3. Persiste registro Photo no banco
    4. Extrai embedding facial (InsightFace)
    5. Salva embedding em data/embeddings/
    6. Atualiza Photo com caminho do embedding
    7. Registra no audit log
    """
    _ensure_dirs()

    # 1. SHA-256
    sha256 = _sha256_file(temp_path)

    # 2. Nome canonico e destino
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ext = Path(original_filename).suffix.lower() or ".jpg"
    canonical_name = f"{ts}_{sha256[:8]}{ext}"
    dest_path = PHOTOS_DIR / canonical_name
    shutil.move(temp_path, str(dest_path))

    # 3. Persiste Photo (sem embedding ainda)
    photo = Photo(
        nome_completo=nome_completo,
        alcunhas=alcunhas,
        cpf=cpf,
        data_nascimento=data_nascimento,
        sexo=sexo,
        etnia_cor=etnia_cor,
        estatura=estatura,
        compleicao=compleicao,
        sinais_particulares=sinais_particulares,
        organizacao_id=organizacao_id,
        caso_vinculado=caso_vinculado,
        contexto_foto=contexto_foto,
        fonte=fonte,
        grau_confiabilidade=grau_confiabilidade,
        observacoes=observacoes,
        caminho_foto=str(dest_path),
        sha256_foto=sha256,
        operador_id=operador.id,
        operador_nome=operador.full_name,
        cadastrado_em=datetime.now(timezone.utc),
    )
    db.add(photo)
    db.flush()  # obtem photo.id sem commit

    # 4. Extrai embedding
    embedding_path = None
    embedding_model = None
    embedding_extraido_em = None

    try:
        embedding, model_name = extract_embedding(str(dest_path))
        if embedding is not None:
            # 5. Salva embedding
            emb_path = _save_embedding(photo.id, embedding)
            embedding_path = emb_path
            embedding_model = model_name
            embedding_extraido_em = datetime.now(timezone.utc).isoformat()
            logger.info(f"Embedding extraido para photo.id={photo.id}")
        else:
            logger.warning(f"Nenhuma face detectada em photo.id={photo.id} — embedding nao gerado")
    except Exception as e:
        logger.error(f"Erro ao extrair embedding para photo.id={photo.id}: {e}")

    # 6. Atualiza com embedding
    photo.embedding_path = embedding_path
    photo.embedding_model = embedding_model
    photo.embedding_extraido_em = embedding_extraido_em

    # 7. Audit log + commit atomico
    log_action(
        db=db,
        operator_id=operador.id,
        operator_username=operador.username,
        action="photo_cadastro",
        entity_type="photo",
        entity_id=str(photo.id),
        description=(
            f"Foto cadastrada: {nome_completo} | "
            f"SHA256={sha256[:16]}... | "
            f"Embedding={'sim' if embedding_path else 'nao detectado'}"
        ),
        manage_transaction=False,
    )
    db.commit()

    return photo


def buscar_fotos(
    db: Session,
    nome: str | None = None,
    sexo: str | None = None,
    etnia_cor: str | None = None,
    grau_confiabilidade: str | None = None,
    organizacao_id: int | None = None,
    sinais_particulares: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Photo], int]:
    """
    Busca fotos por campos estruturados.
    Retorna (lista, total).
    """
    q = db.query(Photo)

    if nome:
        q = q.filter(Photo.nome_completo.ilike(f"%{nome}%"))
    if sexo:
        q = q.filter(Photo.sexo == sexo)
    if etnia_cor:
        q = q.filter(Photo.etnia_cor == etnia_cor)
    if grau_confiabilidade:
        q = q.filter(Photo.grau_confiabilidade == grau_confiabilidade)
    if organizacao_id:
        q = q.filter(Photo.organizacao_id == organizacao_id)
    if sinais_particulares:
        q = q.filter(Photo.sinais_particulares.ilike(f"%{sinais_particulares}%"))

    total = q.count()
    fotos = q.order_by(Photo.cadastrado_em.desc()).offset(offset).limit(limit).all()
    return fotos, total


def comparar_foto(
    db: Session,
    temp_path: str,
    operador: Operator,
    top_k: int = 5,
    threshold: float = 0.4,
) -> tuple[list[dict], str | None]:
    """
    Compara imagem de consulta contra banco de embeddings.

    Retorna:
        (candidatos, aviso)
        candidatos: lista de dicts {photo, score} ordenados por score desc
        aviso: mensagem de advertencia se aplicavel (ex: nenhuma face detectada)
    """
    # Extrai embedding da imagem de consulta
    try:
        query_embedding, _ = extract_embedding(temp_path)
    except Exception as e:
        return [], f"Erro ao processar imagem: {e}"

    if query_embedding is None:
        log_action(
            db=db,
            operator_id=operador.id,
            operator_username=operador.username,
            action="photo_comparacao",
            entity_type="photo",
            entity_id=None,
            description="Comparacao facial: nenhuma face detectada na imagem de consulta",
            manage_transaction=True,
        )
        return [], "Nenhuma face detectada na imagem enviada."

    # Busca fotos com embedding gerado
    fotos_com_embedding = db.query(Photo).filter(
        Photo.embedding_path.isnot(None)
    ).all()

    if not fotos_com_embedding:
        return [], "Banco de fotos vazio ou sem embeddings gerados."

    # Carrega embeddings e calcula similaridade
    candidatos = []
    for foto in fotos_com_embedding:
        try:
            emb = np.load(foto.embedding_path)
            scores = compare_embeddings(query_embedding, [emb])
            score = scores[0]
            if score >= threshold:
                candidatos.append({"photo": foto, "score": score})
        except Exception as e:
            logger.warning(f"Erro ao carregar embedding photo.id={foto.id}: {e}")
            continue

    # Ordena por score e limita ao top_k
    candidatos.sort(key=lambda x: x["score"], reverse=True)
    candidatos = candidatos[:top_k]

    # Audit log da comparacao
    sha256_query = _sha256_file(temp_path) if os.path.isfile(temp_path) else "N/A"
    ids_candidatos = [str(c["photo"].id) for c in candidatos]
    log_action(
        db=db,
        operator_id=operador.id,
        operator_username=operador.username,
        action="photo_comparacao",
        entity_type="photo",
        entity_id=None,
        description=(
            f"Comparacao facial | SHA256_query={sha256_query[:16]}... | "
            f"Candidatos retornados: {ids_candidatos} | "
            f"Total no banco com embedding: {len(fotos_com_embedding)}"
        ),
        manage_transaction=True,
    )

    return candidatos, None