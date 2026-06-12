"""Rotas HTTP do chat — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403

@chat_bp.get("/status")
@require_permission(CHAT_ACCESS_PERMISSION)
def status():
    result = GetChatStatusUseCase().execute(g.current_user)
    return jsonify(result), 200


@chat_bp.get("/response-modes")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_response_modes():
    from app.application.use_cases.get_chat_response_modes_use_case import (
        GetChatResponseModesUseCase,
    )

    return jsonify(GetChatResponseModesUseCase().execute()), 200

@chat_bp.get("/action-providers")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_action_providers():
    return jsonify(make_list_external_action_providers_use_case().execute()), 200


@chat_bp.get("/actions")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_actions():
    provider_key = request.args.get("providerKey") or request.args.get("provider_key")
    actions = make_list_external_actions_use_case().execute(provider_key=provider_key)

    return jsonify(actions), 200


@chat_bp.get("/capabilities")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_chat_capabilities():
    return jsonify(_get_chat_capabilities_from_request()), 200


@chat_bp.get("/assistant/catalog")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_assistant_catalog():
    from uuid import UUID

    from app.application.services.chat_assistant_catalog_service import (
        ChatAssistantCatalogService,
    )

    query = (request.args.get("q") or request.args.get("query") or "").strip()
    agent_id = (request.args.get("agentId") or request.args.get("agent_id") or "").strip()
    onboarding_profile_id = (
        request.args.get("profileId")
        or request.args.get("onboardingProfileId")
        or ""
    ).strip()

    try:
        limit = int(request.args.get("limit", 24))
    except (TypeError, ValueError):
        return bad_request("limit must be a number")

    if limit < 1 or limit > 50:
        return bad_request("limit must be between 1 and 50")

    try:
        user_id = UUID(str(g.current_user.sub))
    except ValueError:
        return bad_request("invalid user id")

    capabilities = _get_chat_capabilities_from_request()

    from app.composition.chat_composer import make_chat_intelligence_settings_service
    from app.composition.repository_composer import make_external_action_repository

    payload = ChatAssistantCatalogService(
        agent_repository=make_chat_agent_repository(),
        action_repository=make_external_action_repository(),
        intelligence_settings=make_chat_intelligence_settings_service(),
    ).build_response(
        user_id=user_id,
        query=query or None,
        agent_id=agent_id or None,
        onboarding_profile_id=onboarding_profile_id or None,
        limit=limit,
        user_permissions=set(capabilities.get("permissions") or []),
        is_superadmin=bool(capabilities.get("isSuperadmin")),
        can_use_tools=bool(capabilities.get("canUseTools")),
        can_open_admin=bool(capabilities.get("canOpenAdmin")),
    )

    return jsonify(payload), 200


@chat_bp.get("/assistant/feedback-reasons")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_assistant_feedback_reasons():
    from app.domain.services.chat_feedback_content_service import ChatFeedbackContentService

    return jsonify(ChatFeedbackContentService.public_payload()), 200


@chat_bp.post("/assistant/help-events")
@require_permission(CHAT_ACCESS_PERMISSION)
def record_assistant_help_event():
    from app.application.services.chat_help_adoption_service import ChatHelpAdoptionService
    from app.application.services.chat_interactivity_preference_service import (
        ChatInteractivityPreferenceService,
    )
    from app.composition.chat_composer import make_chat_session_memory_service

    payload = request.get_json(silent=True) or {}
    event = str(payload.get("event") or "").strip()
    metadata = payload.get("metadata")

    if not event:
        return bad_request("event is required")

    safe_meta = metadata if isinstance(metadata, dict) else {}

    try:
        result = ChatHelpAdoptionService.record(
            user_id=str(g.current_user.sub),
            event=event,
            metadata=safe_meta or None,
        )
    except ValueError as exc:
        return bad_request(str(exc))

    if event == "interactivity_suggestion_clicked":
        from app.domain.services.chat_interactivity_admin_metrics_service import (
            ChatInteractivityAdminMetricsService,
        )
        label = str(safe_meta.get("label") or "").strip()
        session_id = safe_meta.get("sessionId") or safe_meta.get("session_id")

        if label and session_id:
            memory_service = make_chat_session_memory_service()

            ChatInteractivityPreferenceService.record_click(
                repository=memory_service.repository,
                session_id=session_id,
                label=label,
            )

        if label:
            click_snapshot = ChatInteractivityAdminMetricsService.snapshot_from_click(safe_meta)

            if click_snapshot:
                make_audit_repository().log(
                    user_id=UUID(str(g.current_user.sub)),
                    action="chat.interactivity.clicked",
                    metadata=click_snapshot,
                )

                if str(click_snapshot.get("group") or "") == "recuperar":
                    make_audit_repository().log(
                        user_id=UUID(str(g.current_user.sub)),
                        action="chat.error_recovery.clicked",
                        metadata=click_snapshot,
                    )

                from app.domain.services.chat_web_search_admin_metrics_service import (
                    ChatWebSearchAdminMetricsService,
                )

                allowed_web_labels = ChatWebSearchAdminMetricsService.web_follow_up_labels()

                if (
                    str(click_snapshot.get("group") or "") == "web_search"
                    or str(click_snapshot.get("label") or "") in allowed_web_labels
                ):
                    make_audit_repository().log(
                        user_id=UUID(str(g.current_user.sub)),
                        action="chat.web_search.follow_up_clicked",
                        metadata=click_snapshot,
                    )

    if event.startswith("presentation_"):
        from app.domain.services.chat_presentation_admin_metrics_service import (
            ChatPresentationAdminMetricsService,
        )

        event_snapshot = ChatPresentationAdminMetricsService.snapshot_from_event(
            event=event,
            metadata=safe_meta,
        )

        if event_snapshot:
            make_audit_repository().log(
                user_id=UUID(str(g.current_user.sub)),
                action="chat.presentation.event",
                metadata=event_snapshot,
            )

    if event.startswith("typing_correction_"):
        from app.domain.services.chat_typing_correction_admin_metrics_service import (
            ChatTypingCorrectionAdminMetricsService,
        )

        event_snapshot = ChatTypingCorrectionAdminMetricsService.snapshot_from_event(
            event=event,
            metadata=safe_meta,
        )

        if event_snapshot:
            make_audit_repository().log(
                user_id=UUID(str(g.current_user.sub)),
                action="chat.typing_correction.event",
                metadata=event_snapshot,
            )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(result), 200


@chat_bp.post("/typing-suggestions")
@require_permission(CHAT_ACCESS_PERMISSION)
def typing_suggestions():
    from app.application.services.chat_learned_normalization_service import (
        ChatLearnedNormalizationService,
    )
    from app.domain.services.chat_typing_correction_service import (
        ChatTypingCorrectionService,
    )
    from app.infrastructure.config.settings import Settings

    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    text = str(payload.get("text") or "")

    from app.application.services.chat_platform_runtime_access import (
        learning_pipeline_settings,
    )

    learning = learning_pipeline_settings()
    if not (
        learning.get("learningEnabled") and learning.get("typingCorrectionEnabled")
    ):
        return jsonify(
            {
                "hasSuggestions": False,
                "corrected": text,
                "original": text,
                "changes": [],
                "protectedSpans": [],
            }
        ), 200

    ChatLearnedNormalizationService().ensure_loaded()

    return jsonify(ChatTypingCorrectionService.suggest(text)), 200
