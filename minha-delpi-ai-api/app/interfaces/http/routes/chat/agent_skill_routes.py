"""Rotas HTTP de skills do agente — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403


@chat_bp.get("/skills")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_skill_catalog():
    use_case = make_list_chat_skill_catalog_use_case()
    return jsonify(use_case.execute()), 200


@chat_bp.get("/agents/<agent_id>/skills")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_agent_skills(agent_id: str):
    use_case = make_list_chat_agent_skills_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
    )

    if result is None:
        return _not_found_response()

    return jsonify(result), 200


@chat_bp.put("/agents/<agent_id>/skills")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def upsert_agent_skill(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    can_manage_agent, capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure skills for this agent")

    skill_key = payload.get("skillKey") or payload.get("skill_key")

    if not skill_key:
        return bad_request("skillKey is required")

    use_case = make_upsert_chat_agent_skill_use_case()

    try:
        saved = use_case.execute(
            UpsertChatAgentSkillRequest(
                user_id=g.current_user.sub,
                agent_id=agent_id,
                skill_key=str(skill_key),
                enabled=bool(payload.get("enabled", True)),
                can_manage_official_agents=capabilities["canManageOfficialAgents"],
            )
        )

        if not saved:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"ok": True}), 200
