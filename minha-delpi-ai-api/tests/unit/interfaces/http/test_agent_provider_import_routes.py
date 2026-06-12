from pathlib import Path


def test_agent_provider_import_route_supports_async_job():
    source = Path(
        "app/interfaces/http/routes/chat/agent_provider_routes.py"
    ).read_text()

    assert 'request.args.get("async", "").lower() == "true"' in source
    assert "ExternalActionImportJobService.start" in source
    assert "EXTERNAL_ACTION_IMPORT_ASYNC_ENABLED" in source
    assert "return jsonify(job), 202" in source


def test_provider_import_job_status_route_exists():
    source = Path(
        "app/interfaces/http/routes/chat/agent_provider_routes.py"
    ).read_text()

    assert (
        '@chat_bp.get("/providers/<provider_key>/import/jobs/<job_id>")'
        in source
    )
    assert "ExternalActionImportJobService.get" in source
    assert "return jsonify(job), 200" in source


def test_sync_import_path_preserved():
    source = Path(
        "app/interfaces/http/routes/chat/agent_provider_routes.py"
    ).read_text()

    assert "repository.import_schema_from_url(provider_key=provider_key)" in source
    assert "return jsonify(result), 200" in source
