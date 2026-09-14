from tm_app.application.gpt_actions.improvement_package_contract import (
    PACKAGE_BLOCK_KEYS,
    PACKAGE_TOP_LEVEL_KEYS,
    build_package_hints,
)
from tm_app.application.gpt_actions.registration_guide import build_registration_guide


def test_registration_guide_does_not_mark_governed_document_writes_ui_only():
    guide = build_registration_guide()
    hints = guide["package_hints"]

    assert "diagrams" not in hints["ui_only_persist"]
    assert "WBS/decomposition" not in hints["ui_only_persist"]
    assert hints["ui_only_persist"] == [
        "evidence uploads",
        "meeting-minute handwritten signature",
    ]

    governed = hints["governed_document_writes"]
    assert governed["support_is_not_authorization"] is True
    assert "surface_supports.persist_diagram_via_gpt=true" in governed["diagram"]
    assert "surface_supports.persist_decomposition_via_gpt=true" in governed["decomposition"]
    assert governed["flow"] == "PREPARE → SHOW → CONFIRM → WRITE → VERIFY"


def test_registration_flow_routes_only_unsupported_followups_to_ui():
    guide = build_registration_guide()
    followup = next(
        step for step in guide["registration_flow"] if step["id"] == "governed_followups"
    )
    actions = " ".join(followup["actions"])

    assert "Diagrams and WBS/decomposition may be persisted via GPT" in actions
    assert "evidence uploads" in actions
    assert "meeting-minute handwritten signatures" in actions
    assert "Point user to Minha DELPI UI for diagrams" not in actions


def test_registration_guide_contains_canonical_package_shape():
    hints = build_registration_guide()["package_hints"]
    shape = hints["canonical_package_shape"]
    assert shape["top_level"] == list(PACKAGE_TOP_LEVEL_KEYS)
    assert shape["scenario"]["keys"] == list(PACKAGE_BLOCK_KEYS)
    assert "revision" in shape["scenario"]["keys"]
    assert "measurement" in shape["scenario"]["keys"]
    assert "investments" in shape["scenario"]["keys"]
    assert "beneficio_calculo_categoria" in shape["revision_fields"]
    assert "READ CONTRACT" in hints["operational_sequence"][0]
    assert "VALIDATE PACKAGE" in hints["operational_sequence"][3]
    assert hints["validate_operationId"] == "gpt_validate_improvement_package"
    assert hints["commit_operationId"] == "gpt_commit_improvement_package"
    assert hints["dry_run_semantics"]["ready_false_is_not_tool_failure"] is True


def test_canonical_reuse_example_uses_scenario_revision():
    example = build_package_hints()["reuse_existing_example"]
    assert "processo_id" in example["process"]
    assert "instancia_id" in example["instance"]
    assert "revision" in example["scenario"]
    assert "versao_revisao" in example["scenario"]["revision"]
    assert "processo_id" not in example["scenario"]
    assert "versao_revisao" not in example["scenario"]
    assert example["scenario"]["investments"] == []
    assert "beneficio_calculo_categoria" in example["scenario"]["revision"]


def test_package_hints_examples_include_create_and_baseline_plus_scenario():
    hints = build_package_hints()
    create = hints["create_new_example"]
    combo = hints["baseline_plus_scenario_example"]
    assert create["baseline"]["revision"]["versao_revisao"]
    assert create["scenario"]["revision"]["cenario_tipo"] == "melhoria"
    assert "revision" in combo["baseline"]
    assert "revision" in combo["scenario"]
    validate = hints["validate_example"]
    assert "dry_run" not in validate
    assert "revision" in validate["scenario"]
