"""Helpdesk governed writes — capability plumbing for the canonical
``GovernedWriteOrchestrator`` (R4 — Governed Helpdesk Writes V1).

One closed ``action`` enum, one semantic capability per Helpdesk write
operation — policy stays per-capability in ``confirmation_policy.py``.

PREPARE reads the current ticket through the Helpdesk BFF (same-user
Bearer), seals the exact change plus a current-state fingerprint and the
canonical ``can_*`` projection as *guidance* — never authorization. ACT
re-reads the fingerprint (``PROPOSAL_STALE`` on drift), then executes via
the BFF write port with a proposal-bound ``Idempotency-Key``. VERIFY
re-reads through the BFF and compares the authoritative postcondition —
a 2xx without read-back confirmation is ``OUTCOME_VERIFICATION_FAILED``.

TÉO never calls GLPI directly, never stores ticket truth, never widens
the user's ticket universe with technical credentials.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.governed_writes.errors import (
    OUTCOME_VERIFICATION_FAILED,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.governed_writes.proposal import fingerprint
from tm_app.application.helpdesk.helpdesk_write_port import HelpdeskWriteStack

# Tool/Actions ``action`` argument → orchestrator capability. The transport
# passes a coarse action; the semantic capability (which carries the
# canonical execution_policy) is resolved here — never by transport prose.
HELPDESK_ACTION_TO_CAPABILITY: dict[str, str] = {
    "create_ticket": "helpdesk_create_ticket",
    "set_assignee": "helpdesk_set_assignee",
    "add_followup": "helpdesk_add_followup",
    "create_task": "helpdesk_create_task",
    "add_solution": "helpdesk_add_solution",
    "request_validation": "helpdesk_request_validation",
    "accept_solution": "helpdesk_accept_solution",
    "reject_solution": "helpdesk_reject_solution",
    "submit_satisfaction": "helpdesk_submit_satisfaction",
    "accept_validation": "helpdesk_accept_validation",
    "reject_validation": "helpdesk_reject_validation",
    "delete_ticket": "helpdesk_delete_ticket",
    "unlink_glpi_session": "helpdesk_unlink_glpi_session",
    "upload_attachment": "helpdesk_upload_attachment",
}

HELPDESK_CAPABILITIES = frozenset(HELPDESK_ACTION_TO_CAPABILITY.values())

# Required PREPARE fields per capability (ticket_id is required for every
# ticket-scoped operation — handled separately).
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "helpdesk_create_ticket": (
        "title",
        "description",
        "category_id",
        "urgency_id",
    ),
    "helpdesk_set_assignee": ("user_id",),
    "helpdesk_add_followup": ("content",),
    "helpdesk_create_task": ("content",),
    "helpdesk_add_solution": ("content",),
    "helpdesk_request_validation": ("approver_id",),
    "helpdesk_accept_solution": (),
    "helpdesk_reject_solution": (),
    "helpdesk_submit_satisfaction": ("satisfaction",),
    "helpdesk_accept_validation": ("validation_id",),
    "helpdesk_reject_validation": ("validation_id",),
    "helpdesk_delete_ticket": (),
    "helpdesk_unlink_glpi_session": (),
    "helpdesk_upload_attachment": ("file",),
}

# can_* flag projected by the BFF — early UX/PREPARE guidance only.
# The BFF revalidates at commit; a false flag makes the proposal not-ready,
# it never widens authority.
_CAN_FLAG: dict[str, str] = {
    "helpdesk_set_assignee": "can_assign",
    "helpdesk_add_followup": "can_followup",
    "helpdesk_create_task": "can_create_task",
    "helpdesk_add_solution": "can_create_solution",
    "helpdesk_request_validation": "can_request_approval",
    "helpdesk_accept_solution": "can_accept_solution",
    "helpdesk_reject_solution": "can_reject_solution",
    "helpdesk_submit_satisfaction": "can_submit_satisfaction",
    "helpdesk_accept_validation": "can_decide_validation",
    "helpdesk_reject_validation": "can_decide_validation",
}

_CREATE_TICKET_BODY_KEYS = (
    "title",
    "description",
    "category_id",
    "urgency_id",
    "observer_ids",
    "assignee_id",
)

_CREATE_TASK_BODY_KEYS = (
    "content",
    "state",
    "duration_seconds",
    "category_id",
    "user_tech_id",
    "group_tech_id",
    "planned_begin",
    "planned_end",
)

_REQUEST_VALIDATION_BODY_KEYS = ("approver_type", "approver_id", "content")

# Canonical OpenAI fileParams object — the ChatGPT host binds user uploads
# to fields listed in the tool descriptor ``_meta["openai/fileParams"]``.
# download_url/file_id are required by the host contract; mime_type and
# file_name are optional but declared. Never an arbitrary URL/path.
_FILE_OBJECT_KEYS = ("download_url", "file_id", "mime_type", "file_name")


def _missing_fields(capability: str, args: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in _REQUIRED_FIELDS[capability]:
        value = args.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing


def _file_object_errors(file_arg: Any) -> list[str]:
    """Shape validation for the platform file reference — fail closed on
    anything that is not the canonical fileParams object."""
    if not isinstance(file_arg, dict):
        return ["file"]
    missing = [
        key
        for key in ("download_url", "file_id")
        if not str(file_arg.get(key) or "").strip()
    ]
    return [f"file.{key}" for key in missing]


def _validation_status(ticket: dict[str, Any], validation_id: int) -> int | None:
    for item in ticket.get("validations") or []:
        if int(item.get("id") or -1) == int(validation_id):
            return item.get("status")
    return None


def _ticket_fingerprint(
    ticket: dict[str, Any], *, validation_id: int | None = None
) -> str:
    """Relevant-field fingerprint — enough to catch drift that could
    invalidate the prepared change (§17), nothing more."""
    base: dict[str, Any] = {
        "ticket_id": ticket.get("id"),
        "status_id": ticket.get("status_id"),
        "assigned_user_id": ticket.get("assigned_user_id"),
        "updated_at": ticket.get("updated_at"),
    }
    if validation_id is not None:
        base["validation"] = {
            "id": int(validation_id),
            "status": _validation_status(ticket, int(validation_id)),
        }
    return fingerprint(base)


def _normalize_change(capability: str, args: dict[str, Any]) -> dict[str, Any]:
    """Seal only the fields the BFF contract consumes for this capability."""
    ticket_id = args.get("ticket_id")
    change: dict[str, Any] = {
        "capability": capability,
        "ticket_id": int(ticket_id) if ticket_id is not None else None,
    }
    if capability == "helpdesk_create_ticket":
        change["body"] = {
            key: args.get(key)
            for key in _CREATE_TICKET_BODY_KEYS
            if args.get(key) is not None
        }
    elif capability == "helpdesk_set_assignee":
        change["user_id"] = int(args["user_id"]) if args.get("user_id") is not None else None
    elif capability == "helpdesk_add_followup":
        change["content"] = args.get("content")
        change["request_type_id"] = args.get("request_type_id")
    elif capability == "helpdesk_create_task":
        body = {
            key: args.get(key)
            for key in _CREATE_TASK_BODY_KEYS
            if args.get(key) is not None
        }
        # Transport alias ``task_category_id`` → BFF ``category_id``
        # (avoids ambiguity with the ticket's own category on create_ticket).
        if body.get("category_id") is None and args.get("category_id_task") is not None:
            body["category_id"] = args["category_id_task"]
        change["body"] = body
    elif capability == "helpdesk_add_solution":
        change["content"] = args.get("content")
        change["solution_type_id"] = args.get("solution_type_id")
    elif capability == "helpdesk_request_validation":
        change["body"] = {
            key: args.get(key)
            for key in _REQUEST_VALIDATION_BODY_KEYS
            if args.get(key) is not None
        }
    elif capability in ("helpdesk_accept_solution", "helpdesk_reject_solution"):
        change["content"] = args.get("content") or ""
    elif capability == "helpdesk_submit_satisfaction":
        change["satisfaction"] = (
            int(args["satisfaction"]) if args.get("satisfaction") is not None else None
        )
        change["comment"] = args.get("comment") or ""
    elif capability in (
        "helpdesk_accept_validation",
        "helpdesk_reject_validation",
    ):
        vid = args.get("validation_id")
        change["validation_id"] = int(vid) if vid is not None else None
        change["content"] = args.get("content") or ""
    elif capability == "helpdesk_upload_attachment":
        file_arg = args.get("file")
        change["file"] = (
            {
                key: file_arg.get(key)
                for key in _FILE_OBJECT_KEYS
                if file_arg.get(key) is not None
            }
            if isinstance(file_arg, dict)
            else file_arg
        )
        change["title"] = args.get("title")
    # helpdesk_delete_ticket / helpdesk_unlink_glpi_session seal only the
    # capability (+ ticket_id for delete) — no extra BFF body fields.
    return change


def _expected_postcondition(capability: str, change: dict[str, Any]) -> dict[str, Any]:
    if capability == "helpdesk_delete_ticket":
        return {
            # GLPI trash semantics: the ticket leaves the same-user active
            # view — authoritative read-back is canonical not_found.
            "type": "helpdesk_ticket_deleted",
            "capability": capability,
            "ticket_id": change.get("ticket_id"),
            "expected": {"absent_from_active_view": True},
        }
    if capability == "helpdesk_unlink_glpi_session":
        return {
            "type": "helpdesk_glpi_session",
            "capability": capability,
            "ticket_id": None,
            "expected": {"linked": False},
        }
    if capability == "helpdesk_upload_attachment":
        file_arg = change.get("file") if isinstance(change.get("file"), dict) else {}
        return {
            "type": "helpdesk_ticket_attachment",
            "capability": capability,
            "ticket_id": change.get("ticket_id"),
            "expected": {
                # document_id is only known after the BFF write — VERIFY
                # binds the returned id to the authoritative inventory.
                "attachment_present": True,
                "file_name": file_arg.get("file_name"),
            },
        }
    return {
        "type": "helpdesk_ticket_state",
        "capability": capability,
        "ticket_id": change.get("ticket_id"),
        "expected": {
            key: value
            for key, value in {
                "assigned_user_id": change.get("user_id")
                if capability == "helpdesk_set_assignee"
                else None,
                "satisfaction": change.get("satisfaction")
                if capability == "helpdesk_submit_satisfaction"
                else None,
                "validation_status": 3
                if capability == "helpdesk_accept_validation"
                else (4 if capability == "helpdesk_reject_validation" else None),
            }.items()
            if value is not None
        },
    }


def prepare(
    stack: HelpdeskWriteStack,
    authorization: str,
    *,
    capability: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """Pure PREPARE — reads current state, seals the exact change, never writes."""
    missing = _missing_fields(capability, args)
    change = _normalize_change(capability, args)
    checks: list[str] = []
    blocked: list[str] = []
    confirmation_req: dict[str, Any] = {}
    resource_type = "helpdesk_ticket"
    if capability != "helpdesk_upload_attachment" and args.get("file") is not None:
        blocked.append("file_not_applicable")

    if capability == "helpdesk_create_ticket":
        checks.append("create_intent")
        current_fp = fingerprint(
            {"resource": "helpdesk_ticket", "exists": False}
        )
        resource_id = None
    elif capability == "helpdesk_unlink_glpi_session":
        checks.append("session_state_read")
        resource_type = "helpdesk_glpi_session"
        # Same-user session read — the BFF owns OAuth session truth.
        session = stack.read.session(authorization)
        linked = bool(session.get("linked"))
        if not linked:
            blocked.append("session_not_linked")
        current_fp = fingerprint(
            {"resource": "helpdesk_glpi_session", "linked": linked}
        )
        resource_id = None
        confirmation_req["display"] = {
            "operation": "unlink_glpi_session",
            "linked": linked,
            "effect": "session_unlinked_relink_is_browser_flow",
        }
    else:
        ticket_id = change.get("ticket_id")
        if ticket_id is None or int(ticket_id or 0) <= 0:
            missing.append("ticket_id")
            current_fp = fingerprint({"ticket_id": None})
            resource_id = None
        else:
            checks.append("current_state_read")
            # The read itself enforces same-user OAuth ACL/link at the BFF.
            ticket = stack.read.ticket(authorization, int(ticket_id))
            checks.append("can_flag_probe")
            flag = _CAN_FLAG.get(capability)
            if flag and not ticket.get(flag):
                blocked.append(flag)
            if capability in (
                "helpdesk_accept_validation",
                "helpdesk_reject_validation",
            ):
                vid = change.get("validation_id")
                entry = None
                for item in ticket.get("validations") or []:
                    if int(item.get("id") or -1) == int(vid or -1):
                        entry = item
                        break
                if entry is None:
                    blocked.append("validation_not_found")
                elif not entry.get("mine_to_decide"):
                    blocked.append("validation_not_mine_to_decide")
            current_fp = _ticket_fingerprint(
                ticket, validation_id=change.get("validation_id")
            )
            resource_id = str(ticket_id)
            if capability == "helpdesk_upload_attachment":
                checks.append("file_reference_validated")
                for field in _file_object_errors(args.get("file")):
                    blocked.append(f"invalid_{field}")
                file_arg = (
                    change.get("file")
                    if isinstance(change.get("file"), dict)
                    else {}
                )
                confirmation_req["display"] = {
                    "operation": "upload_attachment",
                    "ticket_id": int(ticket_id),
                    "title": ticket.get("title"),
                    "file_name": file_arg.get("file_name"),
                    "mime_type": file_arg.get("mime_type"),
                }
            if capability == "helpdesk_delete_ticket":
                # Exact delete preview for the confirmation prompt — the
                # user must see id + title + status, never a vague ask.
                confirmation_req["display"] = {
                    "ticket_id": int(ticket_id),
                    "title": ticket.get("title"),
                    "status": ticket.get("status"),
                    "assigned_display_name": ticket.get(
                        "assigned_display_name"
                    ),
                    # GLPI move-to-trash — never framed as permanent purge.
                    "delete_semantics": "trash",
                }

    ready = not missing and not blocked
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "current_state_fingerprint": current_fp,
        "exact_change": change,
        "validation_result": {
            "ready": ready,
            "missing": missing,
            "blocked": blocked,
            "checks": checks,
        },
        "consequential_impact": {
            "persists": True,
            "operation": capability,
        },
        "confirmation_requirement": confirmation_req,
        "expected_postcondition": _expected_postcondition(capability, change),
    }


def recompute_fingerprint(
    stack: HelpdeskWriteStack, authorization: str, change: dict[str, Any]
) -> str:
    capability = str(change.get("capability") or "")
    if capability == "helpdesk_create_ticket":
        return fingerprint({"resource": "helpdesk_ticket", "exists": False})
    if capability == "helpdesk_unlink_glpi_session":
        session = stack.read.session(authorization)
        return fingerprint(
            {
                "resource": "helpdesk_glpi_session",
                "linked": bool(session.get("linked")),
            }
        )
    ticket_id = change.get("ticket_id")
    if ticket_id is None:
        return fingerprint({"ticket_id": None})
    ticket = stack.read.ticket(authorization, int(ticket_id))
    return _ticket_fingerprint(ticket, validation_id=change.get("validation_id"))


def _idempotency_key(proposal) -> str:
    """Proposal-bound deterministic key — same proposal + same retry
    reaches the BFF under the same Idempotency-Key."""
    return f"teo-{proposal.proposal_id}"


def execute(
    stack: HelpdeskWriteStack, authorization: str, proposal
) -> dict[str, Any]:
    """ACT on the sealed change — the only path that calls the BFF write."""
    change = proposal.exact_change
    capability = proposal.capability
    ticket_id = change.get("ticket_id")
    key = _idempotency_key(proposal)
    w = stack.write

    if capability == "helpdesk_create_ticket":
        return w.create_ticket(authorization, dict(change.get("body") or {}), idempotency_key=key)
    if capability == "helpdesk_set_assignee":
        return w.set_assignee(
            authorization,
            int(ticket_id),
            user_id=int(change["user_id"]),
            idempotency_key=key,
        )
    if capability == "helpdesk_add_followup":
        return w.add_followup(
            authorization,
            int(ticket_id),
            content=str(change["content"]),
            request_type_id=change.get("request_type_id"),
            idempotency_key=key,
        )
    if capability == "helpdesk_create_task":
        return w.create_task(
            authorization,
            int(ticket_id),
            dict(change.get("body") or {}),
            idempotency_key=key,
        )
    if capability == "helpdesk_add_solution":
        return w.add_solution(
            authorization,
            int(ticket_id),
            content=str(change["content"]),
            solution_type_id=change.get("solution_type_id"),
            idempotency_key=key,
        )
    if capability == "helpdesk_request_validation":
        return w.request_validation(
            authorization,
            int(ticket_id),
            dict(change.get("body") or {}),
            idempotency_key=key,
        )
    if capability == "helpdesk_accept_solution":
        return w.decide_solution(
            authorization,
            int(ticket_id),
            decision="accept",
            content=str(change.get("content") or ""),
            idempotency_key=key,
        )
    if capability == "helpdesk_reject_solution":
        return w.decide_solution(
            authorization,
            int(ticket_id),
            decision="reject",
            content=str(change.get("content") or ""),
            idempotency_key=key,
        )
    if capability == "helpdesk_submit_satisfaction":
        return w.submit_satisfaction(
            authorization,
            int(ticket_id),
            satisfaction=int(change["satisfaction"]),
            comment=str(change.get("comment") or ""),
            idempotency_key=key,
        )
    if capability in ("helpdesk_accept_validation", "helpdesk_reject_validation"):
        return w.decide_validation(
            authorization,
            int(ticket_id),
            int(change["validation_id"]),
            decision=(
                "accept" if capability == "helpdesk_accept_validation" else "reject"
            ),
            content=str(change.get("content") or ""),
            idempotency_key=key,
        )
    if capability == "helpdesk_delete_ticket":
        return w.delete_ticket(
            authorization, int(ticket_id), idempotency_key=key
        )
    if capability == "helpdesk_unlink_glpi_session":
        return w.unlink_glpi_session(authorization, idempotency_key=key)
    if capability == "helpdesk_upload_attachment":
        if stack.files is None:
            raise GovernedWriteError(
                "File source not configured.",
                code=VALIDATION,
                status_code=500,
            )
        file_arg = change.get("file") if isinstance(change.get("file"), dict) else {}
        errors = _file_object_errors(file_arg)
        if errors:
            raise GovernedWriteError(
                f"Invalid file reference: {errors}.",
                code=VALIDATION,
                status_code=400,
            )
        fetched = stack.files.fetch(str(file_arg["download_url"]))
        filename = (
            str(file_arg.get("file_name") or "").strip()
            or str(fetched.get("filename") or "").strip()
            or "arquivo"
        )
        mime = (
            str(file_arg.get("mime_type") or "").strip()
            or str(fetched.get("mime") or "").strip()
            or "application/octet-stream"
        )
        return w.upload_attachment(
            authorization,
            int(ticket_id),
            filename=filename,
            content=fetched["content"],
            mime=mime,
            title=change.get("title") or None,
            idempotency_key=key,
        )
    raise GovernedWriteError(
        f"ACT not implemented for '{capability}'.",
        code=VALIDATION,
        status_code=500,
    )


def _timeline_has(ticket: dict[str, Any], entry_id: Any, kind: str) -> bool:
    for entry in ticket.get("timeline") or []:
        if str(entry.get("id")) == str(entry_id):
            return not kind or str(entry.get("kind") or "") == kind
    return False


def _verification_failed(message: str, **data: Any) -> GovernedWriteError:
    return GovernedWriteError(
        message,
        code=OUTCOME_VERIFICATION_FAILED,
        status_code=409,
        data=data or None,
    )


def verify(
    stack: HelpdeskWriteStack,
    authorization: str,
    proposal,
    write_result: Any,
) -> dict[str, Any]:
    """Authoritative read-back — 2xx alone is never success."""
    change = proposal.exact_change
    capability = proposal.capability
    result = dict(write_result or {})

    if capability == "helpdesk_unlink_glpi_session":
        session = stack.read.session(authorization)
        if bool(session.get("linked")):
            raise _verification_failed(
                "GLPI session still linked after unlink.",
                expected=False,
                actual=session.get("linked"),
            )
        return {"session": session, "write_result": result}

    if capability == "helpdesk_delete_ticket":
        ticket_id = int(change["ticket_id"])
        try:
            still_there = stack.read.ticket(authorization, ticket_id)
        except GptActionsError as exc:
            data = exc.data if isinstance(exc.data, dict) else {}
            if exc.status_code == 404 or data.get("error_kind") == "not_found":
                # Canonical postcondition: trash removal means the ticket
                # is absent from the same-user active view.
                return {
                    "deleted": True,
                    "ticket_id": ticket_id,
                    "write_result": result,
                }
            raise
        raise _verification_failed(
            "Ticket still readable after delete — not removed.",
            ticket_id=ticket_id,
            actual_status_id=still_there.get("status_id"),
        )

    if capability == "helpdesk_create_ticket":
        rid = result.get("id")
        if not rid:
            raise _verification_failed(
                "Ticket create returned no id for read-back."
            )
        ticket = stack.read.ticket(authorization, int(rid))
        return {"ticket": ticket, "write_result": result}

    ticket_id = int(change["ticket_id"])
    ticket = stack.read.ticket(authorization, ticket_id)

    if capability == "helpdesk_upload_attachment":
        document_id = result.get("document_id")
        known_ids = {
            int(item.get("document_id"))
            for item in ticket.get("attachments") or []
            if item.get("document_id") is not None
        }
        known_ids.update(
            int(ref.get("document_id"))
            for ref in ticket.get("attachment_refs") or []
            if ref.get("document_id") is not None
        )
        if not document_id or int(document_id) not in known_ids:
            raise _verification_failed(
                "Uploaded attachment not found in authoritative ticket "
                "attachment inventory.",
                expected_document_id=document_id,
            )
        return {"ticket": ticket, "write_result": result}

    if capability == "helpdesk_set_assignee":
        if int(ticket.get("assigned_user_id") or -1) != int(change["user_id"]):
            raise _verification_failed(
                "Assignee change not confirmed by read-back.",
                expected=change["user_id"],
                actual=ticket.get("assigned_user_id"),
            )
        return {"ticket": ticket, "write_result": result}

    if capability == "helpdesk_add_followup":
        rid = result.get("id")
        if not rid or not _timeline_has(ticket, rid, "followup"):
            raise _verification_failed(
                "Follow-up not found in authoritative ticket timeline.",
                expected_id=rid,
            )
        return {"ticket": ticket, "write_result": result}

    if capability == "helpdesk_create_task":
        rid = result.get("id")
        if not rid or not _timeline_has(ticket, rid, "task"):
            raise _verification_failed(
                "Task not found in authoritative ticket timeline.",
                expected_id=rid,
            )
        return {"ticket": ticket, "write_result": result}

    if capability == "helpdesk_add_solution":
        rid = result.get("id")
        if not rid or not _timeline_has(ticket, rid, "solution"):
            raise _verification_failed(
                "Solution not found in authoritative ticket timeline.",
                expected_id=rid,
            )
        return {"ticket": ticket, "write_result": result}

    if capability == "helpdesk_request_validation":
        rid = result.get("id")
        found = any(
            str(item.get("id")) == str(rid)
            for item in ticket.get("validations") or []
        )
        if not rid or not found:
            raise _verification_failed(
                "Validation request not found in authoritative ticket.",
                expected_id=rid,
            )
        return {"ticket": ticket, "write_result": result}

    if capability in ("helpdesk_accept_solution", "helpdesk_reject_solution"):
        expected_status = result.get("status_id")
        if expected_status is None or ticket.get("status_id") != expected_status:
            raise _verification_failed(
                "Solution decision not confirmed by read-back.",
                expected_status_id=expected_status,
                actual_status_id=ticket.get("status_id"),
            )
        return {"ticket": ticket, "write_result": result}

    if capability == "helpdesk_submit_satisfaction":
        if ticket.get("satisfaction") != change["satisfaction"]:
            raise _verification_failed(
                "Satisfaction not confirmed by read-back.",
                expected=change["satisfaction"],
                actual=ticket.get("satisfaction"),
            )
        return {"ticket": ticket, "write_result": result}

    if capability in ("helpdesk_accept_validation", "helpdesk_reject_validation"):
        expected_status = result.get("status")
        actual = _validation_status(ticket, int(change["validation_id"]))
        if expected_status is None or actual != expected_status:
            raise _verification_failed(
                "Validation decision not confirmed by read-back.",
                expected_status=expected_status,
                actual_status=actual,
            )
        return {"ticket": ticket, "write_result": result}

    raise _verification_failed(
        f"Read-back not implemented for '{capability}'."
    )
