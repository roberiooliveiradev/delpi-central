from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "infra" / "README-ambiente.md"
COMPOSE_PROD = ROOT / "infra" / "docker-compose.yml"
COMPOSE_DEV = ROOT / "infra" / "docker-compose.dev.yml"

CONTAINER_DIR = "/app/data/commercial-attachments"
VOLUME_SUFFIX = f"commercial-attachments:{CONTAINER_DIR}"


def test_readme_documents_room_message_subdir() -> None:
    text = README.read_text(encoding="utf-8")
    assert "COMMERCIAL_ATTACHMENT_UPLOAD_DIR" in text
    assert CONTAINER_DIR in text
    assert "room_message/{messageId}/" in text
    assert "Não criar volume extra" in text or "não criar volume extra" in text.lower()


def test_compose_mounts_same_container_path() -> None:
    prod = COMPOSE_PROD.read_text(encoding="utf-8")
    dev = COMPOSE_DEV.read_text(encoding="utf-8")
    assert VOLUME_SUFFIX in prod
    assert VOLUME_SUFFIX in dev
    assert f"COMMERCIAL_ATTACHMENT_UPLOAD_DIR: {CONTAINER_DIR}" in prod
    assert f"COMMERCIAL_ATTACHMENT_UPLOAD_DIR: {CONTAINER_DIR}" in dev
