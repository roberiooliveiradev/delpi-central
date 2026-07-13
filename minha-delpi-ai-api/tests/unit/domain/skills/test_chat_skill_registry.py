from app.domain.skills.chat_skill_registry import ChatSkillRegistry


def test_catalog_lists_sql_skill():
    from app.domain.skills.chat_skill_registry import invalidate_skill_cache

    invalidate_skill_cache()
    catalog = ChatSkillRegistry.list_catalog()

    assert any(item["skillKey"] == "sql" for item in catalog)
    assert any(item["skillKey"] == "company-knowledge" for item in catalog)
    assert any(item["skillKey"] == "technical-description-delpi" for item in catalog)
    assert any(item["skillKey"] == "quality-action-plans-delpi" for item in catalog)


def test_common_chat_uses_default_technical_description():
    from app.domain.skills.chat_skill_registry import invalidate_skill_cache

    invalidate_skill_cache()
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=False,
        default_company_knowledge=True,
    )

    technical = next(
        item
        for item in bindings
        if item["skillKey"] == "technical-description-delpi"
    )

    assert technical["enabled"] is True

    resolved = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=False,
        default_company_knowledge=True,
    )

    assert resolved["technicalDescription"] is True


def test_technical_description_skill_can_be_disabled():
    from app.domain.skills.chat_skill_registry import invalidate_skill_cache

    invalidate_skill_cache()
    metadata = ChatSkillRegistry.set_enabled({}, "technical-description-delpi", False)

    assert ChatSkillRegistry.is_enabled(metadata, "technical-description-delpi") is False

    resolved = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata=metadata,
        allowed_action_ids=[],
        has_agent=True,
        default_company_knowledge=True,
    )

    assert resolved["technicalDescription"] is False


def test_set_and_read_sql_skill_enabled():
    metadata = ChatSkillRegistry.set_enabled({}, "sql", True)

    assert ChatSkillRegistry.is_enabled(metadata, "sql") is True

    metadata = ChatSkillRegistry.set_enabled(metadata, "sql", False)

    assert ChatSkillRegistry.is_enabled(metadata, "sql") is False


def test_agent_binding_without_explicit_config_is_disabled():
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=True,
    )

    sql = next(item for item in bindings if item["skillKey"] == "sql")

    assert sql["enabled"] is False


def test_common_chat_uses_default_sql_authoring():
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=False,
        default_sql_authoring=True,
    )

    sql = next(item for item in bindings if item["skillKey"] == "sql")

    assert sql["enabled"] is True


def test_common_chat_uses_default_company_knowledge():
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={},
        allowed_action_ids=[],
        has_agent=False,
        default_company_knowledge=True,
    )

    company = next(item for item in bindings if item["skillKey"] == "company-knowledge")

    assert company["enabled"] is True


def test_resolve_runtime_flags_includes_company_knowledge():
    resolved = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={"skills": {"company-knowledge": {"enabled": True}}},
        allowed_action_ids=[],
        has_agent=True,
    )

    assert resolved["companyKnowledge"] is True


def test_drawing_skill_default_when_analyser_action_allowed():
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={},
        allowed_action_ids=["get_product_analyser"],
        has_agent=True,
    )

    drawing = next(
        item for item in bindings if item["skillKey"] == "drawing-analysis-delpi"
    )

    assert drawing["enabled"] is True

    resolved = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={},
        allowed_action_ids=["get_product_analyser"],
        has_agent=True,
    )

    assert resolved["drawingAnalysis"] is True


def test_drawing_skill_on_with_api_externa_analyser_action_id():
    resolved = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={},
        allowed_action_ids=["api_externa.products.get_product_analyser"],
        has_agent=True,
    )

    assert resolved["drawingAnalysis"] is True


def test_drawing_skill_off_when_agent_explicitly_disabled():
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={
            "skills": {"drawing-analysis-delpi": {"engineering": False}},
        },
        allowed_action_ids=["get_product_analyser"],
        has_agent=True,
    )

    drawing = next(
        item for item in bindings if item["skillKey"] == "drawing-analysis-delpi"
    )

    assert drawing["enabled"] is False


def test_quality_action_plans_skill_default_when_pac_action_allowed():
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={},
        allowed_action_ids=["list_quality_action_plans"],
        has_agent=True,
    )

    pac = next(
        item for item in bindings if item["skillKey"] == "quality-action-plans-delpi"
    )

    assert pac["enabled"] is True

    resolved = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={},
        allowed_action_ids=["list_quality_action_plans"],
        has_agent=True,
    )

    assert resolved["qualityActionPlans"] is True


def test_quality_action_plans_skill_off_when_agent_explicitly_disabled():
    bindings = ChatSkillRegistry.list_agent_bindings(
        agent_metadata={
            "skills": {"quality-action-plans-delpi": {"enabled": False}},
        },
        allowed_action_ids=["list_quality_action_plans"],
        has_agent=True,
    )

    pac = next(
        item for item in bindings if item["skillKey"] == "quality-action-plans-delpi"
    )

    assert pac["enabled"] is False
