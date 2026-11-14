"""Foundation tests for satisfaction survey (E1/E2 domain + isolation)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet
from fastapi import Request

from commercial_app.application.security import commercial_permissions as perms
from commercial_app.application.use_cases.manage_satisfaction_surveys import (
    CreateCampaignCommand,
    ManageSatisfactionSurveysUseCase,
    SatisfactionSurveyError,
    SubmitPublicResponseCommand,
)
from commercial_app.domain.entities.satisfaction_survey import (
    RecipientAddItem,
    SatisfactionCampaign,
    SatisfactionRecipient,
)
from commercial_app.domain.services.satisfaction_questionnaire import (
    DIMENSION_KEYS,
    QUESTIONNAIRE_VERSION,
    assert_invite_placeholders_allowed,
    get_questionnaire_catalog,
    unknown_invite_placeholders,
    validate_dimensions_payload,
)
from commercial_app.infrastructure.crypto.token_cipher import TokenCipher
from commercial_app.infrastructure.persistence.plugins import migrations_runner
from commercial_app.interface.http.routes import satisfaction_survey_routes as routes
from commercial_app.middleware import auth_middleware


def test_questionnaire_has_15_canonical_items():
    catalog = get_questionnaire_catalog()
    assert catalog["questionnaire_version"] == QUESTIONNAIRE_VERSION
    assert len(catalog["items"]) == 15
    assert catalog["dimension_keys"] == list(DIMENSION_KEYS)


def test_dimensions_require_explicit_na_or_score():
    payload = {key: 4 for key in DIMENSION_KEYS}
    payload["technical_support"] = None
    normalized = validate_dimensions_payload(payload)
    assert normalized["technical_support"] is None
    with pytest.raises(ValueError):
        validate_dimensions_payload({key: 4 for key in DIMENSION_KEYS if key != "quality"})


def test_invite_placeholders_reject_unknown():
    assert unknown_invite_placeholders("Olá {nome_empresa}") == []
    assert unknown_invite_placeholders("x {foo} y {bar}") == ["{bar}", "{foo}"]
    with pytest.raises(ValueError, match="não permitidos"):
        assert_invite_placeholders_allowed("Assunto {cliente}", "Corpo {link_pesquisa}")


def test_get_recipient_omits_invite_by_default():
    now = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    repo = MagicMock()
    campaign = SatisfactionCampaign(
        id="c1",
        name="Pesquisa 2026",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=10),
        questionnaire_version=QUESTIONNAIRE_VERSION,
        invite_subject="s",
        invite_body="b {link_pesquisa}",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
    )
    recipient = SatisfactionRecipient(
        id="r1",
        campaign_id="c1",
        customer_code="001",
        customer_store="01",
        customer_name_snapshot="Alpha",
        contact_name=None,
        contact_email=None,
        token_hash="hash",
        token_ciphertext="cipher",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
    )
    repo.get_campaign.return_value = campaign
    repo.get_recipient.return_value = recipient
    uc = _build_use_case(repo, now=now)
    payload = uc.get_recipient(campaign_id="c1", recipient_id="r1")
    assert "invite" not in payload
    with_invite = uc.get_recipient(
        campaign_id="c1", recipient_id="r1", include_resolved_invite=True
    )
    assert "invite" in with_invite


def test_serialize_campaign_response_rate():
    now = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    repo = MagicMock()
    uc = _build_use_case(repo, now=now)
    empty = SatisfactionCampaign(
        id="c0",
        name="Vazia",
        starts_at=now,
        ends_at=now + timedelta(days=1),
        questionnaire_version=QUESTIONNAIRE_VERSION,
        invite_subject="s",
        invite_body="b",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
        recipient_count=0,
        response_count=0,
    )
    assert uc.serialize_campaign(empty, now=now)["response_rate"] is None
    filled = SatisfactionCampaign(
        id="c1",
        name="Com taxa",
        starts_at=now,
        ends_at=now + timedelta(days=1),
        questionnaire_version=QUESTIONNAIRE_VERSION,
        invite_subject="s",
        invite_body="b",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
        recipient_count=4,
        response_count=1,
    )
    assert uc.serialize_campaign(filled, now=now)["response_rate"] == 25.0


def test_marketing_and_satisfaction_manage_permissions():
    access = SimpleNamespace(permissions=["commercial.access"])
    marketing = SimpleNamespace(permissions=["commercial.marketing"])
    manage = SimpleNamespace(permissions=["commercial.manage"])
    assert not perms.has_satisfaction_manage(access)
    assert perms.has_satisfaction_manage(marketing)
    assert perms.has_satisfaction_manage(manage)
    assert perms.has_marketing(marketing)
    assert not perms.has_marketing(manage)


def test_migration_v024_is_gated(monkeypatch: pytest.MonkeyPatch, tmp_path):
    path = tmp_path / "V024__satisfaction_surveys.sql"
    path.write_text("-- gated", encoding="utf-8")
    monkeypatch.delenv("COMMERCIAL_SATISFACTION_SURVEY_ENABLED", raising=False)
    assert migrations_runner.is_migration_apply_allowed(path) is False
    monkeypatch.setenv("COMMERCIAL_SATISFACTION_SURVEY_ENABLED", "true")
    assert migrations_runner.is_migration_apply_allowed(path) is True


def test_public_path_allowlist_fail_closed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        auth_middleware.settings,
        "COMMERCIAL_SATISFACTION_SURVEY_ENABLED",
        False,
        raising=False,
    )
    assert (
        auth_middleware._is_satisfaction_public_path(
            "/public/satisfaction-surveys/abc"
        )
        is False
    )
    monkeypatch.setattr(
        auth_middleware.settings,
        "COMMERCIAL_SATISFACTION_SURVEY_ENABLED",
        True,
        raising=False,
    )
    assert (
        auth_middleware._is_satisfaction_public_path(
            "/public/satisfaction-surveys/tok_abcDEF0123456789"
        )
        is True
    )
    assert (
        auth_middleware._is_satisfaction_public_path(
            "/public/satisfaction-surveys/tok/extra/leak"
        )
        is False
    )


class _User:
    def __init__(self, permissions: list[str], sub: str = "user-survey"):
        self.permissions = permissions
        self.sub = sub


def _request(path: str = "/satisfaction-surveys/campaigns") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("test", 123),
        "server": ("test", 80),
    }
    return Request(scope)


def test_list_campaigns_403_for_access_only(monkeypatch: pytest.MonkeyPatch):
    request = _request()
    request.state.user = _User(["commercial.access"])
    response = routes.list_satisfaction_campaigns(request)
    assert response.status_code == 403


def test_list_campaigns_200_for_marketing(monkeypatch: pytest.MonkeyPatch):
    request = _request()
    request.state.user = _User(["commercial.marketing"])
    fake = MagicMock()
    fake.list_campaigns.return_value = []
    monkeypatch.setattr(routes, "_use_case", lambda: fake)
    response = routes.list_satisfaction_campaigns(request)
    assert response.status_code == 200


def test_create_campaign_resolves_actor_from_delpi_auth_id(
    monkeypatch: pytest.MonkeyPatch,
):
    """delpi_auth popula ``user.id`` (não ``sub``); create não pode 401."""
    request = _request()
    request.state.user = SimpleNamespace(
        id="principal-uuid-hml",
        permissions=["commercial.marketing"],
        email="hml@test.local",
        name="HML Tester",
    )
    fake = MagicMock()
    fake.create_campaign.return_value = {"id": "c-new", "name": "HML"}
    monkeypatch.setattr(routes, "_use_case", lambda: fake)
    body = routes.CreateCampaignBody(
        name="HML — Pesquisa",
        starts_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        ends_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    response = routes.create_satisfaction_campaign(request, body)
    assert response.status_code == 201
    cmd = fake.create_campaign.call_args.args[0]
    assert cmd.created_by_user_id == "principal-uuid-hml"


def _build_use_case(repo: MagicMock, *, now: datetime | None = None):
    key = Fernet.generate_key().decode()
    cipher = TokenCipher(key)
    clock = (lambda: now) if now else None
    return ManageSatisfactionSurveysUseCase(
        repo,
        token_cipher=cipher,
        public_base_url="https://example.test",
        clock=clock,
    )


def test_create_campaign_and_add_recipients_idempotent():
    now = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    repo = MagicMock()
    campaign = SatisfactionCampaign(
        id="c1",
        name="Pesquisa 2026",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=10),
        questionnaire_version=QUESTIONNAIRE_VERSION,
        invite_subject="Assunto {nome_empresa}",
        invite_body="Link {link_pesquisa}",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
        recipient_count=0,
        response_count=0,
    )
    existing = SatisfactionRecipient(
        id="r-existing",
        campaign_id="c1",
        customer_code="001",
        customer_store="01",
        customer_name_snapshot="Alpha",
        contact_name=None,
        contact_email=None,
        token_hash="hash",
        token_ciphertext="cipher",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
    )
    created = SatisfactionRecipient(
        id="r-new",
        campaign_id="c1",
        customer_code="002",
        customer_store="01",
        customer_name_snapshot="Beta",
        contact_name=None,
        contact_email=None,
        token_hash="hash2",
        token_ciphertext="cipher2",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
    )
    repo.create_campaign.return_value = campaign
    repo.get_campaign.return_value = campaign

    def find_by_customer(**kwargs):
        if kwargs["customer_code"] == "001":
            return existing
        return None

    repo.find_recipient_by_customer.side_effect = find_by_customer
    repo.create_recipient.return_value = created

    class _Elig:
        def lookup(self, customers):
            from commercial_app.domain.ports.customer_eligibility_port import (
                CustomerEligibility,
            )

            return {
                (code, store): CustomerEligibility(exists=True, active=True)
                for code, store in customers
            }

    uc = ManageSatisfactionSurveysUseCase(
        repo,
        token_cipher=TokenCipher(Fernet.generate_key().decode()),
        public_base_url="https://example.test",
        clock=lambda: now,
        customer_eligibility=_Elig(),
    )
    created_campaign = uc.create_campaign(
        CreateCampaignCommand(
            name="Pesquisa 2026",
            starts_at=campaign.starts_at,
            ends_at=campaign.ends_at,
            created_by_user_id="u1",
        )
    )
    assert created_campaign["status"] == "open"

    batch = uc.add_recipients(
        campaign_id="c1",
        items=[
            RecipientAddItem(customer_code="001", customer_store="01", customer_name="Alpha"),
            RecipientAddItem(customer_code="002", customer_store="01", customer_name="Beta"),
        ],
        created_by_user_id="u1",
    )
    assert batch["counts"]["already_existing"] == 1
    assert batch["counts"]["included"] == 1
    assert batch["counts"]["failed"] == 0


def test_add_recipients_rejects_unknown_totvs_customer():
    now = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    repo = MagicMock()
    campaign = SatisfactionCampaign(
        id="c1",
        name="Pesquisa 2026",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=10),
        questionnaire_version=QUESTIONNAIRE_VERSION,
        invite_subject="s",
        invite_body="b",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
    )
    repo.get_campaign.return_value = campaign
    repo.find_recipient_by_customer.return_value = None

    class _EligMissing:
        def lookup(self, customers):
            return {}

    uc = ManageSatisfactionSurveysUseCase(
        repo,
        token_cipher=TokenCipher(Fernet.generate_key().decode()),
        public_base_url="https://example.test",
        clock=lambda: now,
        customer_eligibility=_EligMissing(),
    )
    batch = uc.add_recipients(
        campaign_id="c1",
        items=[
            RecipientAddItem(customer_code="999", customer_store="01", customer_name="Ghost"),
        ],
        created_by_user_id="u1",
    )
    assert batch["counts"]["failed"] == 1
    assert batch["failed"][0]["reason"] == "customer_not_found"
    repo.create_recipient.assert_not_called()


def test_public_submit_rejects_duplicate_and_validates_dimensions():
    now = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
    repo = MagicMock()
    campaign = SatisfactionCampaign(
        id="c1",
        name="Pesquisa 2026",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=10),
        questionnaire_version=QUESTIONNAIRE_VERSION,
        invite_subject="s",
        invite_body="b",
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
    )
    key = Fernet.generate_key().decode()
    cipher = TokenCipher(key)
    token = "token_value_abcdefghijklmnop"
    recipient = SatisfactionRecipient(
        id="r1",
        campaign_id="c1",
        customer_code="001",
        customer_store="01",
        customer_name_snapshot="Alpha",
        contact_name=None,
        contact_email=None,
        token_hash=ManageSatisfactionSurveysUseCase._hash_token(token),
        token_ciphertext=cipher.encrypt(token),
        created_by_user_id="u1",
        created_at=now,
        updated_at=now,
        version=1,
        has_response=False,
    )
    repo.get_recipient_by_token_hash.return_value = recipient
    repo.get_campaign.return_value = campaign
    repo.get_response_by_recipient.return_value = None

    class _Resp:
        id = "resp1"
        submitted_at = now

    repo.create_response.return_value = _Resp()
    uc = ManageSatisfactionSurveysUseCase(
        repo, token_cipher=cipher, public_base_url="https://example.test", clock=lambda: now
    )
    dims = {key: 5 for key in DIMENSION_KEYS}
    dims["quality"] = None
    result = uc.submit_public_response(
        SubmitPublicResponseCommand(
            token=token,
            overall_score=4,
            recommendation_score=9,
            dimensions=dims,
        )
    )
    assert result["status"] == "submitted"

    recipient_done = SatisfactionRecipient(
        id=recipient.id,
        campaign_id=recipient.campaign_id,
        customer_code=recipient.customer_code,
        customer_store=recipient.customer_store,
        customer_name_snapshot=recipient.customer_name_snapshot,
        contact_name=recipient.contact_name,
        contact_email=recipient.contact_email,
        token_hash=recipient.token_hash,
        token_ciphertext=recipient.token_ciphertext,
        created_by_user_id=recipient.created_by_user_id,
        created_at=recipient.created_at,
        updated_at=recipient.updated_at,
        version=recipient.version,
        has_response=True,
    )
    repo.get_recipient_by_token_hash.return_value = recipient_done
    with pytest.raises(SatisfactionSurveyError) as exc:
        uc.submit_public_response(
            SubmitPublicResponseCommand(
                token=token,
                overall_score=4,
                recommendation_score=9,
                dimensions=dims,
            )
        )
    assert exc.value.code == "already_submitted"
