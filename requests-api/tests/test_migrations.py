from requests_app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
    SCHEMA_NAME,
    calculate_checksum,
    list_migration_files,
    parse_version_and_name,
)


def test_migrations_dir_exists():
    assert MIGRATIONS_DIR.is_dir()


def test_list_migration_files_in_order():
    files = list_migration_files()
    names = [path.name for path in files]
    assert names == [
        "V001__schema_migrations.sql",
        "V002__core_domain.sql",
        "V003__idempotency_keys.sql",
        "V004__attachments_artifacts_events.sql",
        "V005__integration_outbox.sql",
        "V006__seed_invoice_issuance_request_type.sql",
        "V007__seed_raw_material_creation_request_type.sql",
        "V008__request_type_journey_progress.sql",
        "V009__request_correction_targets.sql",
        "V010__comment_attachments.sql",
        "V011__invoice_issue_confirmation_workflow.sql",
        "V012__invoice_reject_fulfillment_and_file_lock.sql",
    ]


def test_parse_version_and_name():
    version, name = parse_version_and_name(list_migration_files()[0])
    assert version == "V001"
    assert name == "schema_migrations"


def test_calculate_checksum_is_stable():
    path = list_migration_files()[0]
    first = calculate_checksum(path)
    second = calculate_checksum(path)
    assert first == second
    assert len(first) == 64


def test_schema_name():
    assert SCHEMA_NAME == "my_requests"


def test_v002_contains_core_tables():
    v002 = MIGRATIONS_DIR / "V002__core_domain.sql"
    sql = v002.read_text(encoding="utf-8")
    for table in (
        "request_types",
        "requests",
        "request_status_history",
        "request_assignments",
        "request_comments",
    ):
        assert table in sql

    _, name = parse_version_and_name(v002)
    assert name == "core_domain"


def test_v006_seeds_invoice_issuance():
    v006 = MIGRATIONS_DIR / "V006__seed_invoice_issuance_request_type.sql"
    sql = v006.read_text(encoding="utf-8")
    assert "invoice-issuance" in sql
    assert "my-requests.invoice-issuance" in sql
    assert "api_delpi" in sql
    _, name = parse_version_and_name(v006)
    assert name == "seed_invoice_issuance_request_type"


def test_v007_seeds_raw_material_creation():
    v007 = MIGRATIONS_DIR / "V007__seed_raw_material_creation_request_type.sql"
    sql = v007.read_text(encoding="utf-8")
    assert "raw-material-creation" in sql
    assert "schema_driven" in sql
    assert "my-requests.raw-material-creation" in sql
    assert "description" in sql
    _, name = parse_version_and_name(v007)
    assert name == "seed_raw_material_creation_request_type"


def test_v008_adds_journey_progress_metadata():
    v008 = MIGRATIONS_DIR / "V008__request_type_journey_progress.sql"
    sql = v008.read_text(encoding="utf-8")
    assert "journey" in sql
    assert "invoice-issuance" in sql
    assert "raw-material-creation" in sql
    assert "statusMappings" in sql
    _, name = parse_version_and_name(v008)
    assert name == "request_type_journey_progress"


def test_v011_invoice_confirmation_and_artifact_require():
    v011 = MIGRATIONS_DIR / "V011__invoice_issue_confirmation_workflow.sql"
    sql = v011.read_text(encoding="utf-8")
    assert "awaiting_requester_confirmation" in sql
    assert "confirm_fulfillment" in sql
    assert "invoice_pdf" in sql
    assert "invoice-issuance" in sql
    _, name = parse_version_and_name(v011)
    assert name == "invoice_issue_confirmation_workflow"


def test_v012_reject_fulfillment_and_file_lock():
    v012 = MIGRATIONS_DIR / "V012__invoice_reject_fulfillment_and_file_lock.sql"
    sql = v012.read_text(encoding="utf-8")
    assert "reject_fulfillment" in sql
    assert "fileImmutableStatuses" in sql
    assert "awaiting_requester_confirmation" in sql
    assert "invoice-issuance" in sql
    _, name = parse_version_and_name(v012)
    assert name == "invoice_reject_fulfillment_and_file_lock"
