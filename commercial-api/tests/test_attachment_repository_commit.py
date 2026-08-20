"""Regressão: INSERT/DELETE de anexos devem commit (execute_returning_one)."""

from pathlib import Path


REPO = (
    Path(__file__).resolve().parents[1]
    / "commercial_app"
    / "infrastructure"
    / "persistence"
    / "repositories"
    / "postgres_attachment_repository.py"
).read_text(encoding="utf-8")


def test_attachment_create_and_delete_commit_via_execute_returning_one() -> None:
    create_block = REPO.split("def create(", 1)[1].split("def delete(", 1)[0]
    delete_block = REPO.split("def delete(", 1)[1]
    assert "execute_returning_one" in create_block
    assert "self.fetch_one" not in create_block
    assert "execute_returning_one" in delete_block
    assert "self.fetch_one" not in delete_block
