"""
photo_service.py -- Servico de cadastro, busca e gestao do Banco de Fotos.
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

MOTIVOS_DESCARTE = [
    "Imagem sem pessoa visivel",
    "Imagem duplicada fora do sistema",
    "Qualidade insuficiente para analise",
    "Foto irrelevante para o acervo",
    "Erro de importacao",
    "Outro (ver observacoes)",
]


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
    importado_em_lote: bool = False,
) -> Photo:
    _ensure_dirs()

    sha256 = _sha256_file(temp_path)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ext = Path(original_filename).suffix.lower() or ".jpg"
    canonical_name = f"{ts}_{sha256[:8]}{ext}"
    dest_path = PHOTOS_DIR / canonical_name
    shutil.move(temp_path, str(dest_path))

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
        importado_em_lote=importado_em_lote,
        revisado_em=None,
        status="ativo",
        motivo_descarte=None,
        descartado_em=None,
        descartado_por=None,
        operador_id=operador.id,
        operador_nome=operador.full_name,
        cadastrado_em=datetime.now(timezone.utc),
    )
    db.add(photo)
    db.flush()

    embedding_path = None
    embedding_model = None
    embedding_extraido_em = None

    try:
        embedding, model_name = extract_embedding(str(dest_path))
        if embedding is not None:
            emb_path = _save_embedding(photo.id, embedding)
            embedding_path = emb_path
            embedding_model = model_name
            embedding_extraido_em = datetime.now(timezone.utc).isoformat()
            logger.info(f"Embedding extraido para photo.id={photo.id}")
        else:
            logger.warning(
                f"Nenhuma face detectada em photo.id={photo.id} -- embedding nao gerado"
            )
    except Exception as e:
        logger.error(f"Erro ao extrair embedding para photo.id={photo.id}: {e}")

    photo.embedding_path = embedding_path
    photo.embedding_model = embedding_model
    photo.embedding_extraido_em = embedding_extraido_em

    origem = "importacao_lote" if importado_em_lote else "cadastro_manual"
    log_action(
        db=db,
        operator_id=operador.id,
        operator_username=operador.username,
        action="photo_cadastro",
        entity_type="photo",
        entity_id=str(photo.id),
        description=(
            f"Foto cadastrada [{origem}]: {nome_completo} | "
            f"SHA256={sha256[:16]}... | "
            f"Embedding={'sim' if embedding_path else 'nao detectado'}"
        ),
        manage_transaction=False,
    )
    db.commit()

    return photo


def atualizar_foto(
    db: Session,
    photo: Photo,
    operador: Operator,
    nome_completo: str,
    sexo: str,
    etnia_cor: str,
    contexto_foto: str,
    fonte: str,
    grau_confiabilidade: str,
    alcunhas: str | None = None,
    cpf: str | None = None,
    data_nascimento: str | None = None,
    estatura: str | None = None,
    compleicao: str | None = None,
    sinais_particulares: str | None = None,
    caso_vinculado: str | None = None,
    observacoes: str | None = None,
) -> Photo:
    """Atualiza metadados de uma foto e marca revisado_em."""
    campos_anteriores = f"{photo.nome_completo} / {photo.sexo} / {photo.etnia_cor}"

    photo.nome_completo = nome_completo
    photo.alcunhas = alcunhas
    photo.cpf = cpf
    photo.data_nascimento = data_nascimento
    photo.sexo = sexo
    photo.etnia_cor = etnia_cor
    photo.estatura = estatura
    photo.compleicao = compleicao
    photo.sinais_particulares = sinais_particulares
    photo.contexto_foto = contexto_foto
    photo.fonte = fonte
    photo.grau_confiabilidade = grau_confiabilidade
    photo.caso_vinculado = caso_vinculado
    photo.observacoes = observacoes
    photo.revisado_em = datetime.now(timezone.utc)

    log_action(
        db=db,
        operator_id=operador.id,
        operator_username=operador.username,
        action="photo_edicao",
        entity_type="photo",
        entity_id=str(photo.id),
        description=(
            f"Metadados atualizados: {campos_anteriores} -> "
            f"{nome_completo} / {sexo} / {etnia_cor} | "
            f"revisado_em={photo.revisado_em.isoformat()}"
        ),
        manage_transaction=False,
    )
    db.commit()
    return photo


def aprovar_foto(
    db: Session,
    photo: Photo,
    operador: Operator,
    commit: bool = True,
) -> Photo:
    """Marca foto como revisada sem alterar metadados."""
    photo.revisado_em = datetime.now(timezone.utc)
    log_action(
        db=db,
        operator_id=operador.id,
        operator_username=operador.username,
        action="photo_aprovacao",
        entity_type="photo",
        entity_id=str(photo.id),
        description=f"Foto aprovada/revisada: {photo.nome_completo} | ID #{photo.id}",
        manage_transaction=False,
    )
    if commit:
        db.commit()
    return photo


def descartar_foto(
    db: Session,
    photo: Photo,
    operador: Operator,
    motivo: str,
    commit: bool = True,
) -> Photo:
    """
    Descarte logico (D-AT-014): nao exclui o registro, apenas muda status.
    Registro permanece no banco e no audit log.
    """
    photo.status = "descartado"
    photo.motivo_descarte = motivo
    photo.descartado_em = datetime.now(timezone.utc)
    photo.descartado_por = operador.username
    log_action(
        db=db,
        operator_id=operador.id,
        operator_username=operador.username,
        action="photo_descarte",
        entity_type="photo",
        entity_id=str(photo.id),
        description=(
            f"Foto descartada [logico]: {photo.nome_completo} | "
            f"ID #{photo.id} | Motivo: {motivo}"
        ),
        manage_transaction=False,
    )
    if commit:
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
    pendente_revisao: bool = False,
    incluir_descartados: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Photo], int]:
    """
    Busca fotos por campos estruturados.
    Por padrao exclui registros descartados (status != 'ativo').
    incluir_descartados=True: retorna todos independente de status.
    pendente_revisao=True: retorna apenas importados em lote sem revisao.
    """
    q = db.query(Photo)

    if not incluir_descartados:
        q = q.filter(Photo.status == "ativo")

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
    if pendente_revisao:
        q = q.filter(Photo.importado_em_lote == True, Photo.revisado_em == None)

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

    # Busca apenas fotos ativas com embedding
    fotos_com_embedding = db.query(Photo).filter(
        Photo.embedding_path.isnot(None),
        Photo.status == "ativo",
    ).all()

    if not fotos_com_embedding:
        return [], "Banco de fotos vazio ou sem embeddings gerados."

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

    candidatos.sort(key=lambda x: x["score"], reverse=True)
    candidatos = candidatos[:top_k]

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