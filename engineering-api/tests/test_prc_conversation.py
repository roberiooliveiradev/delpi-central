"""PRC-CONVERSATION — conversa do caso (Issue #207, P0+P1).

Cobre: criação/listagem/edição de mensagens, anexos da conversa,
idempotência, CAS, escopo por objeto (requester × analyst × terceiro),
congelamento em estado terminal e anti-IDOR — sobre o harness real
FastAPI + repo/storage in-memory (mesma fiação do runtime).
"""

from __future__ import annotations

import io

import pytest

from tests.conftest import rbac_payload
from engineering_app.domain.product_registration.models import MR_PRC_CREATE
from tests.test_product_registration import (
    ANALYST,
    _post,
    _token,
    prc_service_repo,  # noqa: F401 — fiação do service
)

# Ator «solicitante» real: só my-requests.prc.create — sem engineering.access,
# portanto não-analista e sujeito ao escopo por objeto.
REQUESTER_PERMS = [MR_PRC_CREATE]
from tests.test_prc_ref023_attachments import PNG, _create

REQUESTER_SUB = "user-1"
ANALYST_SUB = "analyst-1"
OTHER_SUB = "intruder-1"


def _base(rid: str) -> str:
    return f"/v1/product-registration/requests/{rid}"


def _as(jwks_env, core_rbac, sub, perms=ANALYST):
    core_rbac["behavior"] = ("data", rbac_payload(perms, id=sub))
    return _token(jwks_env, sub)


def _comment(client, jwks_env, core_rbac, rid, body="olá engenharia",
             sub=REQUESTER_SUB, headers=None, perms=ANALYST):
    tok = _as(jwks_env, core_rbac, sub, perms)
    h = {"Authorization": f"Bearer {tok}", **(headers or {})}
    return client.post(f"{_base(rid)}/comments", json={"body": body},
                       headers=h)


def _post_comment_ok(client, jwks_env, core_rbac, rid, **kw):
    r = _comment(client, jwks_env, core_rbac, rid, **kw)
    assert r.status_code == 201, r.text
    return r.json()["data"]["comment"]


def _start(client, jwks_env, core_rbac, rid):
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    r = _post(client, f"{_base(rid)}/actions/start", tok,
              json={"expectedVersion": 1})
    assert r.status_code == 200, r.text


class TestCommentCreate:
    def test_create_returns_persisted_comment(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        c = _post_comment_ok(client, jwks_env, core_rbac, rid)
        assert c["requestId"] == rid
        assert c["authorSubject"] == REQUESTER_SUB
        assert c["body"] == "olá engenharia"
        assert c["isMine"] is True
        assert c["version"] == 1
        assert c["edited"] is False

    def test_author_never_from_payload(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
        r = client.post(
            f"{_base(rid)}/comments",
            json={"body": "oi", "authorUserId": "spoofed",
                  "authorSubject": "spoofed"},
            headers={"Authorization": f"Bearer {tok}"},
        )
        assert r.status_code == 201, r.text
        assert r.json()["data"]["comment"]["authorSubject"] == REQUESTER_SUB

    def test_empty_and_external_image_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        assert _comment(client, jwks_env, core_rbac, rid, body="  ").status_code == 422
        r = _comment(client, jwks_env, core_rbac, rid,
                     body="![x](https://evil.example/t.png)")
        assert r.status_code == 422
        # attachment: scheme é o único caminho de imagem legítimo
        r = _comment(client, jwks_env, core_rbac, rid,
                     body="![x](attachment:pending:abc)")
        assert r.status_code == 201, r.text

    def test_idempotent_replay_same_key_same_body(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        h = {"Idempotency-Key": "conv-k1"}
        r1 = _comment(client, jwks_env, core_rbac, rid, headers=h)
        r2 = _comment(client, jwks_env, core_rbac, rid, headers=h)
        assert r1.status_code == 201 and r2.status_code == 200
        tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
        items = client.get(f"{_base(rid)}/comments",
                           headers={"Authorization": f"Bearer {tok}"}
                           ).json()["data"]["items"]
        assert len(items) == 1  # replay não duplica

    def test_idempotent_key_payload_divergence(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        h = {"Idempotency-Key": "conv-k2"}
        assert _comment(client, jwks_env, core_rbac, rid,
                        headers=h).status_code == 201
        r = _comment(client, jwks_env, core_rbac, rid, body="outro",
                     headers=h)
        assert r.status_code == 409


class TestCommentList:
    def test_order_pagination_is_mine(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        for i in range(3):
            _post_comment_ok(client, jwks_env, core_rbac, rid,
                             body=f"m{i}", sub=REQUESTER_SUB)
        _post_comment_ok(client, jwks_env, core_rbac, rid,
                         body="analyst reply", sub=ANALYST_SUB)
        tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
        r = client.get(f"{_base(rid)}/comments?page=1&pageSize=2",
                       headers={"Authorization": f"Bearer {tok}"})
        data = r.json()["data"]
        assert data["total"] == 4 and len(data["items"]) == 2
        bodies = [i["body"] for i in data["items"]]
        assert bodies == ["m0", "m1"]  # cronológica ASC
        page2 = client.get(f"{_base(rid)}/comments?page=2&pageSize=2",
                           headers={"Authorization": f"Bearer {tok}"}
                           ).json()["data"]["items"]
        assert [i["body"] for i in page2] == ["m2", "analyst reply"]
        assert page2[-1]["isMine"] is False

    def test_out_of_scope_user_gets_403(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        _post_comment_ok(client, jwks_env, core_rbac, rid)
        # OTHER_SUB só tem MR_PRC_CREATE → não-analista, fora do escopo.
        tok = _as(jwks_env, core_rbac, OTHER_SUB, REQUESTER_PERMS)
        r = client.get(f"{_base(rid)}/comments",
                       headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403
        r = _comment(client, jwks_env, core_rbac, rid, sub=OTHER_SUB,
                     perms=REQUESTER_PERMS)
        assert r.status_code == 403

    def test_no_permission_401_or_403(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        r = client.get(f"{_base(rid)}/comments")
        assert r.status_code in (401, 403)
        core_rbac["behavior"] = ("data", rbac_payload([], id=OTHER_SUB))
        tok = _token(jwks_env, OTHER_SUB)
        r = client.get(f"{_base(rid)}/comments",
                       headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403

    def test_analyst_reads_and_posts(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        _start(client, jwks_env, core_rbac, rid)
        c = _post_comment_ok(client, jwks_env, core_rbac, rid,
                             body="pergunta técnica", sub=ANALYST_SUB)
        assert c["authorSubject"] == ANALYST_SUB


class TestCommentUpdate:
    def test_author_edits_and_version_bumps(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        c = _post_comment_ok(client, jwks_env, core_rbac, rid)
        tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
        r = client.patch(
            f"{_base(rid)}/comments/{c['commentId']}",
            json={"body": "editado", "expectedVersion": 1},
            headers={"Authorization": f"Bearer {tok}"},
        )
        assert r.status_code == 200, r.text
        c2 = r.json()["data"]["comment"]
        assert c2["body"] == "editado"
        assert c2["version"] == 2 and c2["edited"] is True
        # autoridade original preservada
        assert c2["authorSubject"] == REQUESTER_SUB

    def test_stale_version_409(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        c = _post_comment_ok(client, jwks_env, core_rbac, rid)
        tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
        client.patch(f"{_base(rid)}/comments/{c['commentId']}",
                     json={"body": "v2"}, headers={"Authorization": f"Bearer {tok}"})
        r = client.patch(f"{_base(rid)}/comments/{c['commentId']}",
                         json={"body": "v3", "expectedVersion": 1},
                         headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 409

    def test_non_author_non_analyst_403(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        c = _post_comment_ok(client, jwks_env, core_rbac, rid)
        # analyst do próprio caso? não — analista pode moderar; quem
        # não pode é o requester de outro caso (escopo) E um
        # não-analista no escopo (requester do caso).
        tok_other = _as(jwks_env, core_rbac, OTHER_SUB, REQUESTER_PERMS)
        r = client.patch(f"{_base(rid)}/comments/{c['commentId']}",
                         json={"body": "hack"},
                         headers={"Authorization": f"Bearer {tok_other}"})
        assert r.status_code == 403
        # requester do caso (não-autor, não-analista) também 403
        c_analyst = _post_comment_ok(client, jwks_env, core_rbac, rid,
                                     body="do analista", sub=ANALYST_SUB)
        tok_req = _as(jwks_env, core_rbac, REQUESTER_SUB, REQUESTER_PERMS)
        r = client.patch(f"{_base(rid)}/comments/{c_analyst['commentId']}",
                         json={"body": "hack"},
                         headers={"Authorization": f"Bearer {tok_req}"})
        assert r.status_code == 403

    def test_comment_of_other_request_404(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid_a = _create(client, jwks_env, core_rbac, suffix="a")
        rid_b = _create(client, jwks_env, core_rbac, suffix="b")
        c = _post_comment_ok(client, jwks_env, core_rbac, rid_a)
        tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
        r = client.patch(f"{_base(rid_b)}/comments/{c['commentId']}",
                         json={"body": "x"},
                         headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 404  # identidade composta — anti-IDOR


class TestTerminalFreeze:
    def test_rejected_case_freezes_conversation(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        _post_comment_ok(client, jwks_env, core_rbac, rid)  # antes: ok
        tok = _as(jwks_env, core_rbac, ANALYST_SUB)
        r = _post(client, f"{_base(rid)}/actions/reject", tok,
                  json={"expectedVersion": 1, "reason": "fora de escopo"})
        assert r.status_code == 200, r.text
        r = _comment(client, jwks_env, core_rbac, rid, body="tarde demais")
        assert r.status_code == 409  # conversation_frozen
        # leitura da conversa segue aberta
        r = client.get(f"{_base(rid)}/comments",
                       headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200


class TestCommentAttachments:
    def _open_comment(self, client, jwks_env, core_rbac, rid):
        _start(client, jwks_env, core_rbac, rid)
        return _post_comment_ok(client, jwks_env, core_rbac, rid,
                                body="segue print", sub=ANALYST_SUB)

    def _upload(self, client, tok, rid, cid, content=PNG,
                filename="print.png", mime="image/png"):
        return client.post(
            f"{_base(rid)}/comments/{cid}/attachments",
            headers={"Authorization": f"Bearer {tok}"},
            files={"file": (filename, io.BytesIO(content), mime)},
        )

    def test_upload_list_download_delete(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        c = self._open_comment(client, jwks_env, core_rbac, rid)
        cid, tok = c["commentId"], _as(jwks_env, core_rbac, ANALYST_SUB)
        r = self._upload(client, tok, rid, cid)
        assert r.status_code == 201, r.text
        att = r.json()["data"]["attachment"]
        assert att["mediaType"] == "image/png"
        assert "storageKey" not in att and "storage_key" not in att
        # lista
        r = client.get(f"{_base(rid)}/comments/{cid}/attachments",
                       headers={"Authorization": f"Bearer {tok}"})
        assert len(r.json()["data"]["attachments"]) == 1
        # download
        r = client.get(
            f"{_base(rid)}/comments/{cid}/attachments/{att['attachmentId']}",
            headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200 and r.content == PNG
        assert r.headers["x-content-type-options"] == "nosniff"
        # delete (autor do comentário)
        r = client.delete(
            f"{_base(rid)}/comments/{cid}/attachments/{att['attachmentId']}",
            headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        r = client.get(f"{_base(rid)}/comments/{cid}/attachments",
                       headers={"Authorization": f"Bearer {tok}"})
        assert r.json()["data"]["attachments"] == []

    def test_non_author_upload_403_and_idor_404(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid_a = _create(client, jwks_env, core_rbac, suffix="a")
        rid_b = _create(client, jwks_env, core_rbac, suffix="b")
        _start(client, jwks_env, core_rbac, rid_a)
        # comentário do ANALISTA → requester (no escopo, não-autor,
        # não-analista) não pode anexar nele
        c2 = _post_comment_ok(client, jwks_env, core_rbac, rid_a,
                              body="com anexo", sub=ANALYST_SUB)
        tok_req = _as(jwks_env, core_rbac, REQUESTER_SUB, REQUESTER_PERMS)
        r = self._upload(client, tok_req, rid_a, c2["commentId"])
        assert r.status_code == 403
        # analyst envia anexo legítimo
        tok_an = _as(jwks_env, core_rbac, ANALYST_SUB)
        att = self._upload(client, tok_an, rid_a, c2["commentId"]
                           ).json()["data"]["attachment"]
        # IDOR: attachment do caso A via rota do caso B → 404
        r = client.get(
            f"{_base(rid_b)}/comments/{c2['commentId']}/attachments/"
            f"{att['attachmentId']}",
            headers={"Authorization": f"Bearer {tok_an}"})
        assert r.status_code == 404

    def test_fake_type_rejected_and_dedup(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _create(client, jwks_env, core_rbac)
        c = self._open_comment(client, jwks_env, core_rbac, rid)
        cid, tok = c["commentId"], _as(jwks_env, core_rbac, ANALYST_SUB)
        r = self._upload(client, tok, rid, cid, content=b"MZ" + b"\x00" * 32,
                         filename="evil.png")
        assert r.status_code == 422
        # dedup: mesmo bytes+nome → não duplica
        self._upload(client, tok, rid, cid)
        r = self._upload(client, tok, rid, cid)
        assert r.status_code == 201
        assert r.json()["data"]["deduplicated"] is True
