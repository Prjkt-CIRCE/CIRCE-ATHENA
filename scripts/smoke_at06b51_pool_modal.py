from __future__ import annotations

from app.services.case_intake_service import classify_material_bin


def main() -> None:
    assert classify_material_bin("ordem_servico.pdf") == "documents"
    assert classify_material_bin("foto_suspeito.JPG") == "images"
    assert classify_material_bin("print.png") == "images"
    assert classify_material_bin("audio.opus") == "audio"
    assert classify_material_bin("gravacao.wav") == "audio"
    assert classify_material_bin("video.mp4") == "video"
    assert classify_material_bin("sem_extensao") == "documents"
    assert classify_material_bin("arquivo.bin", "image/jpeg") == "images"

    print("AT-06B5.1 SMOKE: OK")
    print("classification=documents/images/audio/video")


if __name__ == "__main__":
    main()
