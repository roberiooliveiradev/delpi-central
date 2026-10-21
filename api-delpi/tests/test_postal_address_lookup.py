"""Postal address lookup — domain, provider chain e adapters (INT-CEP-01)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
import requests

from app.application.use_cases.addresses.lookup_postal_address_use_case import (
    LookupPostalAddressUseCase,
)
from app.domain.addresses.postal_address import (
    PostalAddressProviderError,
    PostalAddressResult,
    normalize_postal_code,
)
from app.infrastructure.gateways.postal_address.postal_address_providers import (
    BrasilApiPostalAddressProvider,
    ViaCepPostalAddressProvider,
)


class _StubProvider:
    def __init__(self, name="stub", result=None, error=None):
        self.name = name
        self._result = result
        self._error = error
        self.calls: list[str] = []

    def lookup(self, digits):
        self.calls.append(digits)
        if self._error is not None:
            raise self._error
        return self._result


def _found(postal_code="01310100", source="stub", street="Rua X"):
    return PostalAddressResult(
        postal_code=postal_code,
        found=True,
        street=street,
        district="Centro",
        city="Cidade",
        state="SP",
        ibge_city_code="3550308",
        source=source,
        result_type="street" if street else "municipality",
    )


class TestNormalizePostalCode:
    def test_accepts_digits_and_mask(self):
        assert normalize_postal_code("01310100") == "01310100"
        assert normalize_postal_code("01310-100") == "01310100"
        assert normalize_postal_code("89120000") == "89120000"

    @pytest.mark.parametrize(
        "bad", ["", "123", "123456789", "abcdefgh", "01310-1000", None]
    )
    def test_rejects_wrong_shapes(self, bad):
        with pytest.raises(ValueError):
            normalize_postal_code(bad)


class TestLookupPostalAddressUseCase:
    def test_requires_at_least_one_provider(self):
        with pytest.raises(ValueError):
            LookupPostalAddressUseCase(providers=[])

    def test_first_provider_hit_short_circuits(self):
        a = _StubProvider(result=_found())
        b = _StubProvider(result=_found())
        out = LookupPostalAddressUseCase([a, b]).execute("01310-100")
        assert out.found is True
        assert a.calls == ["01310100"]
        assert b.calls == []

    def test_fallback_when_first_proves_not_found(self):
        """R4.1 regression — 89120000 absent in provider A, found in B."""
        a = _StubProvider(name="viacep", result=None)
        b = _StubProvider(
            name="brasilapi",
            result=_found(postal_code="89120000", source="brasilapi", street=None),
        )
        out = LookupPostalAddressUseCase([a, b]).execute("89120000")
        assert out.found is True
        assert out.source == "brasilapi"
        assert out.result_type == "municipality"
        assert a.calls == ["89120000"] and b.calls == ["89120000"]

    def test_fallback_when_first_fails_technically(self):
        a = _StubProvider(error=PostalAddressProviderError("viacep timeout"))
        b = _StubProvider(result=_found(source="brasilapi"))
        out = LookupPostalAddressUseCase([a, b]).execute("01310100")
        assert out.found is True
        assert b.calls == ["01310100"]

    def test_not_found_only_when_all_providers_prove_it(self):
        a = _StubProvider(result=None)
        b = _StubProvider(result=None)
        out = LookupPostalAddressUseCase([a, b]).execute("99999999")
        assert out.found is False
        assert out.postal_code == "99999999"

    def test_error_when_provider_failed_and_none_found(self):
        """Indisponibilidade nunca vira found=false."""
        a = _StubProvider(error=PostalAddressProviderError("down"))
        b = _StubProvider(result=None)
        with pytest.raises(PostalAddressProviderError):
            LookupPostalAddressUseCase([a, b]).execute("99999999")

    def test_error_when_all_providers_fail(self):
        a = _StubProvider(error=PostalAddressProviderError("down"))
        b = _StubProvider(error=PostalAddressProviderError("down too"))
        with pytest.raises(PostalAddressProviderError):
            LookupPostalAddressUseCase([a, b]).execute("01310100")

    def test_invalid_cep_rejected_before_any_provider(self):
        a = _StubProvider(result=_found())
        with pytest.raises(ValueError):
            LookupPostalAddressUseCase([a]).execute("123")
        assert a.calls == []


_VIACEP_FOUND = {
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "bairro": "Bela Vista",
    "localidade": "São Paulo",
    "uf": "sp",
    "ibge": "3550308",
}
_BRASILAPI_FOUND = {
    "cep": "89120000",
    "state": "SC",
    "city": "Timbó",
    "neighborhood": None,
    "street": None,
    "service": "open-cep",
    "ibge": {"city": "4218202", "state": "42"},
}


def _resp(status=200, payload=None):
    return SimpleNamespace(status_code=status, json=lambda: payload)


class TestViaCepAdapter:
    def test_maps_full_payload(self):
        p = ViaCepPostalAddressProvider(
            base_url="https://viacep.test/ws", timeout_seconds=1
        )
        with patch("requests.get", return_value=_resp(200, _VIACEP_FOUND)) as g:
            out = p.lookup("01310100")
        assert g.call_args.args[0] == "https://viacep.test/ws/01310100/json/"
        assert "User-Agent" in g.call_args.kwargs["headers"]
        assert g.call_args.kwargs["allow_redirects"] is False
        assert out.found and out.street == "Avenida Paulista"
        assert out.state == "SP" and out.ibge_city_code == "3550308"
        assert out.result_type == "street" and out.source == "viacep"

    def test_erro_flag_is_not_found(self):
        p = ViaCepPostalAddressProvider(
            base_url="https://viacep.test/ws", timeout_seconds=1
        )
        with patch(
            "requests.get", return_value=_resp(200, {"erro": "true"})
        ):
            assert p.lookup("99999999") is None

    def test_timeout_raises_provider_error(self):
        p = ViaCepPostalAddressProvider(
            base_url="https://viacep.test/ws", timeout_seconds=1
        )
        with patch(
            "requests.get", side_effect=requests.Timeout("slow")
        ):
            with pytest.raises(PostalAddressProviderError) as exc:
                p.lookup("01310100")
        assert exc.value.status_code is None

    def test_http_error_raises_provider_error(self):
        p = ViaCepPostalAddressProvider(
            base_url="https://viacep.test/ws", timeout_seconds=1
        )
        with patch("requests.get", return_value=_resp(500, {})):
            with pytest.raises(PostalAddressProviderError) as exc:
                p.lookup("01310100")
        assert exc.value.status_code == 500

    def test_invalid_json_raises_provider_error(self):
        p = ViaCepPostalAddressProvider(
            base_url="https://viacep.test/ws", timeout_seconds=1
        )
        bad = SimpleNamespace(
            status_code=200,
            json=lambda: (_ for _ in ()).throw(ValueError("no json")),
        )
        with patch("requests.get", return_value=bad):
            with pytest.raises(PostalAddressProviderError):
                p.lookup("01310100")


class TestBrasilApiAdapter:
    def test_maps_partial_municipality_payload(self):
        p = BrasilApiPostalAddressProvider(
            base_url="https://brasilapi.test/api/cep/v1", timeout_seconds=1
        )
        with patch("requests.get", return_value=_resp(200, _BRASILAPI_FOUND)) as g:
            out = p.lookup("89120000")
        assert g.call_args.args[0] == "https://brasilapi.test/api/cep/v1/89120000"
        assert "User-Agent" in g.call_args.kwargs["headers"]
        assert out.found and out.source == "brasilapi"
        assert out.city == "Timbó" and out.state == "SC"
        assert out.ibge_city_code == "4218202"
        assert out.street is None and out.district is None
        assert out.result_type == "municipality"

    def test_404_is_not_found(self):
        p = BrasilApiPostalAddressProvider(
            base_url="https://brasilapi.test/api/cep/v1", timeout_seconds=1
        )
        with patch("requests.get", return_value=_resp(404, {})):
            assert p.lookup("99999999") is None

    def test_payload_without_city_is_not_found(self):
        p = BrasilApiPostalAddressProvider(
            base_url="https://brasilapi.test/api/cep/v1", timeout_seconds=1
        )
        with patch("requests.get", return_value=_resp(200, {"erro": "true"})):
            assert p.lookup("99999999") is None
