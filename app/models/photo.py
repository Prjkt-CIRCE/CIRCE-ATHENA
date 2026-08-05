from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Identificacao ---
    nome_completo: Mapped[str] = mapped_column(String(256), nullable=False)
    alcunhas: Mapped[str | None] = mapped_column(Text, nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    data_nascimento: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # --- Caracteristicas fisicas (campos controlados) ---
    sexo: Mapped[str] = mapped_column(String(32), nullable=False)
    etnia_cor: Mapped[str] = mapped_column(String(32), nullable=False)
    estatura: Mapped[str | None] = mapped_column(String(32), nullable=True)
    compleicao: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sinais_particulares: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Vinculacao ---
    organizacao_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    caso_vinculado: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # --- Procedencia (cadeia de custodia) ---
    contexto_foto: Mapped[str] = mapped_column(String(64), nullable=False)
    fonte: Mapped[str] = mapped_column(Text, nullable=False)
    grau_confiabilidade: Mapped[str] = mapped_column(String(16), nullable=False)

    # --- Texto livre ---
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Arquivo ---
    caminho_foto: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256_foto: Mapped[str] = mapped_column(String(64), nullable=False)

    # --- Embedding facial ---
    embedding_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    embedding_extraido_em: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # --- Importacao em lote (AT-02b) ---
    importado_em_lote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revisado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Status e descarte logico (AT-02c / D-AT-014) ---
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ativo")
    motivo_descarte: Mapped[str | None] = mapped_column(Text, nullable=True)
    descartado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    descartado_por: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # --- Auditoria (automaticos) ---
    operador_id: Mapped[int] = mapped_column(Integer, nullable=False)
    operador_nome: Mapped[str] = mapped_column(String(128), nullable=False)
    cadastrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )