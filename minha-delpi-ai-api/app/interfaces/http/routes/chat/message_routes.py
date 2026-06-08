"""Rotas HTTP do chat — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403

@chat_bp.patch("/messages/<message_id>")
@require_permission(CHAT_ASK_PERMISSION)
def update_message(message_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_update_chat_message_use_case()

    try:
        message = use_case.execute(
            UpdateChatMessageRequest(
                user_id=g.current_user.sub,
                message_id=message_id,
                content=payload.get("content", ""),
            )
        )

        if not message:
            db.session.rollback()
            return jsonify(
                {
                    "errors": [
                        {
                            "code": "not_found",
                            "message": "Resource not found",
                            "path": "_global",
                        }
                    ]
                }
            ), 404

        db.session.commit()

    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(message)), 200


@chat_bp.get("/sessions/<session_id>/messages")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_history(session_id: str):
    use_case = make_get_chat_history_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        session_id=session_id,
    )

    allow_admin_debug = _can_use_admin_debug()
    payload = []

    for message in result:
        item = asdict(message)
        if not allow_admin_debug:
            metadata = item.get("metadata")
            if isinstance(metadata, dict) and metadata.get("adminDebug") is not None:
                metadata = dict(metadata)
                metadata.pop("adminDebug", None)
                item["metadata"] = metadata
        payload.append(item)

    return jsonify(payload), 200


@chat_bp.patch("/sessions/<session_id>/active-branch")
@require_permission(CHAT_ASK_PERMISSION)
def switch_active_branch(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    anchor_user_message_id = payload.get("anchorUserMessageId") or payload.get(
        "anchor_user_message_id"
    )

    if not anchor_user_message_id:
        return bad_request("anchorUserMessageId is required")

    use_case = make_switch_chat_branch_use_case()

    try:
        result = use_case.execute(
            SwitchChatBranchRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
                anchor_user_message_id=str(anchor_user_message_id),
            )
        )
        db.session.commit()
    except (ChatMessageNotFoundError, ChatSessionNotFoundError, ChatSessionAccessDeniedError):
        db.session.rollback()
        return _not_found_response()
    except Exception:
        db.session.rollback()
        raise

    allow_admin_debug = _can_use_admin_debug()
    response_payload = []

    for message in result:
        item = asdict(message)
        if not allow_admin_debug:
            metadata = item.get("metadata")
            if isinstance(metadata, dict) and metadata.get("adminDebug") is not None:
                metadata = dict(metadata)
                metadata.pop("adminDebug", None)
                item["metadata"] = metadata
        response_payload.append(item)

    return jsonify(response_payload), 200


@chat_bp.put("/sessions/<session_id>/messages/<message_id>/feedback")
@require_permission(CHAT_ASK_PERMISSION)
@rate_limit("chat_messages", Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)
def upsert_message_feedback(session_id: str, message_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    rating_raw = payload.get("rating")
    reason_raw = payload.get("reason")
    comment_raw = payload.get("comment")

    rating = None

    if rating_raw is not None:
        try:
            rating = int(rating_raw)
        except (TypeError, ValueError):
            return bad_request("rating must be -1, 1 or null")

    use_case = make_upsert_chat_message_feedback_use_case()

    try:
        reason_value = str(reason_raw).strip() if reason_raw is not None else None
        comment_value = str(comment_raw).strip() if comment_raw is not None else None

        result = use_case.execute(
            user_id=g.current_user.sub,
            session_id=session_id,
            message_id=message_id,
            rating=rating,
            reason=reason_value,
            comment=comment_value,
        )

        if rating in (-1, 1):
            audit_metadata = (result or {}).get("auditMetadata") or {}

            if audit_metadata:
                make_audit_repository().log(
                    user_id=UUID(str(g.current_user.sub)),
                    action="chat.feedback.submitted",
                    metadata=audit_metadata,
                )

            if rating == -1 and reason_value:
                from app.domain.services.chat_web_search_admin_metrics_service import (
                    ChatWebSearchAdminMetricsService,
                )

                if ChatWebSearchAdminMetricsService.is_web_feedback_reason(reason_value):
                    make_audit_repository().log(
                        user_id=UUID(str(g.current_user.sub)),
                        action="chat.feedback.web",
                        metadata=ChatWebSearchAdminMetricsService.feedback_audit_metadata(
                            message_id=message_id,
                            reason=reason_value,
                            rating=rating,
                        ),
                    )

        if isinstance(result, dict):
            result.pop("auditMetadata", None)

        db.session.commit()

        if rating == -1:
            from app.application.use_cases.chat_quality_issues_use_cases import (
                EvaluateFeedbackIssuesUseCase,
            )
            from app.application.use_cases.get_admin_feedback_summary_use_case import (
                GetAdminFeedbackSummaryUseCase,
            )

            feedback_summary = GetAdminFeedbackSummaryUseCase().execute(hours=168)
            created_issues = EvaluateFeedbackIssuesUseCase().execute(
                alerts=feedback_summary.get("alerts"),
                feedback_summary=feedback_summary,
            )

            if created_issues and isinstance(result, dict):
                db.session.commit()
                result["issuesCreated"] = created_issues
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@chat_bp.post("/sessions/<session_id>/messages")
@require_permission(CHAT_ASK_PERMISSION)
@rate_limit("chat_messages", Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)
def send_message(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_send_chat_message_use_case()

    try:
        result = use_case.execute(
            _build_send_chat_message_request(
                session_id=session_id,
                payload=payload,
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.post("/sessions/<session_id>/messages/<message_id>/resend/stream")
@require_permission(CHAT_ASK_PERMISSION)
@rate_limit("chat_messages", Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)
def resend_message_stream(session_id: str, message_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    request_dto = _build_send_chat_message_request(
        session_id=session_id,
        payload=payload,
        resend_from_message_id=message_id,
    )

    return _stream_chat_response(session_id, request_dto)


@chat_bp.post("/sessions/<session_id>/messages/cancel")
@require_permission(CHAT_ASK_PERMISSION)
def cancel_message_stream(session_id: str):
    use_case = make_cancel_chat_stream_use_case()

    try:
        use_case.execute(
            user_id=g.current_user.sub,
            session_id=session_id,
        )
        db.session.commit()
    except (ChatSessionNotFoundError, ChatSessionAccessDeniedError):
        db.session.rollback()
        return _not_found_response()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"cancelled": True}), 200


@chat_bp.post("/sessions/<session_id>/messages/stream")
@require_permission(CHAT_ASK_PERMISSION)
@rate_limit("chat_messages", Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)
def stream_message(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    request_dto = _build_send_chat_message_request(
        session_id=session_id,
        payload=payload,
    )

    return _stream_chat_response(session_id, request_dto)
