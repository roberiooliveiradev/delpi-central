from tm_app.application.gpt_actions.improvement_package_contract import (
    PACKAGE_BLOCK_KEYS,
    PACKAGE_TOP_LEVEL_KEYS,
    build_package_hints,
)
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    build_gpt_actions_openapi,
    count_operations,
)
from tm_app.application.gpt_actions.registration_guide import build_registration_guide


def test_registration_guide_does_not_mark_governed_document_writes_ui_only():
    guide = build_registration_guide()
    hints = guide["package_hints"]

    assert "diagrams" not in hints["ui_only_persist"]
    assert "WBS/decomposition" not in hints["ui_only_persist"]
    assert "binary evidence uploads" in hints["ui_only_persist"]
    assert "meeting-minute handwritten signature" in hints["ui_only_persist"]
    assert "evidence uploads" not in hints["ui_only_persist"]
    parity = hints["gpt_governed_parity"]
    assert "gpt_list_evidence" in parity["evidence_link_metadata"]
    assert "gpt_manage_evidence" in parity["evidence_link_metadata"]
    assert "gpt_get_process_timeline" in parity["process_timeline"]
    assert "gpt_adjust_shared_resource_cost" in parity[
        "shared_resource_cost_adjustment"
    ]
    assert "gpt_meeting_minute_manage" in parity["meeting_minute_extras"]

    governed = hints["governed_document_writes"]
    assert governed["support_is_not_authorization"] is True
    assert "surface_supports.persist_diagram_via_gpt=true" in governed["diagram"]
    assert "surface_supports.persist_decomposition_via_gpt=true" in governed["decomposition"]
    assert governed["flow"] == (
        "PREPARE → SHOW → CONFIRM → COMMIT → AUTHORITATIVE READ-BACK → VERIFY"
    )


def test_registration_flow_routes_only_unsupported_followups_to_ui():
    guide = build_registration_guide()
    followup = next(
        step for step in guide["registration_flow"] if step["id"] == "governed_followups"
    )
    actions = " ".join(followup["actions"])

    assert "Diagrams and WBS/decomposition may be persisted via GPT" in actions
    assert "gpt_list_evidence" in actions
    assert "gpt_manage_evidence" in actions
    assert "binary evidence upload" in actions.lower()
    assert "meeting-minute handwritten signatures" in actions
    assert "Point user to Minha DELPI UI for diagrams" not in actions
    assert "universally UI-only" not in actions.lower()


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
    assert hints["commit_operationId"] == "gpt_commit_proposal"
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


def test_registration_guide_official_flow_validate_confirm_commit_readback():
    hints = build_registration_guide()["package_hints"]
    seq = " | ".join(hints["operational_sequence"])
    assert "VALIDATE PACKAGE" in seq
    assert "SHOW USER" in seq
    assert "EXPLICIT CONFIRMATION" in seq
    assert "COMMIT" in seq
    assert "READ-BACK" in seq
    assert "VERIFY" in seq
    # Validate before commit in sequence order.
    assert seq.index("VALIDATE") < seq.index("COMMIT")
    assert seq.index("COMMIT") < seq.index("READ-BACK")


def test_registration_guide_commit_result_unknown_policy():
    hints = build_registration_guide()["package_hints"]
    unknown = hints["commit_result_unknown"]
    assert unknown["do_not_claim_success"] is True
    assert unknown["inspect_read_current_state_before_retry"] is True
    assert unknown["avoid_duplicate_write"] is True
    assert unknown["no_http_bypass"] is True
    assert unknown["no_silent_create_update_substitute"] is True
    assert unknown["no_retry_loop"] is True
    assert unknown["package_change_invalidates_confirmation"] is True
    assert "read_back" in unknown["success_requires"]
    assert "verify" in unknown["success_requires"]
    joined = " ".join(unknown["notes"]).lower()
    assert "unknown" in joined
    assert "saved" in joined or "cadastrado" in joined or "gravado" in joined
    states = hints["persistence_outcome_states"]
    assert states == [
        "VALIDATED",
        "CONFIRMED",
        "COMMIT_ATTEMPTED",
        "COMMIT_CONFIRMED",
        "PERSISTED",
        "VERIFIED",
    ]


def test_teo_contract_drift_openapi_guide_instructions():
    """Drift gate: OpenAPI ↔ guide ↔ specialist instructions stay aligned."""
    from pathlib import Path

    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS)
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS) == 18
    assert "gpt_validate_improvement_package" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_commit_proposal" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_prepare_record_change" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_commit_improvement_package" not in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_list_evidence" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_manage_evidence" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_get_process_timeline" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_adjust_shared_resource_cost" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_meeting_minute_manage" in GPT_ACTIONS_OPERATION_IDS

    validate = doc["paths"]["/transformometro/gpt-actions/v1/improvement-packages/validate"][
        "post"
    ]
    commit = doc["paths"]["/transformometro/gpt-actions/v1/proposals/commit"]["post"]
    assert validate["x-openai-isConsequential"] is False
    assert commit["x-openai-isConsequential"] is True

    hints = build_registration_guide()["package_hints"]
    assert hints["validate_operationId"] == validate["operationId"]
    assert hints["commit_operationId"] == "gpt_commit_proposal"

    text = Path("docs/gpt-actions/specialist-instructions.md").read_text(encoding="utf-8")
    assert "gpt_prepare_record_change" in text
    assert "gpt_commit_proposal" in text
    assert "agent_directives" in text
    assert "commit_now" in text
    assert "AUTHORITATIVE READ-BACK" in text
    # Package validate lives in OpenAPI + registration_guide; paste stays budget-stable.
    assert hints["validate_operationId"] == "gpt_validate_improvement_package"

