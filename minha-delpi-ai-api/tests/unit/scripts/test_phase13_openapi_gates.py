"""Gates Fase 13 — x-delpi e pathEntityFallbacks."""

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()


def test_path_entity_fallback_pruning_gate_passes():
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "audit_path_entity_fallback_pruning",
        root / "scripts" / "audit_path_entity_fallback_pruning.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    report = module.validate()

    assert report["ok"] is True
    assert report["redundantFallbackCount"] == 0
    assert report["remainingFallbackCount"] == 0


def test_openapi_delpi_metadata_gate_passes_on_api_delpi_schema():
    import importlib.util
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    api_delpi_root = root.parent / "api-delpi"

    if not api_delpi_root.is_dir():
        import pytest

        pytest.skip("api-delpi não disponível no workspace")

    if str(api_delpi_root) not in sys.path:
        sys.path.insert(0, str(api_delpi_root))

    try:
        from app.main import app
    except Exception as exc:  # noqa: BLE001
        import pytest

        pytest.skip(f"api-delpi OpenAPI indisponível: {exc}")

    spec = importlib.util.spec_from_file_location(
        "audit_openapi_delpi_metadata",
        root / "scripts" / "audit_openapi_delpi_metadata.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    report = module.validate_schema(app.openapi())

    assert report["ok"] is True
    assert report["operations"] == report["withDelpiMetadata"]
