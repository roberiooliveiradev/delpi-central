from app.domain.skills.chat_skill_registry import ChatSkillRegistry


def test_catalog_lists_sql_skill():
    catalog = ChatSkillRegistry.list_catalog()

    assert any(item["skillKey"] == "sql" for item in catalog)


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
