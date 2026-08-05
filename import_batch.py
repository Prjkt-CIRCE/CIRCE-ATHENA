"""
import_batch.py -- Script CLI de importacao em lote do acervo NAS.
Sprint AT-02b (D-AT-013)

Uso:
    python import_batch.py --pasta C:\Caminho\Para\Fotos --operador admin [--dry-run]

Comportamento:
    - Varre recursivamente a pasta buscando .jpg, .jpeg, .png
    - Para cada imagem: calcula SHA-256, verifica duplicata, extrai embedding, persiste
    - Campos de metadados preenchidos com sentinela [IMPORTADO_LOTE] (D-AT-013)
    - Registra no audit log com operador informado
    - Duplicatas (mesmo SHA-256 ja no banco) sao ignoradas com aviso
    - Imagens sem rosto detectavel sao registradas como falha e o lote continua
    - --dry-run: varre e relata sem persistir nada
"""

import argparse
import hashlib
import shutil
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Garante que o modulo app e encontrado a partir da raiz do projeto
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import SessionLocal
from app.models.photo import Photo
from app.models.operator import Operator
from app.services.audit_service import log_action
from app.services.face_service import extract_embedding
from app.services.photo_service import _sha256_file, _save_embedding, _ensure_dirs, PHOTOS_DIR, EMBEDDINGS_DIR

import numpy as np

EXTENSOES_SUPORTADAS = {".jpg", ".jpeg", ".png"}

SENTINELA = "[IMPORTADO_LOTE]"


def varrer_pasta(pasta: Path) -> list[Path]:
    """Retorna lista de arquivos de imagem encontrados recursivamente."""
    arquivos = []
    for ext in EXTENSOES_SUPORTADAS:
        arquivos.extend(pasta.rglob(f"*{ext}"))
        arquivos.extend(pasta.rglob(f"*{ext.upper()}"))
    # Remove duplicatas de path (case-insensitive em Windows pode gerar)
    vistos = set()
    unicos = []
    for a in sorted(arquivos):
        key = str(a).lower()
        if key not in vistos:
            vistos.add(key)
            unicos.append(a)
    return unicos


def sha256_ja_existe(db, sha256: str) -> bool:
    return db.query(Photo).filter(Photo.sha256_foto == sha256).first() is not None


def importar_imagem(
    db,
    caminho: Path,
    operador: Operator,
    dry_run: bool,
) -> dict:
    """
    Processa uma unica imagem.
    Retorna dict com status: 'sucesso', 'duplicata', 'sem_rosto', 'erro'
    """
    resultado = {"arquivo": str(caminho), "status": None, "detalhe": ""}

    # 1. SHA-256
    try:
        sha256 = _sha256_file(str(caminho))
    except Exception as e:
        resultado["status"] = "erro"
        resultado["detalhe"] = f"Erro ao calcular SHA-256: {e}"
        return resultado

    # 2. Verifica duplicata
    if not dry_run and sha256_ja_existe(db, sha256):
        resultado["status"] = "duplicata"
        resultado["detalhe"] = f"SHA-256 {sha256[:16]}... ja existe no banco"
        return resultado

    if dry_run:
        # No dry-run, apenas verifica se teria duplicata e simula extracao
        duplicata = sha256_ja_existe(db, sha256)
        if duplicata:
            resultado["status"] = "duplicata"
            resultado["detalhe"] = f"[DRY-RUN] SHA-256 {sha256[:16]}... ja existe"
        else:
            resultado["status"] = "sucesso"
            resultado["detalhe"] = f"[DRY-RUN] Seria importada (SHA-256={sha256[:16]}...)"
        return resultado

    # 3. Copia arquivo para data/photos/ com nome canonico
    _ensure_dirs()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    ext = caminho.suffix.lower()
    canonical_name = f"{ts}_{sha256[:8]}{ext}"
    dest_path = PHOTOS_DIR / canonical_name

    try:
        shutil.copy2(str(caminho), str(dest_path))
    except Exception as e:
        resultado["status"] = "erro"
        resultado["detalhe"] = f"Erro ao copiar arquivo: {e}"
        return resultado

    # 4. Persiste Photo com sentinela
    photo = Photo(
        nome_completo=SENTINELA,
        alcunhas=None,
        cpf=None,
        data_nascimento=None,
        sexo=SENTINELA,
        etnia_cor=SENTINELA,
        estatura=None,
        compleicao=None,
        sinais_particulares=None,
        organizacao_id=None,
        caso_vinculado=str(caminho.parent.name),  # nome da pasta de origem como contexto
        contexto_foto=SENTINELA,
        fonte=f"Importacao em lote: {caminho.parent}",
        grau_confiabilidade="nao_verificada",
        observacoes=f"Arquivo original: {caminho.name}",
        caminho_foto=str(dest_path),
        sha256_foto=sha256,
        importado_em_lote=True,
        revisado_em=None,
        operador_id=operador.id,
        operador_nome=operador.full_name,
        cadastrado_em=datetime.now(timezone.utc),
    )
    db.add(photo)
    db.flush()

    # 5. Extrai embedding
    embedding_path = None
    embedding_model = None
    embedding_extraido_em = None
    sem_rosto = False

    try:
        embedding, model_name = extract_embedding(str(dest_path))
        if embedding is not None:
            emb_path = _save_embedding(photo.id, embedding)
            embedding_path = emb_path
            embedding_model = model_name
            embedding_extraido_em = datetime.now(timezone.utc).isoformat()
        else:
            sem_rosto = True
    except Exception as e:
        sem_rosto = True
        resultado["detalhe"] = f"Extracao falhou: {e}"

    photo.embedding_path = embedding_path
    photo.embedding_model = embedding_model
    photo.embedding_extraido_em = embedding_extraido_em

    # 6. Audit log + commit
    log_action(
        db=db,
        operator_id=operador.id,
        operator_username=operador.username,
        action="photo_cadastro",
        entity_type="photo",
        entity_id=str(photo.id),
        description=(
            f"Foto cadastrada [importacao_lote]: {caminho.name} | "
            f"SHA256={sha256[:16]}... | "
            f"Embedding={'sim' if embedding_path else 'nao detectado'}"
        ),
        manage_transaction=False,
    )
    db.commit()

    if sem_rosto:
        resultado["status"] = "sem_rosto"
        resultado["detalhe"] = resultado["detalhe"] or "Nenhuma face detectada — registro criado sem embedding"
    else:
        resultado["status"] = "sucesso"
        resultado["detalhe"] = f"photo.id={photo.id} | SHA256={sha256[:16]}..."

    return resultado


def main():
    parser = argparse.ArgumentParser(
        description="Importacao em lote de fotos para o banco CIRCE Athena."
    )
    parser.add_argument(
        "--pasta",
        required=True,
        help="Caminho da pasta a varrer recursivamente",
    )
    parser.add_argument(
        "--operador",
        required=True,
        help="Username do operador responsavel pela importacao",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula a importacao sem persistir nada no banco",
    )
    args = parser.parse_args()

    pasta = Path(args.pasta)
    if not pasta.exists() or not pasta.is_dir():
        print(f"[ERRO] Pasta nao encontrada: {pasta}")
        sys.exit(1)

    dry_run = args.dry_run

    # Abre sessao e valida operador
    db = SessionLocal()
    try:
        operador = db.query(Operator).filter(Operator.username == args.operador).first()
        if operador is None:
            print(f"[ERRO] Operador '{args.operador}' nao encontrado no banco.")
            print("       Use o username exato cadastrado no sistema.")
            sys.exit(1)

        print()
        print("=" * 60)
        print("  CIRCE Athena -- Importacao em Lote")
        print("=" * 60)
        print(f"  Pasta    : {pasta}")
        print(f"  Operador : {operador.full_name} ({operador.username})")
        print(f"  Modo     : {'DRY-RUN (nenhum dado sera salvo)' if dry_run else 'EXECUCAO REAL'}")
        print("=" * 60)

        # Varre arquivos
        arquivos = varrer_pasta(pasta)
        total = len(arquivos)

        if total == 0:
            print("\n  Nenhuma imagem encontrada na pasta.")
            sys.exit(0)

        print(f"\n  {total} imagem(ns) encontrada(s). Iniciando processamento...\n")

        # Contadores
        sucessos = 0
        sem_rosto = 0
        duplicatas = 0
        erros = 0

        for i, caminho in enumerate(arquivos, start=1):
            prefixo = f"[{i:>4}/{total}]"
            resultado = importar_imagem(db, caminho, operador, dry_run)

            status = resultado["status"]
            detalhe = resultado["detalhe"]
            nome = caminho.name

            if status == "sucesso":
                sucessos += 1
                print(f"{prefixo} OK       {nome}")
                if detalhe:
                    print(f"           {detalhe}")
            elif status == "sem_rosto":
                sem_rosto += 1
                print(f"{prefixo} SEM_ROSTO {nome}")
                print(f"           {detalhe}")
            elif status == "duplicata":
                duplicatas += 1
                print(f"{prefixo} DUPLICATA {nome}")
                print(f"           {detalhe}")
            elif status == "erro":
                erros += 1
                print(f"{prefixo} ERRO     {nome}")
                print(f"           {detalhe}")

        # Relatorio final
        print()
        print("=" * 60)
        print("  RELATORIO FINAL")
        print("=" * 60)
        print(f"  Total encontrado : {total}")
        print(f"  Importados       : {sucessos}")
        print(f"  Sem rosto        : {sem_rosto}  (registrados, sem embedding)")
        print(f"  Duplicatas       : {duplicatas}  (ignorados)")
        print(f"  Erros            : {erros}")
        print("=" * 60)

        if dry_run:
            print()
            print("  [DRY-RUN] Nenhum dado foi persistido.")

        if sem_rosto > 0 and not dry_run:
            print()
            print(f"  AVISO: {sem_rosto} foto(s) importada(s) sem rosto detectavel.")
            print("  Esses registros constam no banco com flag PENDENTE")
            print("  e precisam de revisao humana antes de uso em comparacoes.")

        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()