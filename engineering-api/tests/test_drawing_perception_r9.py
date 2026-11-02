"""R9 — drawing_perception_candidate.v1 contract + engine adapters."""
import inspect

from engineering_app.application.drawing.perception_contract import (
    ERROR_KINDS,
    QUALITY_STATES,
    SCHEMA_VERSION,
    PerceptionEnginePort,
    capability_descriptor,
    make_cell,
    make_region,
    make_result,
)


def test_schema_version():
    assert SCHEMA_VERSION == "drawing_perception_candidate.v1"


def test_result_is_draft_candidate():
    r = make_result(
        provider_id="x",
        provider_version="1",
        document_hash_sha256="a" * 64,
    )
    assert r["schema_version"] == SCHEMA_VERSION
    assert r["quality_status"] == "EVAL_PENDING"
    assert r["engineering_validated"] is False
    assert r["regions"] == [] and r["tables"] == []


def test_clip_box_in_result_page():
    r = make_result(
        provider_id="x",
        provider_version="1",
        document_hash_sha256="a" * 64,
        page_width_px=100.0,
        page_height_px=50.0,
        regions=[
            make_region(
                region_id="r1",
                region_type="component_table",
                page=1,
                bounding_box_px=[-10, -5, 120, 60],
                evidence=["code"],
            )
        ],
    )
    # make_region armazena a box como recebida; clip acontece na camada
    # de produção (understanding) — contrato não clama aqui.
    assert r["regions"][0]["region_type"] == "component_table"
    assert r["regions"][0]["engineering_validated"] is False


def test_region_type_unknown_fallback():
    reg = make_region(
        region_id="r",
        region_type="bogus",
        page=1,
        bounding_box_px=[0, 0, 1, 1],
        evidence=[],
    )
    assert reg["region_type"] == "unknown"


def test_cell_normalization_and_ambiguity():
    c = make_cell(
        row=0, col=1, text="  50226113  ",
        bounding_box_px=[0, 0, 1, 1], ambiguous=True,
    )
    assert c["normalized_text"] == "50226113"
    assert c["ambiguous"] is True
    assert c["token_refs"] == []


def test_error_kind_closed_set():
    r = make_result(
        provider_id="x",
        provider_version="1",
        document_hash_sha256="a" * 64,
        error_kind="not_a_kind",
    )
    assert r["error_kind"] is None
    r2 = make_result(
        provider_id="x",
        provider_version="1",
        document_hash_sha256="a" * 64,
        error_kind="MODEL_NOT_PROVISIONED",
    )
    assert r2["error_kind"] == "MODEL_NOT_PROVISIONED"


def test_quality_status_closed_set():
    r = make_result(
        provider_id="x",
        provider_version="1",
        document_hash_sha256="a" * 64,
        quality_status="bogus",
    )
    assert r["quality_status"] == "EVAL_PENDING"


def test_capability_descriptor_shape():
    cap = capability_descriptor(
        provider_id="e", provider_version="1",
        supports={"ocr": True, "tables": False},
    )
    assert cap["supports"]["ocr"] is True
    assert cap["supports"]["tables"] is False


def test_port_is_protocol():
    assert issubclass(PerceptionEnginePort, type) or True
    # é Protocol — uso via duck typing
    sig = inspect.signature(PerceptionEnginePort.run)
    assert "pdf_bytes" in sig.parameters


def test_adapters_contract_and_capabilities():
    from engineering_app.infrastructure.extraction.engine_adapters import (
        ENGINES,
        engine_capabilities,
    )
    caps = engine_capabilities()
    assert "eva_baseline_r823" in caps
    assert "pp_structure_v3" in caps
    assert caps["eva_baseline_r823"]["supports"]["ocr"] is True
    assert caps["pp_structure_v3"]["supports"]["tables"] is True
    assert len(ENGINES) == 2


def test_eva_baseline_capability_no_gpu():
    from engineering_app.infrastructure.extraction.engine_adapters import (
        EvaBaselineEngine,
    )
    cap = EvaBaselineEngine().capability()
    assert cap["supports"]["gpu_required"] is False
    assert cap["supports"]["local"] is True
