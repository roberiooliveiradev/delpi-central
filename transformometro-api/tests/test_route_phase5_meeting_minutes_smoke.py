"""Smokes Nível A — fase 5: atas, convites públicos e perfil de assinatura.

operationIds literais abaixo alimentam audit_route_test_coverage.
"""

from __future__ import annotations

import pytest

from tests.support.route_smoke_runner import run_route_smoke

OPERATION_IDS = (
    "cancel_meeting_minute",
    "create_meeting_minute",
    "create_meeting_minute_version",
    "delete_meeting_minute",
    "export_meeting_minute_pdf",
    "finalize_meeting_minute",
    "generate_meeting_minute_from_transcript",
    "get_meeting_minute",
    "get_meeting_minute_audit",
    "get_meeting_minute_sign_context",
    "get_meeting_minute_signature_image",
    "get_my_signature_image",
    "get_my_signature_profile",
    "get_public_meeting_minute_sign_invite",
    "list_meeting_minutes",
    "list_meeting_minutes_pending_signatures",
    "refuse_meeting_minute_signature",
    "refuse_public_meeting_minute_invite",
    "replace_meeting_minute_participants",
    "replace_meeting_minute_signers",
    "send_meeting_minute_for_signature",
    "sign_meeting_minute",
    "sign_public_meeting_minute_invite",
    "update_meeting_minute",
    "update_my_signature_profile",
    "upload_my_signature_image",
)


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_route_nivel_a_smoke(operation_id, tm_client, openapi_ops):
    meta = openapi_ops[operation_id]
    run_route_smoke(tm_client, meta)
