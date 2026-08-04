"""
face_service.py — Wrapper InsightFace para extracao de embeddings faciais.
Usa CUDAExecutionProvider (RTX 4080) com fallback automatico para CPU.
D-AT-011: onnxruntime-gpu com cuDNN via pip (PATH do usuario).
"""
import os
import site
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Garante que as DLLs do cuDNN estao acessiveis antes de qualquer import de onnxruntime
def _register_nvidia_dlls() -> None:
    for sp in site.getsitepackages():
        for pkg in ["cudnn", "cublas", "cuda_nvrtc"]:
            p = os.path.join(sp, "nvidia", pkg, "bin")
            if os.path.isdir(p):
                try:
                    os.add_dll_directory(p)
                except Exception:
                    pass

_register_nvidia_dlls()

from insightface.app import FaceAnalysis  # noqa: E402 — import apos registro de DLLs

_app: FaceAnalysis | None = None


def _get_app() -> FaceAnalysis:
    """Retorna instancia singleton do FaceAnalysis (lazy init)."""
    global _app
    if _app is None:
        logger.info("Inicializando InsightFace (buffalo_l, CUDA+CPU)...")
        _app = FaceAnalysis(
            name="buffalo_l",
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        _app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("InsightFace inicializado.")
    return _app


def extract_embedding(image_path: str) -> tuple[np.ndarray | None, str]:
    """
    Extrai embedding facial de uma imagem.

    Retorna:
        (embedding, model_name) se face detectada
        (None, model_name) se nenhuma face detectada

    A imagem deve ser um arquivo de imagem valido (JPEG, PNG).
    Lanca ValueError se o arquivo nao existir ou nao for legivel.
    """
    import cv2

    if not os.path.isfile(image_path):
        raise ValueError(f"Arquivo nao encontrado: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Nao foi possivel ler a imagem: {image_path}")

    app = _get_app()
    faces = app.get(img)

    model_name = "buffalo_l"

    if not faces:
        logger.warning(f"Nenhuma face detectada em: {image_path}")
        return None, model_name

    # Usa a face de maior area (mais prominente na imagem)
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    embedding = face.embedding.astype(np.float32)

    logger.info(f"Embedding extraido: shape={embedding.shape}, norma={np.linalg.norm(embedding):.4f}")
    return embedding, model_name


def compare_embeddings(query: np.ndarray, candidates: list[np.ndarray]) -> list[float]:
    """
    Calcula similaridade coseno entre query e lista de candidatos.
    Retorna lista de scores no mesmo indice dos candidatos (0.0 a 1.0).
    Score mais alto = mais similar.
    """
    if not candidates:
        return []

    q = query / (np.linalg.norm(query) + 1e-10)
    scores = []
    for c in candidates:
        c_norm = c / (np.linalg.norm(c) + 1e-10)
        score = float(np.dot(q, c_norm))
        # Normaliza de [-1,1] para [0,1]
        scores.append((score + 1.0) / 2.0)
    return scores