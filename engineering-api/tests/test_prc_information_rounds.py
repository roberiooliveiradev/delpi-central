"""PRC-REF-019 — rodadas de esclarecimento: REST + paridade EVA.

Fluxo: analista abre rodada tipada (request-information) → solicitante
rascunha/envia respostas → analista aceita ou pede complemento →
``resume`` só passa sem rodada aberta (ou com ``waiver:``).
"""

from __future__ import annotations

import json

import pytest

from tests.conftest import rbac_payload
from tests.test_prc_eva_parity import _ctx, _entry
from tests.test_product_registration import (  # noqa: F401
    ANALYST,
    _post,
    _submit_create,
    _token,
    prc_service_repo,
)
from tests.test_d16_attendance_flags import _patch

from engineering_app.interface.mcp import prc_semantic
from engineering_app.interface.mcp.semantic_bridge import (
    _EXECUTE_DISPATCH,
    _READ_DISPATCH,
)

REQUESTER_SUB = "user-1"
ANALYST_SUB = "analyst-1"


def _base(rid: str) -> str:
    return f"/v1/product-registration/requests/{rid}"


def _as(jwks_env, core_rbac, sub: str) -> str:
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    return _token(jwks_env, sub)


def _get_as(client, jwks_env, core_rbac, url, sub):
    tok = _as(jwks_env, core_rbac, sub)
    return client.get(url, headers={"Authorization": f"Bearer {tok}"})


def _open_case(client, jwks_env, core_rbac) -> str:
    """Caso criado pelo solicitante e iniciado pelo analista (v2)."""
    _as(jwks_env, core_rbac, REQUESTER_SUB)
    rid = _submit_create(
        client, jwks_env, core_rbac, sub=REQUESTER_SUB
    ).json()["data"]["requestId"]
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    resp = _post(
        client, f"{_base(rid)}/actions/start", tok,
        json={"expectedVersion": 1},
    )
    assert resp.status_code == 200, resp.text
    return rid


def _request_information(
    client, jwks_env, core_rbac, rid, *, body=None, headers=None,
):
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    payload = {
        "expectedVersion": 2,
        "message": "Precisamos de esclarecimentos.",
        "questions": [
            {
                "targetType": "FIELD",
                "targetPath": "description",
                "questionText": "Confirme a descrição técnica.",
            },
            {
                "targetType": "GENERAL",
                "questionText": "Há desenho de referência?",
            },
        ],
    }
    if body is not None:
        payload = body
    return _post(
        client, f"{_base(rid)}/actions/request-information", tok,
        json=payload, headers=headers,
    )


def _open_round(client, jwks_env, core_rbac):
    rid = _open_case(client, jwks_env, core_rbac)
    resp = _request_information(client, jwks_env, core_rbac, rid)
    assert resp.status_code == 200, resp.text
    return rid, resp.json()["data"]["informationRound"]


def _answers(rnd, text="Resposta do solicitante."):
    return [
        {"questionId": q["id"], "text": f"{text} {q['ordinal']}"}
        for q in rnd["questions"]
    ]


def _draft(client, jwks_env, core_rbac, rid, rnd, *, sub=REQUESTER_SUB):
    tok = _as(jwks_env, core_rbac, sub)
    return _patch(
        client, f"{_base(rid)}/information-rounds/{rnd['id']}/answers",
        tok,
        json={
            "expectedRoundVersion": rnd["version"],
            "answers": _answers(rnd),
        },
    )


def _submit(
    client, jwks_env, core_rbac, rid, round_id, version,
    *, sub=REQUESTER_SUB, answers=None,
):
    tok = _as(jwks_env, core_rbac, sub)
    body = {"expectedRoundVersion": version}
    if answers is not None:
        body["answers"] = answers
    return _post(
        client,
        f"{_base(rid)}/information-rounds/{round_id}"
        "/actions/submit-answers",
        tok, json=body,
    )


def _submitted_round(client, jwks_env, core_rbac):
    rid, rnd = _open_round(client, jwks_env, core_rbac)
    drafted = _draft(client, jwks_env, core_rbac, rid, rnd)
    assert drafted.status_code == 200, drafted.text
    version = drafted.json()["data"]["version"]
    sent = _submit(client, jwks_env, core_rbac, rid, rnd["id"], version)
    assert sent.status_code == 200, sent.text
    return rid, sent.json()["data"]


def _accept(client, jwks_env, core_rbac, rid, rnd, question_id, version):
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    return _post(
        client,
        f"{_base(rid)}/information-rounds/{rnd['id']}"
        f"/questions/{question_id}/actions/accept",
        tok, json={"expectedRoundVersion": version},
    )


class TestInformationRoundRest:
    def test_structured_questions_create_round(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        assert rnd["status"] == "awaiting_requester"
        assert rnd["message"] == "Precisamos de esclarecimentos."
        assert [q["targetType"] for q in rnd["questions"]] == [
            "FIELD", "GENERAL",
        ]
        assert rnd["questions"][0]["targetPath"] == "description"
        assert all(q["status"] == "pending" for q in rnd["questions"])

        detail = _get_as(
            client, jwks_env, core_rbac, _base(rid), ANALYST_SUB
        ).json()["data"]
        assert detail["status"] == "needs_information"

        listed = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds", ANALYST_SUB,
        ).json()["data"]
        assert listed["total"] == 1
        assert listed["hasOpenBlocker"] is True
        got = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds/{rnd['id']}", ANALYST_SUB,
        )
        assert got.status_code == 200
        assert got.json()["data"]["id"] == rnd["id"]

    def test_empty_question_text_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _open_case(client, jwks_env, core_rbac)
        resp = _request_information(
            client, jwks_env, core_rbac, rid,
            body={
                "expectedVersion": 2,
                "questions": [
                    {"targetType": "GENERAL", "questionText": ""}
                ],
            },
        )
        assert resp.status_code == 422, resp.text
        # sem efeito colateral: caso segue em atendimento
        detail = _get_as(
            client, jwks_env, core_rbac, _base(rid), ANALYST_SUB
        ).json()["data"]
        assert detail["status"] == "in_progress"

    def test_blank_question_text_rejected_by_domain_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _open_case(client, jwks_env, core_rbac)
        resp = _request_information(
            client, jwks_env, core_rbac, rid,
            body={
                "expectedVersion": 2,
                "questions": [
                    {"targetType": "GENERAL", "questionText": "   "}
                ],
            },
        )
        assert resp.status_code == 422, resp.text

    def test_invalid_field_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _open_case(client, jwks_env, core_rbac)
        resp = _request_information(
            client, jwks_env, core_rbac, rid,
            body={
                "expectedVersion": 2,
                "questions": [
                    {
                        "targetType": "FIELD",
                        "targetPath": "campoInexistente",
                        "questionText": "Qual o valor?",
                    }
                ],
            },
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["data"]["fields"]["targetPath"] == "unknown"

    def test_requester_draft_and_submit(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        drafted = _draft(client, jwks_env, core_rbac, rid, rnd)
        assert drafted.status_code == 200, drafted.text
        view = drafted.json()["data"]
        assert view["status"] == "awaiting_requester"
        assert {q["status"] for q in view["questions"]} == {"drafted"}
        assert view["questions"][0]["answer"]["text"].startswith(
            "Resposta do solicitante."
        )

        sent = _submit(
            client, jwks_env, core_rbac, rid, rnd["id"], view["version"]
        )
        assert sent.status_code == 200, sent.text
        sent_view = sent.json()["data"]
        assert sent_view["status"] == "awaiting_review"
        assert {q["status"] for q in sent_view["questions"]} == {
            "submitted"
        }

    def test_submit_with_empty_answer_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        q = rnd["questions"][0]
        resp = _submit(
            client, jwks_env, core_rbac, rid, rnd["id"], rnd["version"],
            answers=[{"questionId": q["id"], "text": ""}],
        )
        assert resp.status_code == 422, resp.text

    def test_other_user_cannot_submit_403(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        # analista não é o solicitante do caso
        blocked = _draft(
            client, jwks_env, core_rbac, rid, rnd, sub=ANALYST_SUB
        )
        assert blocked.status_code == 403, blocked.text
        resp = _submit(
            client, jwks_env, core_rbac, rid, rnd["id"], rnd["version"],
            sub=ANALYST_SUB, answers=_answers(rnd),
        )
        assert resp.status_code == 403, resp.text
        # rodada intacta
        got = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds/{rnd['id']}", ANALYST_SUB,
        ).json()["data"]
        assert got["status"] == "awaiting_requester"

    def test_analyst_accept_all_then_resume(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, view = _submitted_round(client, jwks_env, core_rbac)
        version = view["version"]
        for q in view["questions"]:
            resp = _accept(
                client, jwks_env, core_rbac, rid, view, q["id"], version
            )
            assert resp.status_code == 200, resp.text
            version = resp.json()["data"]["version"]
        final = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds/{view['id']}", ANALYST_SUB,
        ).json()["data"]
        assert final["status"] == "resolved"
        assert {q["status"] for q in final["questions"]} == {"accepted"}

        tok = _as(jwks_env, core_rbac, ANALYST_SUB)
        resumed = _post(
            client, f"{_base(rid)}/actions/resume", tok,
            json={"expectedVersion": 3},
        )
        assert resumed.status_code == 200, resumed.text
        assert resumed.json()["data"]["status"] == "in_progress"

    def test_requester_cannot_accept_questions_with_stale_version(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, view = _submitted_round(client, jwks_env, core_rbac)
        q = view["questions"][0]
        stale = _accept(
            client, jwks_env, core_rbac, rid, view, q["id"],
            view["version"] + 5,
        )
        assert stale.status_code == 409, stale.text

    def test_follow_up_creates_second_round(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, view = _submitted_round(client, jwks_env, core_rbac)
        tok = _as(jwks_env, core_rbac, ANALYST_SUB)
        resp = _post(
            client,
            f"{_base(rid)}/information-rounds/{view['id']}"
            "/actions/request-follow-up",
            tok,
            json={
                "expectedRoundVersion": view["version"],
                "followUpQuestionIds": [view["questions"][0]["id"]],
                "questions": [
                    {
                        "targetType": "FIELD",
                        "targetPath": "description",
                        "questionText": "Detalhe melhor a descrição.",
                    }
                ],
                "message": "Complemento necessário.",
            },
            headers={"Idempotency-Key": "fu-1"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert data["round"]["id"] != view["id"]
        assert data["round"]["status"] == "awaiting_requester"
        assert data["round"]["parentRoundId"] == view["id"]
        parent_q = {
            q["id"]: q["status"] for q in data["parentRound"]["questions"]
        }
        assert parent_q[view["questions"][0]["id"]] == (
            "follow_up_requested"
        )

        listed = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds", ANALYST_SUB,
        ).json()["data"]
        assert listed["total"] == 2
        assert listed["hasOpenBlocker"] is True

        replay = _post(
            client,
            f"{_base(rid)}/information-rounds/{view['id']}"
            "/actions/request-follow-up",
            tok,
            json={
                "expectedRoundVersion": view["version"],
                "followUpQuestionIds": [view["questions"][0]["id"]],
                "questions": [
                    {
                        "targetType": "FIELD",
                        "targetPath": "description",
                        "questionText": "Detalhe melhor a descrição.",
                    }
                ],
                "message": "Complemento necessário.",
            },
            headers={"Idempotency-Key": "fu-1"},
        )
        assert replay.status_code == 200, replay.text
        assert replay.json()["data"]["round"]["id"] == data["round"]["id"]

    def test_follow_up_requires_question_ids_422(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, view = _submitted_round(client, jwks_env, core_rbac)
        tok = _as(jwks_env, core_rbac, ANALYST_SUB)
        resp = _post(
            client,
            f"{_base(rid)}/information-rounds/{view['id']}"
            "/actions/request-follow-up",
            tok,
            json={
                "expectedRoundVersion": view["version"],
                "followUpQuestionIds": [],
                "questions": [
                    {"targetType": "GENERAL", "questionText": "Mais?"}
                ],
            },
        )
        assert resp.status_code == 422, resp.text

    def test_resume_blocked_without_accept_409(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, _view = _submitted_round(client, jwks_env, core_rbac)
        tok = _as(jwks_env, core_rbac, ANALYST_SUB)
        resp = _post(
            client, f"{_base(rid)}/actions/resume", tok,
            json={"expectedVersion": 3},
        )
        assert resp.status_code == 409, resp.text
        assert "information_round_open" in resp.text
        detail = _get_as(
            client, jwks_env, core_rbac, _base(rid), ANALYST_SUB
        ).json()["data"]
        assert detail["status"] == "needs_information"

    def test_detail_filters_resume_and_exposes_information_exchange(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """FIX-01: allowedActions sem resume enquanto blocker aberto;
        informationExchange carrega capacidades explícitas."""
        rid, view = _open_round(client, jwks_env, core_rbac)
        # Analista: pode revisar, não responder; resume filtrado.
        analyst_detail = _get_as(
            client, jwks_env, core_rbac, _base(rid), ANALYST_SUB
        ).json()["data"]
        assert analyst_detail["status"] == "needs_information"
        assert "resume" not in analyst_detail["allowedActions"]
        assert "reject" in analyst_detail["allowedActions"]
        info = analyst_detail["informationExchange"]
        assert info["hasOpenBlocker"] is True
        assert info["canRespond"] is False
        assert info["canReview"] is True
        assert info["activeRoundStatus"] == "awaiting_requester"
        assert info["activeRoundId"] == view["id"]

        # Solicitante com engineering.access (dual-role): canRespond.
        requester_detail = _get_as(
            client, jwks_env, core_rbac, _base(rid), REQUESTER_SUB
        ).json()["data"]
        req_info = requester_detail["informationExchange"]
        assert req_info["hasOpenBlocker"] is True
        assert req_info["canRespond"] is True
        assert req_info["canReview"] is True
        assert "resume" not in requester_detail["allowedActions"]

    def test_resume_waiver_resolves_open_round(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, rnd = _open_round(client, jwks_env, core_rbac)
        tok = _as(jwks_env, core_rbac, ANALYST_SUB)
        resp = _post(
            client, f"{_base(rid)}/actions/resume", tok,
            json={
                "expectedVersion": 3,
                "reason": "waiver: retorno interno legado",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == "in_progress"
        got = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds/{rnd['id']}", ANALYST_SUB,
        ).json()["data"]
        assert got["status"] == "resolved"

    def test_request_information_idempotent(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _open_case(client, jwks_env, core_rbac)
        first = _request_information(
            client, jwks_env, core_rbac, rid,
            headers={"Idempotency-Key": "ri-1"},
        )
        second = _request_information(
            client, jwks_env, core_rbac, rid,
            headers={"Idempotency-Key": "ri-1"},
        )
        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert (
            first.json()["data"]["informationRound"]["id"]
            == second.json()["data"]["informationRound"]["id"]
        )
        assert "replayed" not in second.json()["data"]
        listed = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds", ANALYST_SUB,
        ).json()["data"]
        assert listed["total"] == 1

    def test_legacy_reason_and_pending_fields_still_work(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _open_case(client, jwks_env, core_rbac)
        resp = _request_information(
            client, jwks_env, core_rbac, rid,
            body={
                "expectedVersion": 2,
                "reason": "falta ficha técnica",
                "pendingFields": ["unit"],
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["status"] == "needs_information"
        questions = data["informationRound"]["questions"]
        assert len(questions) == 1
        assert questions[0]["targetType"] == "FIELD"
        assert questions[0]["targetPath"] == "unit"

    def test_unknown_round_404_and_bad_uuid_400(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, _rnd = _open_round(client, jwks_env, core_rbac)
        missing = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds/"
            "00000000-0000-4000-8000-000000000000",
            ANALYST_SUB,
        )
        assert missing.status_code == 404
        bad = _get_as(
            client, jwks_env, core_rbac,
            f"{_base(rid)}/information-rounds/not-a-uuid", ANALYST_SUB,
        )
        assert bad.status_code == 400


class TestInformationRoundEvaParity:
    def test_dispatch_registered(self):
        for action in ("information_round_list", "information_round_get"):
            assert ("product_registration", action) in _READ_DISPATCH
        for action in (
            "request_information",
            "information_question_accept",
            "information_follow_up",
        ):
            assert ("product_registration", action) in _EXECUTE_DISPATCH

    def test_registry_reuses_six_mcp_tools(self):
        from engineering_app.application.eva.semantic_registry import (
            SEMANTIC_ACTIONS,
            SEMANTIC_TOOL_NAMES,
            semantic_action,
        )

        assert len(SEMANTIC_TOOL_NAMES) == 6
        for action in (
            "request_information",
            "information_round_list",
            "information_round_get",
            "information_question_accept",
            "information_follow_up",
        ):
            entry = semantic_action("product_registration", action)
            assert entry is not None and entry.status == "proven"
            assert entry.tool in SEMANTIC_TOOL_NAMES
        assert {a.tool for a in SEMANTIC_ACTIONS} <= set(
            SEMANTIC_TOOL_NAMES
        )

    @pytest.mark.asyncio
    async def test_eva_full_cycle_matches_rest_effects(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _open_case(client, jwks_env, core_rbac)
        analyst = _ctx(ANALYST_SUB)

        opened = await prc_semantic.execute_action(
            analyst, _entry("request_information"), "act",
            target_ref=rid, expected_version=2,
            payload={
                "message": "Via EVA",
                "questions": [
                    {
                        "targetType": "FIELD",
                        "targetPath": "description",
                        "questionText": "Confirme a descrição.",
                    }
                ],
            },
            idempotency_key="eva-ri-1",
        )
        body = json.loads(opened.content[0].text)
        assert body["success"] is True, body
        rnd = body["data"]["informationRound"]
        assert rnd["status"] == "awaiting_requester"

        listed = await prc_semantic.read_action(
            analyst, _entry("information_round_list"),
            {"request_id": rid},
        )
        listed_data = json.loads(listed.content[0].text)["data"]
        assert listed_data["total"] == 1
        assert listed_data["hasOpenBlocker"] is True

        got = await prc_semantic.read_action(
            analyst, _entry("information_round_get"),
            {"request_id": rid, "round_id": rnd["id"]},
        )
        assert json.loads(got.content[0].text)["data"]["id"] == rnd["id"]

        # solicitante responde pela REST; analista aceita via EVA
        drafted = _draft(client, jwks_env, core_rbac, rid, rnd)
        assert drafted.status_code == 200, drafted.text
        sent = _submit(
            client, jwks_env, core_rbac, rid, rnd["id"],
            drafted.json()["data"]["version"],
        )
        assert sent.status_code == 200, sent.text
        sent_view = sent.json()["data"]

        prep = await prc_semantic.execute_action(
            analyst, _entry("information_question_accept"), "prepare",
            target_ref=rid,
            payload={
                "round_id": rnd["id"],
                "question_id": sent_view["questions"][0]["id"],
                "expected_round_version": sent_view["version"],
            },
        )
        assert json.loads(prep.content[0].text)["data"]["phase"] == (
            "prepare"
        )
        accepted = await prc_semantic.execute_action(
            analyst, _entry("information_question_accept"), "act",
            target_ref=rid,
            payload={
                "round_id": rnd["id"],
                "question_id": sent_view["questions"][0]["id"],
                "expected_round_version": sent_view["version"],
            },
        )
        accepted_body = json.loads(accepted.content[0].text)
        assert accepted_body["success"] is True, accepted_body
        assert accepted_body["data"]["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_eva_follow_up_creates_second_round(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, view = _submitted_round(client, jwks_env, core_rbac)
        out = await prc_semantic.execute_action(
            _ctx(ANALYST_SUB), _entry("information_follow_up"), "act",
            target_ref=rid,
            payload={
                "round_id": view["id"],
                "expected_round_version": view["version"],
                "follow_up_question_ids": [view["questions"][0]["id"]],
                "questions": [
                    {
                        "targetType": "GENERAL",
                        "questionText": "Pode detalhar?",
                    }
                ],
            },
        )
        body = json.loads(out.content[0].text)
        assert body["success"] is True, body
        assert body["data"]["round"]["parentRoundId"] == view["id"]

    @pytest.mark.asyncio
    async def test_eva_requester_cannot_accept_and_missing_ids_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid, view = _submitted_round(client, jwks_env, core_rbac)
        # sem round_id/question_id → validação, sem efeito
        bad = await prc_semantic.execute_action(
            _ctx(ANALYST_SUB), _entry("information_question_accept"),
            "act", target_ref=rid, expected_version=view["version"],
            payload={},
        )
        assert json.loads(bad.content[0].text)["success"] is False
        # principal sem engineering.access → negado no service (fail-closed)
        denied = await prc_semantic.execute_action(
            _ctx("outsider", permissions=["dashboard-engineering.view"]),
            _entry("information_question_accept"), "act",
            target_ref=rid,
            payload={
                "round_id": view["id"],
                "question_id": view["questions"][0]["id"],
                "expected_round_version": view["version"],
            },
        )
        assert json.loads(denied.content[0].text)["success"] is False
