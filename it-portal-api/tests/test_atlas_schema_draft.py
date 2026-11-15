"""Static safeguards for a review-only DDL draft, not a PostgreSQL migration."""
from pathlib import Path

DDL = (
    Path(__file__).resolve().parents[2]
    / "docs/12-roadmap-e-evolucao/mcp-linux-control/05-atlas-p22d-candidate-schema.sql"
).read_text(encoding="utf-8")


def test_schema_outside_automatic_migrations():
    assert "REVIEW-ONLY" in DDL
    assert "CREATE TABLE it_portal.atlas_deploy_challenges" in DDL
    assert "CREATE TABLE it_portal.atlas_deploy_proposals" in DDL
    assert "CREATE TABLE it_portal.atlas_deploy_events" in DDL


def test_uniqueness_and_expiration_required():
    assert "UNIQUE (requester_subject, request_id)" in DDL
    assert "challenge_digest char(64) NOT NULL UNIQUE" in DDL
    assert "ON DELETE RESTRICT" in DDL
    assert "status = 'executing'" in DDL
    assert "interval '90 seconds'" in DDL
    assert "interval '10 minutes'" in DDL


def test_no_privileged_grants_or_destructive_ddl():
    assert not any(item in DDL.upper() for item in (
        "CREATE ROLE ", "GRANT ALL ", "DROP TABLE ", "DO $$", "EXECUTE PROCEDURE",
    ))
