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
