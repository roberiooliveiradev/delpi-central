"""Shared fixtures — app, client, fake S2S validator, fake provider."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.create_app import create_app
from app.infrastructure import s2s_auth
from app.infrastructure.rate_limits import reset_rate_limiter


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return app.test_client()


class FakeValidator:
    """Test double for ``delpi_auth.ServiceTokenValidator``.

    ``outcome``: "ok" | "denied" | "invalid" | "unavailable" | "config"
    """

    def __init__(self, outcome: str = "ok", client_id: str = "supplies-api"):
        self._outcome = outcome
        self._client_id = client_id

    def validate(self, token, *, required_scopes=(), allowed_clients=None):
        from delpi_auth.service_errors import (
            ServiceAuthConfigError,
            ServiceClientDeniedError,
            ServiceTokenInvalidError,
            ServiceValidatorUnavailableError,
        )

        if self._outcome == "denied":
            raise ServiceClientDeniedError()
        if self._outcome == "invalid":
            raise ServiceTokenInvalidError()
        if self._outcome == "unavailable":
            raise ServiceValidatorUnavailableError()
        if self._outcome == "config":
            raise ServiceAuthConfigError()
        return SimpleNamespace(client_id=self._client_id, scopes=frozenset())


@pytest.fixture()
def s2s_ok(monkeypatch):
    monkeypatch.setattr(
        s2s_auth, "_shared_validator", FakeValidator("ok")
    )
    yield
    monkeypatch.setattr(s2s_auth, "_shared_validator", None)


@pytest.fixture()
def in_memory_limiter(monkeypatch):
    """Shared in-memory limiter resolved through the singleton."""
    from app.infrastructure.config.settings import Settings
    from app.infrastructure.rate_limits import rate_limiter

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "brasilapi")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "process_local")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED", True)
    reset_rate_limiter()
    yield rate_limiter()
    reset_rate_limiter()


class FakeTransportResponse:
    def __init__(self, status_code: int, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def fake_transport(status_code: int, payload=None, headers=None):
    def _transport(url, *, timeout):
        return FakeTransportResponse(status_code, payload, headers)

    return _transport


BRASILAPI_PAYLOAD = {
    "cnpj": "19131243000197",
    "razao_social": "OPEN KNOWLEDGE BRASIL",
    "nome_fantasia": "REDE PELO CONHECIMENTO LIVRE",
    "descricao_tipo_de_logradouro": "ALAMEDA",
    "logradouro": "FRANCA, 243",
    "numero": "243",
    "complemento": "APT 34",
    "bairro": "JARDIM PAULISTA",
    "cep": "01.422-000",
    "municipio": "SAO PAULO",
    "uf": "SP",
    "codigo_municipio_ibge": 3550308,
    "ddd_telefone_1": "1134567890",
    "ddd_telefone_2": None,
    "email": "fisc@example.test",
    "situacao_cadastral": 2,
    "descricao_situacao_cadastral": "ATIVA",
    "cnae_fiscal": 9430800,
    "cnae_fiscal_descricao": "Associacoes de defesa de direitos sociais",
    "natureza_juridica": "Associacao Privada",
    "data_inicio_atividade": "2013-10-03",
    "porte": "MICRO EMPRESA",
    "qsa": [{"nome_socio": "SOCIO EXEMPLO", "cnpj_cpf_do_socio": "***"}],
}
