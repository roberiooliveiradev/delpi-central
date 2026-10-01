"""C3 — bench-session resolve identidade oficial via Portal RH.

Cobre: nome oficial como única fonte, matrícula textual ("001"), bloqueios
(inativo/inexistente/indisponível/contrato inválido), alias legado
operatorCode, divergência de payload, ausência de persistência em erro,
autonomia de sessão já criada e lookup único.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.domain.errors import (
    OperatorDirectoryContractError,
    OperatorDirectoryUnavailable,
    OperatorInactive,
    OperatorNotFound,
)
from production_control_app.domain.operator_identity import OperatorIdentity
from production_control_app.interface.http.routes import (
    public_machine_load_routes as routes,
)

from tests.test_production_run_service import (
    FakeOperatorDirectory,
    FakePulse,
    FakeRepo,
    make_mes,
    make_service,
)


def _classify_open_downtime(downtimes) -> None:
    from datetime import datetime, timezone
    for e in downtimes.events:
        if e["ended_at"] is None:
            e["reason_code"] = "other"
            e["confirmed"] = True
            e["confirmed_at"] = datetime.now(timezone.utc)
            return
    raise AssertionError("expected an open downtime")


def _identity(reg: str, **kw) -> OperatorIdentity:
    return OperatorIdentity(
        external_id=kw.pop("external_id", 42),
        registration=reg,
        full_name=kw.pop("full_name", "ALESSANDRA GAVA ROCHA"),
        branch_code=kw.pop("branch_code", "02"),
        active=kw.pop("active", True),
    )


class DirectoryStub:
    """Directory port stub com resposta programável e contagem de chamadas."""

    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls: list[str] = []

    def find_by_registration(self, registration: str):
        self.calls.append(registration)
        if self.error is not None:
            raise self.error
        return self.result or _identity(registration)


class TestBenchSessionIdentityService:
    def _service(self, repo: FakeRepo, directory) -> tuple:
        service = make_service(repo, FakePulse(), operator_directory=directory)
        return service

    def test_valid_registration_persists_official_identity(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub(_identity("20057"))
        service = self._service(repo, directory)
        data = service.create_bench_session(
            branch="02", work_center="CT-123", registration="20057"
        )
        assert data["operatorCode"] == "20057"
        assert data["operatorName"] == "ALESSANDRA GAVA ROCHA"
        row = next(iter(repo.sessions.values()))
        assert row["operator_code"] == "20057"
        assert row["operator_name"] == "ALESSANDRA GAVA ROCHA"

    def test_leading_zeroes_preserved(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub(_identity("001"))
        service = self._service(repo, directory)
        data = service.create_bench_session(
            branch="01", work_center="CT01", registration="001"
        )
        assert directory.calls == ["001"]
        assert data["operatorCode"] == "001"
        assert next(iter(repo.sessions.values()))["operator_code"] == "001"

    def test_single_lookup_per_creation(self) -> None:
        directory = DirectoryStub()
        service = self._service(FakeRepo(), directory)
        service.create_bench_session(
            branch="01", work_center="CT01", registration="20057"
        )
        assert len(directory.calls) == 1

    def test_inactive_blocks_and_persists_nothing(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub(_identity("20057", active=False))
        service = self._service(repo, directory)
        with pytest.raises(OperatorInactive):
            service.create_bench_session(
                branch="01", work_center="CT01", registration="20057"
            )
        assert not repo.sessions

    def test_not_found_blocks_and_persists_nothing(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub(error=OperatorNotFound("não encontrada"))
        service = self._service(repo, directory)
        with pytest.raises(OperatorNotFound):
            service.create_bench_session(
                branch="01", work_center="CT01", registration="99999"
            )
        assert not repo.sessions

    def test_unavailable_blocks_and_persists_nothing(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub(
            error=OperatorDirectoryUnavailable("indisponível")
        )
        service = self._service(repo, directory)
        with pytest.raises(OperatorDirectoryUnavailable):
            service.create_bench_session(
                branch="01", work_center="CT01", registration="20057"
            )
        assert not repo.sessions

    def test_contract_error_blocks_and_persists_nothing(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub(
            error=OperatorDirectoryContractError("contrato inválido")
        )
        service = self._service(repo, directory)
        with pytest.raises(OperatorDirectoryContractError):
            service.create_bench_session(
                branch="01", work_center="CT01", registration="20057"
            )
        assert not repo.sessions

    def test_different_branch_does_not_block(self) -> None:
        """Filial do colaborador != filial do cockpit: permitido nesta etapa."""
        repo = FakeRepo()
        directory = DirectoryStub(_identity("20057", branch_code="01"))
        service = self._service(repo, directory)
        data = service.create_bench_session(
            branch="02", work_center="CT-9", registration="20057"
        )
        assert data["operatorName"] == "ALESSANDRA GAVA ROCHA"

    def test_existing_session_operates_with_directory_offline(self) -> None:
        """Sessão criada segue autônoma: Pause/Resume/Stop sem novo lookup."""
        repo = FakeRepo()
        device = {
            "deviceId": "dev-1", "counter": 100, "counterEpoch": 1,
            "online": True,
        }
        pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
        directory = DirectoryStub(_identity("20057"))
        mes, _states, downtimes = make_mes()
        service = make_service(
            repo, pulse, operator_directory=directory, mes_lifecycle=mes
        )
        session = service.create_bench_session(
            branch="01", work_center="CT01", registration="20057"
        )["sessionToken"]
        directory.error = OperatorDirectoryUnavailable("offline")
        directory.calls.clear()
        run = service.start_run(
            branch="01", work_center="CT01",
            production_order="OP1", operation_code="10",
            session_token=session,
        )
        service.pause_run(run["id"], session_token=session)
        _classify_open_downtime(downtimes)
        service.resume_run(run["id"], session_token=session)
        service.stop_run(run["id"], session_token=session)
        assert directory.calls == []


class _CockpitOK:
    def is_valid_token(self, token) -> bool:
        return token == "tok"


class _BranchOK:
    def assert_valid_branch(self, branch: str) -> str:
        return branch


def _client(repo: FakeRepo, directory) -> TestClient:
    from production_control_app.application.services.operator_directory_service import (  # noqa: E501
        OperatorDirectoryService,
    )
    # Serviço real por cima do stub → validação de matrícula (vazia/>30) aplica.
    service = make_service(
        repo, FakePulse(), operator_directory=OperatorDirectoryService(directory)
    )
    app = FastAPI()
    app.include_router(routes.router)
    monkey_app = app
    routes.build_production_run_service = lambda *a, **kw: service  # type: ignore[assignment]
    routes.build_public_cockpit_access_service = lambda: _CockpitOK()  # type: ignore[assignment]
    routes.build_branch_access_service = lambda: _BranchOK()  # type: ignore[assignment]
    return TestClient(monkey_app)


def _post(api: TestClient, payload: dict):
    return api.post("/public/machine-load/tok/bench-sessions", json=payload)


class TestBenchSessionEndpoint:
    def test_registration_canonical_creates_session(self) -> None:
        repo = FakeRepo()
        api = _client(repo, DirectoryStub(_identity("20057")))
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-123", "registration": "20057",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["operatorCode"] == "20057"
        assert data["operatorName"] == "ALESSANDRA GAVA ROCHA"

    def test_legacy_operator_code_alias(self) -> None:
        repo = FakeRepo()
        api = _client(repo, DirectoryStub(_identity("20057")))
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-123",
            "operatorCode": "20057", "operatorName": "Batman",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["operatorName"] == "ALESSANDRA GAVA ROCHA"
        assert next(iter(repo.sessions.values()))["operator_name"] == (
            "ALESSANDRA GAVA ROCHA"
        )

    def test_same_registration_and_operator_code_accepted(self) -> None:
        api = _client(FakeRepo(), DirectoryStub())
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-1",
            "registration": "20057", "operatorCode": "20057",
        })
        assert resp.status_code == 200

    def test_divergent_registration_and_operator_code_rejected(self) -> None:
        repo = FakeRepo()
        api = _client(repo, DirectoryStub())
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-1",
            "registration": "001", "operatorCode": "20057",
        })
        assert resp.status_code == 422
        assert not repo.sessions

    @pytest.mark.parametrize(
        "payload",
        [
            {"branch": "02", "workCenter": "CT-1"},
            {"branch": "02", "workCenter": "CT-1", "registration": "   "},
            {"branch": "02", "workCenter": "CT-1", "registration": "x" * 31},
        ],
    )
    def test_missing_or_invalid_registration_rejected(self, payload) -> None:
        repo = FakeRepo()
        api = _client(repo, DirectoryStub())
        assert _post(api, payload).status_code == 422
        assert not repo.sessions

    def test_not_found_maps_404(self) -> None:
        repo = FakeRepo()
        api = _client(repo, DirectoryStub(error=OperatorNotFound("nf")))
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-1", "registration": "99999",
        })
        assert resp.status_code == 404
        assert "Matrícula não encontrada" in resp.text
        assert not repo.sessions

    def test_inactive_maps_403(self) -> None:
        repo = FakeRepo()
        api = _client(repo, DirectoryStub(_identity("20057", active=False)))
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-1", "registration": "20057",
        })
        assert resp.status_code == 403
        assert "não está ativa" in resp.text
        assert not repo.sessions

    @pytest.mark.parametrize(
        "error",
        [
            OperatorDirectoryUnavailable("down"),
            OperatorDirectoryUnavailable("auth", status_code=401),
            OperatorDirectoryContractError("bad payload"),
        ],
    )
    def test_directory_errors_map_503(self, error) -> None:
        repo = FakeRepo()
        api = _client(repo, DirectoryStub(error=error))
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-1", "registration": "20057",
        })
        assert resp.status_code == 503
        assert "token" not in resp.text.lower()
        assert not repo.sessions

    def test_zeroes_through_endpoint(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub(_identity("001"))
        api = _client(repo, directory)
        resp = _post(api, {
            "branch": "01", "workCenter": "CT-1", "registration": "001",
        })
        assert resp.status_code == 200
        assert directory.calls == ["001"]
        assert next(iter(repo.sessions.values()))["operator_code"] == "001"

    def test_honeypot_short_circuits(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub()
        api = _client(repo, directory)
        resp = _post(api, {
            "branch": "02", "workCenter": "CT-1",
            "registration": "20057", "website": "spam",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["sessionToken"] is None
        assert directory.calls == []
        assert not repo.sessions


class TestCurrentBenchSession:
    """C4 — GET /bench-sessions/current: restore sem consultar o RH."""

    def _service_with_session(self, repo: FakeRepo):
        service = make_service(repo, FakePulse())
        created = service.create_bench_session(
            branch="01", work_center="CT01", registration="20057"
        )
        return service, created["sessionToken"]

    def test_valid_session_returns_snapshot(self) -> None:
        repo = FakeRepo()
        service, token = self._service_with_session(repo)
        data = service.get_current_bench_session(token)
        assert data["sessionToken"] == token
        assert data["operatorCode"] == "20057"
        assert data["operatorName"] == "Operador"
        assert data["branch"] == "01"
        assert data["workCenter"] == "CT01"
        assert data["expiresAt"] is not None

    @pytest.mark.parametrize("bad", [None, "", "   ", "token-inexistente"])
    def test_invalid_tokens_raise_auth(self, bad) -> None:
        from production_control_app.domain.errors import BenchSessionRequired

        repo = FakeRepo()
        service, _ = self._service_with_session(repo)
        with pytest.raises(BenchSessionRequired):
            service.get_current_bench_session(bad)

    def test_ended_session_raises_auth(self) -> None:
        from production_control_app.domain.errors import BenchSessionRequired

        repo = FakeRepo()
        service, token = self._service_with_session(repo)
        service.end_bench_session(token)
        with pytest.raises(BenchSessionRequired):
            service.get_current_bench_session(token)

    def test_expired_session_raises_auth(self) -> None:
        from production_control_app.domain.errors import BenchSessionRequired

        repo = FakeRepo()
        service, token = self._service_with_session(repo)
        row = next(iter(repo.sessions.values()))
        from datetime import datetime, timedelta, timezone
        row["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(BenchSessionRequired):
            service.get_current_bench_session(token)

    def test_current_session_does_not_call_directory(self) -> None:
        repo = FakeRepo()
        directory = DirectoryStub()
        service = make_service(repo, FakePulse(), operator_directory=directory)
        token = service.create_bench_session(
            branch="01", work_center="CT01", registration="20057"
        )["sessionToken"]
        directory.error = OperatorDirectoryUnavailable("offline")
        directory.calls.clear()
        data = service.get_current_bench_session(token)
        assert data["operatorName"] == "ALESSANDRA GAVA ROCHA"
        assert directory.calls == []
