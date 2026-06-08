"""Rotas HTTP do chat — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403

@chat_bp.post("/sessions")
@require_permission(CHAT_ACCESS_PERMISSION)
def create_session():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_create_chat_session_use_case()

    try:
        result = use_case.execute(
            CreateChatSessionRequest(
                user_id=g.current_user.sub,
                title=payload.get("title"),
                context=payload.get("context"),
                project_id=payload.get("projectId") or payload.get("project_id"),
                agent_id=payload.get("agentId") or payload.get("agent_id"),
                fork_from_session_id=(
                    payload.get("forkFromSessionId") or payload.get("fork_from_session_id")
                ),
                fork_until_message_id=(
                    payload.get("forkUntilMessageId") or payload.get("fork_until_message_id")
                ),
                fork_resend_user_message=bool(
                    payload.get("forkResendUserMessage")
                    or payload.get("fork_resend_user_message")
                ),
            )
        )

        db.session.commit()
    except (ChatMessageNotFoundError, ChatSessionNotFoundError, ChatSessionAccessDeniedError):
        db.session.rollback()
        return _not_found_response()
    except (ValueError, InvalidChatSessionInputError) as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    response_data = asdict(result)
    response_data["privacy_notice"] = _PRIVACY_NOTICE
    return jsonify(response_data), 201


@chat_bp.get("/sessions")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_sessions():
    archived = request.args.get("archived", "false").lower() == "true"

    use_case = make_list_chat_sessions_use_case()
    result = use_case.execute(
        g.current_user.sub,
        archived=archived,
    )

    return jsonify([asdict(session) for session in result]), 200




@chat_bp.patch("/sessions/<session_id>")
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
def rename_session(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_rename_chat_session_use_case()

    try:
        session = use_case.execute(
            RenameChatSessionRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
                title=payload.get("title", ""),
            )
        )

        if not session:
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

    return jsonify(asdict(session)), 200




@chat_bp.delete("/sessions/<session_id>")
@require_permission(CHAT_ACCESS_PERMISSION)
def delete_session(session_id: str):
    use_case = make_delete_chat_session_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            session_id=session_id,
        )

        if not deleted:
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

    except Exception:
        db.session.rollback()
        raise

    return "", 204


@chat_bp.patch("/sessions/<session_id>/pin")
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
def pin_session(session_id: str):
    use_case = make_set_chat_session_pinned_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            pinned=True,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.patch("/sessions/<session_id>/unpin")
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
def unpin_session(session_id: str):
    use_case = make_set_chat_session_pinned_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            pinned=False,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.patch("/sessions/<session_id>/archive")
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
def archive_session(session_id: str):
    use_case = make_set_chat_session_archived_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            archived=True,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.patch("/sessions/<session_id>/unarchive")
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
def unarchive_session(session_id: str):
    use_case = make_set_chat_session_archived_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            archived=False,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.post("/sessions/<session_id>/memory/clear")
@require_permission(CHAT_ASK_PERMISSION)
def clear_session_memory(session_id: str):
    use_case = make_clear_chat_session_memory_use_case()

    try:
        cleared = use_case.execute(
            user_id=UUID(str(g.current_user.sub)),
            session_id=UUID(str(session_id)),
        )
        db.session.commit()
    except ChatSessionNotFoundError:
        db.session.rollback()
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        db.session.rollback()
        return jsonify({"error": "forbidden"}), 403
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"cleared": cleared}), 200


@chat_bp.get("/sessions/<session_id>/memory/context")
@require_permission(CHAT_ASK_PERMISSION)
def get_session_memory_context(session_id: str):
    from uuid import UUID

    use_case = make_chat_session_memory_pins_use_case()

    try:
        result = use_case.get_context(
            user_id=UUID(str(g.current_user.sub)),
            session_id=UUID(str(session_id)),
        )
    except ChatSessionNotFoundError:
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        return jsonify({"error": "forbidden"}), 403
    except Exception:
        raise

    return jsonify(result), 200


@chat_bp.post("/sessions/<session_id>/memory/pins")
@require_permission(CHAT_ASK_PERMISSION)
def add_session_memory_pin(session_id: str):
    from uuid import UUID

    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    kind = payload.get("kind")
    value = payload.get("value")

    if not kind or not value:
        return bad_request("kind and value are required")

    use_case = make_chat_session_memory_pins_use_case()

    try:
        result = use_case.add_pin(
            user_id=UUID(str(g.current_user.sub)),
            session_id=UUID(str(session_id)),
            kind=str(kind),
            value=str(value),
        )
        db.session.commit()
    except ChatSessionNotFoundError:
        db.session.rollback()
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        db.session.rollback()
        return jsonify({"error": "forbidden"}), 403
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@chat_bp.post("/sessions/<session_id>/memory/context-items")
@require_permission(CHAT_ASK_PERMISSION)
def add_session_memory_context_item(session_id: str):
    from uuid import UUID

    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    content = payload.get("content")
    filename = payload.get("filename")
    role = payload.get("role")
    kind = payload.get("kind")
    message_id = payload.get("messageId") or payload.get("message_id")
    question = payload.get("question")
    answer = payload.get("answer")
    question_message_id = payload.get("questionMessageId") or payload.get(
        "question_message_id"
    )
    answer_message_id = payload.get("answerMessageId") or payload.get("answer_message_id")

    has_turn = bool(str(question or "").strip()) and bool(str(answer or "").strip())
    has_content = content is not None and str(content).strip()
    has_file = bool(str(filename or "").strip())

    if not has_turn and not has_content and not has_file:
        return bad_request("content, filename or question+answer is required")

    use_case = make_chat_session_memory_pins_use_case()

    try:
        result = use_case.add_context_item(
            user_id=UUID(str(g.current_user.sub)),
            session_id=UUID(str(session_id)),
            content=str(content or ""),
            filename=str(filename).strip() if filename else None,
            role=str(role).strip().lower() if role else None,
            kind=str(kind).strip().lower() if kind else None,
            message_id=str(message_id).strip() if message_id else None,
            question=str(question) if question is not None else None,
            answer=str(answer) if answer is not None else None,
            question_message_id=str(question_message_id).strip()
            if question_message_id
            else None,
            answer_message_id=str(answer_message_id).strip()
            if answer_message_id
            else None,
        )
        db.session.commit()
    except ChatSessionNotFoundError:
        db.session.rollback()
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        db.session.rollback()
        return jsonify({"error": "forbidden"}), 403
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@chat_bp.delete("/sessions/<session_id>/memory/context-items/<item_id>")
@require_permission(CHAT_ASK_PERMISSION)
def remove_session_memory_context_item(session_id: str, item_id: str):
    from uuid import UUID

    use_case = make_chat_session_memory_pins_use_case()

    try:
        result = use_case.remove_context_item(
            user_id=UUID(str(g.current_user.sub)),
            session_id=UUID(str(session_id)),
            item_id=str(item_id),
        )
        db.session.commit()
    except ChatSessionNotFoundError:
        db.session.rollback()
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        db.session.rollback()
        return jsonify({"error": "forbidden"}), 403
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@chat_bp.put("/sessions/<session_id>/memory/response-format")
@require_permission(CHAT_ASK_PERMISSION)
def set_session_response_format(session_id: str):
    from uuid import UUID

    payload = request.get_json(silent=True) or {}
    response_format = payload.get("responseFormat") or payload.get("response_format")

    if not response_format:
        return bad_request("responseFormat is required")

    use_case = make_chat_session_memory_pins_use_case()

    try:
        result = use_case.set_response_format(
            user_id=UUID(str(g.current_user.sub)),
            session_id=UUID(str(session_id)),
            response_format=str(response_format),
        )
        db.session.commit()
    except ChatSessionNotFoundError:
        db.session.rollback()
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        db.session.rollback()
        return jsonify({"error": "forbidden"}), 403
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@chat_bp.delete("/sessions/<session_id>/memory/pins/<kind>")
@require_permission(CHAT_ASK_PERMISSION)
def remove_session_memory_pin(session_id: str, kind: str):
    from uuid import UUID

    use_case = make_chat_session_memory_pins_use_case()

    try:
        result = use_case.remove_pin(
            user_id=UUID(str(g.current_user.sub)),
            session_id=UUID(str(session_id)),
            kind=str(kind),
        )
        db.session.commit()
    except ChatSessionNotFoundError:
        db.session.rollback()
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        db.session.rollback()
        return jsonify({"error": "forbidden"}), 403
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200

