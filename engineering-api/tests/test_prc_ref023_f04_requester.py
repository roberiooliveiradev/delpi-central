"""PRC-REF-023-F04 — solicitante de Minhas Solicitações no mesmo caso PRC.

Prova que um usuário comum (``my-requests.access`` +
``my-requests.raw-material-creation.create``, sem ``engineering.access``)
cria, acompanha, anexa, corrige e reenvia o próprio caso — enquanto
terceiros ficam negados e as operações de atendimento continuam
exclusivas de ``engineering.access``.
"""

from __future__ import annotations

import io

import pytest

from tests.conftest import rbac_payload
from tests.test_d16_attendance_flags import _patch
from tests.test_prc_ref022_correction_returns import (
    ANALYST_SUB,
    _as,
    _base,
    _return_targets,
)
from tests.test_product_registration import (  # noqa: F401
    ANALYST,
    _create_body,
    _post,
    _token,
    prc_service_repo,
)

MR_REQUESTER = [
    "my-requests.access",
    "my-requests.raw-material-creation.create",
]
MR_ACCESS_ONLY = ["my-requests.access"]

REQUESTER_SUB = "user-1"
OTHER_SUB = "other-user"


def _as_requester(jwks_env, core_rbac, sub: str) -> str:
    core_rbac["behavior"] = ("data", rbac_payload(MR_REQUESTER, id=sub))
    return _token(jwks_env, sub)


def _get(client, url, token):
    return client.get(url, headers={"Authorization": f"Bearer {token}"})


def _requester_create(client, jwks_env, core_rbac, sub=REQUESTER_SUB):
    tok = _as_requester(jwks_env, core_rbac, sub)
    body = _create_body(source="my-requests")
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        tok,
        json=body,
        headers={"Idempotency-Key": f"k-{sub}-1"},
    )
    return resp


def _case_version(client, tok, rid) -> int:
    resp = _get(client, _base(rid), tok)
    assert resp.status_code == 200, resp.text
    return int(resp.json()["data"]["caseVersion"])


def _start_attendance(client, jwks_env, core_rbac, rid):
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    version = _case_version(client, tok, rid)
    resp = _post(
        client,
        f"{_base(rid)}/actions/start",
        tok,
        json={"expectedVersion": version},
    )
    assert resp.status_code == 200, resp.text
    return tok


class TestRequesterIntake:
    def test_requester_creates_without_engineering_access(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        resp = _requester_create(client, jwks_env, core_rbac)
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()["data"]
        assert data["requestId"]
        assert data["caseStatus"] == "submitted"
        detail = _get(
            client, _base(data["requestId"]),
            _as_requester(jwks_env, core_rbac, REQUESTER_SUB),
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["data"]["requester"]["subject"] == REQUESTER_SUB

    def test_my_requests_access_only_cannot_create(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        core_rbac["behavior"] = (
            "data",
            rbac_payload(MR_ACCESS_ONLY, id="viewer-1"),
        )
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env, "viewer-1"),
            json=_create_body(source="my-requests"),
        )
        assert resp.status_code == 403, resp.text

    def test_requester_source_my_requests_accepted(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        resp = _requester_create(client, jwks_env, core_rbac)
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["data"]["source"] == "my-requests"

    def test_unknown_source_still_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        tok = _as_requester(jwks_env, core_rbac, REQUESTER_SUB)
        resp = _post(
            client,
            "/v1/product-registration/intake/requests",
            tok,
            json=_create_body(source="unknown-front"),
        )
        assert resp.status_code == 403, resp.text


class TestRequesterScope:
    def test_requester_lists_only_own_cases(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _requester_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        own = _as_requester(jwks_env, core_rbac, REQUESTER_SUB)
        resp = _get(client, "/v1/product-registration/requests", own)
        assert resp.status_code == 200, resp.text
        ids = [i["id"] for i in resp.json()["data"]["items"]]
        assert rid in ids

        other = _as_requester(jwks_env, core_rbac, OTHER_SUB)
        resp = _get(client, "/v1/product-registration/requests", other)
        assert resp.status_code == 200, resp.text
        ids = [i["id"] for i in resp.json()["data"]["items"]]
        assert rid not in ids

    def test_analyst_sees_requester_case_in_queue(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _requester_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        tok = _as(jwks_env, core_rbac, ANALYST_SUB)
        resp = _get(client, "/v1/product-registration/requests", tok)
        assert resp.status_code == 200, resp.text
        ids = [i["id"] for i in resp.json()["data"]["items"]]
        assert rid in ids

    def test_third_requester_denied_detail_and_attachment(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _requester_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        other = _as_requester(jwks_env, core_rbac, OTHER_SUB)
        for url in (
            _base(rid),
            f"{_base(rid)}/timeline",
            f"{_base(rid)}/attachments",
            f"{_base(rid)}/correction-returns",
        ):
            resp = _get(client, url, other)
            assert resp.status_code == 403, (url, resp.text)

    def test_requester_cannot_process_attendance(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _requester_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        own = _as_requester(jwks_env, core_rbac, REQUESTER_SUB)
        version = _case_version(client, own, rid)
        bodies = {
            "start": {"expectedVersion": version},
            "reject": {
                "expectedVersion": version,
                "reason": "Tentativa indevida de rejeição.",
            },
            "return-for-correction": {
                "expectedVersion": version,
                "targets": _return_targets("unit"),
            },
        }
        for action, body in bodies.items():
            resp = _post(
                client,
                f"{_base(rid)}/actions/{action}",
                own,
                json=body,
            )
            assert resp.status_code == 403, (action, resp.text)


class TestRequesterCorrection:
    def test_requester_correction_roundtrip(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _requester_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        analyst = _start_attendance(client, jwks_env, core_rbac, rid)
        version = _case_version(client, analyst, rid)
        resp = _post(
            client,
            f"{_base(rid)}/actions/return-for-correction",
            analyst,
            json={
                "expectedVersion": version,
                "targets": _return_targets("unit"),
            },
            headers={"Idempotency-Key": f"ret-{rid}-1"},
        )
        assert resp.status_code == 200, resp.text
        version = int(resp.json()["data"]["caseVersion"])

        requester = _as_requester(jwks_env, core_rbac, REQUESTER_SUB)
        detail = _get(client, _base(rid), requester).json()["data"]
        assert detail["status"] == "needs_correction"
        assert "save_returned_fields" in detail["allowedActions"]
        assert "resubmit_correction" in detail["allowedActions"]
        assert detail["correctionExchange"]["canCorrect"] is True
        assert (
            detail["correctionExchange"]["requesterAuthz"]["status"]
            == "object_scoped"
        )

        resp = _patch(
            client,
            f"{_base(rid)}/returned-fields",
            requester,
            json={
                "expectedVersion": version,
                "changes": [
                    {
                        "path": "unit",
                        "proposedValue": "KG",
                        "reason": "Unidade correta é KG.",
                        "mode": "changed",
                    }
                ],
            },
            headers={"Idempotency-Key": f"save-{rid}-1"},
        )
        assert resp.status_code == 200, resp.text
        version = int(resp.json()["data"]["caseVersion"])

        resp = _post(
            client,
            f"{_base(rid)}/actions/resubmit-correction",
            requester,
            json={"expectedVersion": version},
            headers={"Idempotency-Key": f"resub-{rid}-1"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == "in_progress"
        assert resp.json()["data"]["id"] == rid

    def test_other_requester_cannot_correct(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _requester_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        analyst = _start_attendance(client, jwks_env, core_rbac, rid)
        version = _case_version(client, analyst, rid)
        resp = _post(
            client,
            f"{_base(rid)}/actions/return-for-correction",
            analyst,
            json={
                "expectedVersion": version,
                "targets": _return_targets("unit"),
            },
        )
        assert resp.status_code == 200, resp.text
        version = int(resp.json()["data"]["caseVersion"])

        other = _as_requester(jwks_env, core_rbac, OTHER_SUB)
        resp = _patch(
            client,
            f"{_base(rid)}/returned-fields",
            other,
            json={
                "expectedVersion": version,
                "changes": [
                    {
                        "path": "unit",
                        "proposedValue": "KG",
                        "reason": "Tentativa indevida.",
                        "mode": "changed",
                    }
                ],
            },
        )
        assert resp.status_code == 403, resp.text


class TestRequesterAttachments:
    def test_requester_upload_download_and_isolation(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _requester_create(client, jwks_env, core_rbac).json()["data"][
            "requestId"
        ]
        requester = _as_requester(jwks_env, core_rbac, REQUESTER_SUB)
        pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        resp = client.post(
            f"{_base(rid)}/attachments",
            headers={"Authorization": f"Bearer {requester}"},
            files={
                "file": ("spec.pdf", io.BytesIO(pdf), "application/pdf")
            },
        )
        assert resp.status_code in (200, 201), resp.text
        att_id = resp.json()["data"]["attachment"]["attachmentId"]

        resp = _get(
            client,
            f"{_base(rid)}/attachments/{att_id}/download",
            requester,
        )
        assert resp.status_code == 200, resp.text
        assert resp.content == pdf

        other = _as_requester(jwks_env, core_rbac, OTHER_SUB)
        for url in (
            f"{_base(rid)}/attachments",
            f"{_base(rid)}/attachments/{att_id}/download",
        ):
            resp = _get(client, url, other)
            assert resp.status_code == 403, (url, resp.text)

        analyst = _as(jwks_env, core_rbac, ANALYST_SUB)
        resp = _get(client, f"{_base(rid)}/attachments", analyst)
        assert resp.status_code == 200, resp.text


class TestRequesterReadInputs:
    def test_requester_reads_reference_data(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        tok = _as_requester(jwks_env, core_rbac, REQUESTER_SUB)
        resp = _get(
            client, "/v1/product-registration/reference-data", tok
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "my-requests" in data["sources"]
