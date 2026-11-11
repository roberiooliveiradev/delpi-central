"""PRC-REF-023-F01 — documentos opcionais de apoio técnico."""

from __future__ import annotations

import io

import pytest

from tests.conftest import rbac_payload
from tests.test_product_registration import (
    ANALYST,
    _post,
    _submit_create,
    _token,
    prc_service_repo,
)

REQUESTER_SUB = "user-1"
ANALYST_SUB = "analyst-1"
OTHER_SUB = "other-user"


def _base(rid: str) -> str:
    return f"/v1/product-registration/requests/{rid}"


def _as(jwks_env, core_rbac, sub):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    return _token(jwks_env, sub)


PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
PNG = (
    b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + b"IHDR" + b"\x00" * 21
)
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 16 + b"\xff\xd9"
WEBP = b"RIFF" + (16).to_bytes(4, "little") + b"WEBP" + b"VP8 " + b"\x00" * 8
WEBP = b"RIFF" + (len(b"WEBPVP8 \x00\x00\x00\x00")).to_bytes(
    4, "little"
) + b"WEBPVP8 \x00\x00\x00\x00"


def _upload(client, tok, rid, content, filename, mime="application/pdf"):
    return client.post(
        f"{_base(rid)}/attachments",
        headers={"Authorization": f"Bearer {tok}"},
        files={"file": (filename, io.BytesIO(content), mime)},
    )


def _create(client, jwks_env, core_rbac, suffix=""):
    from tests.test_product_registration import _create_body
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=REQUESTER_SUB))
    body = _create_body()
    body["externalRequestId"] = f"ext-1{suffix}"
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env, REQUESTER_SUB),
        json=body,
        headers={"Idempotency-Key": f"k-1{suffix}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["requestId"]


def _create_and_start(client, jwks_env, core_rbac, rid):
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    r = _post(
        client, f"{_base(rid)}/actions/start", tok,
        json={"expectedVersion": 1},
    )
    assert r.status_code == 200, r.text


def test_create_without_attachment(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = client.get(
        f"{_base(rid)}/attachments",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attachments"] == []
    assert r.json()["data"]["canUpload"] is True


def test_upload_pdf_valid(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, PDF, "datasheet.pdf")
    assert r.status_code == 201, r.text
    att = r.json()["data"]["attachment"]
    assert att["state"] == "AVAILABLE"
    assert att["mediaType"] == "application/pdf"
    assert att["sizeBytes"] == len(PDF)
    assert att["sha256"]
    assert att["originalFileName"] == "datasheet.pdf"
    # Semântica honesta: inspeção estrutural, não scan antimalware.
    assert att["inspection"] == "structural"
    assert "storageKey" not in str(att).lower()
    assert "storage_key" not in att


def test_upload_image_valid(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, PNG, "foto.png", "image/png")
    assert r.status_code == 201, r.text
    assert r.json()["data"]["attachment"]["mediaType"] == "image/png"


def test_upload_type_not_allowed(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, b"MZ\x90\x00" + b"\x00" * 60, "evil.exe")
    assert r.status_code == 422, r.text


def test_upload_fake_mime_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    """Content-Type declarado PDF com bytes de texto → rejeitado."""
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(
        client, tok, rid, b"plain text not a pdf", "fake.pdf",
        "application/pdf",
    )
    assert r.status_code == 422, r.text


def test_upload_corrupt_pdf_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(
        client, tok, rid, b"%PDF-1.4 corrupted-no-eof", "bad.pdf"
    )
    assert r.status_code == 422, r.text


def test_upload_empty_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, b"", "empty.pdf")
    assert r.status_code == 422, r.text


def test_upload_too_large_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    big = b"%PDF-1.4\n" + b"\x00" * (10 * 1024 * 1024 + 1)
    r = _upload(client, tok, rid, big, "big.pdf")
    assert r.status_code == 413, r.text


def test_upload_other_requester_forbidden(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, OTHER_SUB)
    r = _upload(client, tok, rid, PDF, "doc.pdf")
    assert r.status_code in (403, 404), r.text


def test_download_authorized(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, PDF, "datasheet.pdf")
    assert r.status_code == 201, r.text
    att_id = r.json()["data"]["attachment"]["attachmentId"]
    # Solicitante baixa
    d = client.get(
        f"{_base(rid)}/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert d.status_code == 200, d.text
    assert d.content == PDF
    assert "attachment" in d.headers.get("content-disposition", "")
    assert d.headers.get("x-content-type-options") == "nosniff"
    # Analista autorizado também baixa
    tok2 = _as(jwks_env, core_rbac, ANALYST_SUB)
    d = client.get(
        f"{_base(rid)}/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {tok2}"},
    )
    assert d.status_code == 200, d.text


def test_download_other_case_forbidden(
    client, jwks_env, core_rbac, prc_service_repo
):
    """Usuário sem engineering.access não baixa documento do chamado —
    negado no gate de permissão antes do objeto."""
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, PDF, "doc.pdf")
    att_id = r.json()["data"]["attachment"]["attachmentId"]
    core_rbac["behavior"] = ("data", rbac_payload([], id=OTHER_SUB))
    tok2 = _token(jwks_env, OTHER_SUB)
    d = client.get(
        f"{_base(rid)}/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {tok2}"},
    )
    assert d.status_code == 403, d.text


def test_list_other_case_forbidden(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    core_rbac["behavior"] = ("data", rbac_payload([], id=OTHER_SUB))
    tok2 = _token(jwks_env, OTHER_SUB)
    r = client.get(
        f"{_base(rid)}/attachments",
        headers={"Authorization": f"Bearer {tok2}"},
    )
    assert r.status_code == 403, r.text


def test_download_attachment_not_found_404(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    d = client.get(
        f"{_base(rid)}/attachments/22222222-2222-2222-2222-222222222222/download",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert d.status_code == 404, d.text


def test_upload_analyst_forbidden(
    client, jwks_env, core_rbac, prc_service_repo
):
    """Analista (não-solicitante) não anexa — upload é do requester."""
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, ANALYST_SUB)
    r = _upload(client, tok, rid, PDF, "doc.pdf")
    assert r.status_code == 403, r.text


def test_download_attachment_of_other_case_404(
    client, jwks_env, core_rbac, prc_service_repo
):
    """ID de anexo de um caso não serve em outro caso."""
    rid1 = _create(client, jwks_env, core_rbac)
    rid2 = _create(client, jwks_env, core_rbac, suffix="-b")
    assert rid1 != rid2
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid1, PDF, "doc.pdf")
    att_id = r.json()["data"]["attachment"]["attachmentId"]
    d = client.get(
        f"{_base(rid2)}/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert d.status_code == 404, d.text


def test_duplicate_upload_deduplicated(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r1 = _upload(client, tok, rid, PDF, "doc.pdf")
    r2 = _upload(client, tok, rid, PDF, "doc.pdf")
    assert r1.status_code == 201 and r2.status_code == 201
    a1 = r1.json()["data"]["attachment"]
    a2 = r2.json()["data"]["attachment"]
    assert a1["attachmentId"] == a2["attachmentId"]
    assert r2.json()["data"]["deduplicated"] is True
    # Lista continua com 1 documento
    lst = client.get(
        f"{_base(rid)}/attachments",
        headers={"Authorization": f"Bearer {tok}"},
    ).json()["data"]["attachments"]
    assert len(lst) == 1


def test_upload_in_progress_blocked_for_everyone(
    client, jwks_env, core_rbac, prc_service_repo
):
    """FIX-08 — iniciado o atendimento, documentos da ficha ficam
    somente leitura (upload, retry e substituição bloqueados)."""
    rid = _create(client, jwks_env, core_rbac)
    _create_and_start(client, jwks_env, core_rbac, rid)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, PDF, "doc.pdf")
    assert r.status_code == 409, r.text
    lst = client.get(
        f"{_base(rid)}/attachments",
        headers={"Authorization": f"Bearer {tok}"},
    ).json()["data"]
    assert lst["canUpload"] is False


def test_upload_completed_case_rejected(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    repo = prc_service_repo["repo"]
    req = repo._requests[rid]
    req["status"] = "completed"
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(client, tok, rid, PDF, "doc.pdf")
    assert r.status_code == 409, r.text


def test_upload_nonexistent_case_404(
    client, jwks_env, core_rbac, prc_service_repo
):
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(
        client, tok, "11111111-1111-1111-1111-111111111111", PDF, "d.pdf"
    )
    assert r.status_code == 404, r.text


def test_filename_sanitized(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    r = _upload(
        client, tok, rid, PDF, "../../etc/passwd.pdf"
    )
    assert r.status_code == 201, r.text
    name = r.json()["data"]["attachment"]["originalFileName"]
    assert "/" not in name and ".." not in name
    assert name == "passwd.pdf"


def test_multiple_attachments_list(
    client, jwks_env, core_rbac, prc_service_repo
):
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    assert _upload(client, tok, rid, PDF, "a.pdf").status_code == 201
    assert _upload(client, tok, rid, PNG, "b.png", "image/png").status_code == 201
    lst = client.get(
        f"{_base(rid)}/attachments",
        headers={"Authorization": f"Bearer {tok}"},
    ).json()["data"]["attachments"]
    assert len(lst) == 2


def test_attachment_not_in_completion(
    client, jwks_env, core_rbac, prc_service_repo
):
    """Anexo não altera verify/complete — conclusão segue MATCH oficial."""
    rid = _create(client, jwks_env, core_rbac)
    tok = _as(jwks_env, core_rbac, REQUESTER_SUB)
    assert _upload(client, tok, rid, PDF, "doc.pdf").status_code == 201
    # Fluxo REF-020 permanece: o detalhe não inclui anexo como campo.
    detail = client.get(
        _base(rid),
        headers={"Authorization": f"Bearer {tok}"},
    ).json()["data"]
    assert "attachments" not in (detail.get("technicalDraft") or {})
