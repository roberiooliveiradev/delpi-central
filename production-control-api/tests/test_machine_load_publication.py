"""E1 — fundação WORKING x PUBLISHED: generation_id + machine_load_publications."""

from __future__ import annotations

import copy
import json
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Any

import pytest

from production_control_app.infrastructure.persistence import (
    postgres_machine_load_publication_repository as publication_module,
)
from production_control_app.infrastructure.persistence.machine_load_snapshot_row_cache import (
    PUBLISHED_NAMESPACE,
    clear_snapshot_row_cache,
)
from production_control_app.infrastructure.persistence.postgres_machine_load_publication_repository import (
    PostgresMachineLoadPublicationRepository,
)
from tests.test_machine_load import (
    FULL_PERMS,
    FakeGateway,
    FakeSnapshotRepo,
    _service,
    _user,
)


def _is_uuid(value: Any) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


# --- geração no WORKING --------------------------------------------------------


def test_seed_snapshot_carries_a_valid_generation() -> None:
    snapshots = FakeSnapshotRepo()
    _service(FakeGateway(), snapshots).build(_user(*FULL_PERMS), branch="01")
    assert _is_uuid(snapshots.rows["01"]["generation_id"])


def test_every_refresh_opens_a_new_generation() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    first = snapshots.rows["01"]["generation_id"]

    service.refresh(_user(*FULL_PERMS), branch="01")
    second = snapshots.rows["01"]["generation_id"]
    service.refresh(_user(*FULL_PERMS), branch="01")
    third = snapshots.rows["01"]["generation_id"]

    assert _is_uuid(first) and _is_uuid(second) and _is_uuid(third)
    assert len({first, second, third}) == 3


def test_manual_mutation_keeps_the_same_generation() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    generation = snapshots.rows["01"]["generation_id"]

    service.reorder_sequence(
        _user(*FULL_PERMS),
        branch="01",
        work_center="CT-01A",
        ordered_keys=[{"production_order": "24640401002", "operation_code": "03"}],
    )

    assert snapshots.payload_updates == 1
    assert snapshots.rows["01"]["generation_id"] == generation


# --- repositório PUBLISHED ------------------------------------------------------


class FakePublicationsDb:
    """Tabela em memória com a mesma cara da tupla real (UNIQUE branch + upsert)."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.writes = 0
        self.probes = 0
        self.full_reads = 0
        self._clock = 0

    @contextmanager
    def connection(self):
        yield self

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def commit(self) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...]) -> None:
        self._result = None
        if "INSERT INTO" in query:
            (
                branch,
                generation_id,
                start_date,
                end_date,
                payload_text,
                schema_version,
                source,
                source_refreshed_at,
                source_refreshed_by,
                published_by,
            ) = params
            self._clock += 1
            self.writes += 1
            row = {
                "id": f"pub-{self._clock}",
                "branch": branch,
                "generation_id": generation_id,
                "start_date": start_date,
                "end_date": end_date,
                "payload_json": json.loads(payload_text),
                "schema_version": schema_version,
                "source": source,
                "source_refreshed_at": source_refreshed_at,
                "source_refreshed_by": source_refreshed_by,
                "published_at": datetime(2026, 9, 20, 12, self._clock, tzinfo=timezone.utc),
                "published_by": published_by,
            }
            # xmin muda a cada UPDATE — emula a versão da tupla.
            row["row_version"] = str(self._clock)
            self.rows[branch] = row
            # Postgres devolve a linha desserializada: nunca a mesma referência
            # do JSON armazenado.
            self._result = copy.deepcopy(row)
            return
        if "UPDATE" in query:
            payload_text, branch = params
            row = self.rows[str(branch)]
            self._clock += 1
            self.writes += 1
            # Só o conteúdo muda: generation_id e published_* são da publicação original.
            row = {
                **row,
                "payload_json": json.loads(payload_text),
                "row_version": str(self._clock),
            }
            self.rows[str(branch)] = row
            self._result = copy.deepcopy(row)
            return
        branch = str(params[0])
        row = self.rows.get(branch)
        if "payload_json" not in query:
            self.probes += 1
        else:
            self.full_reads += 1
        if row is None:
            self._result = None
        elif "payload_json" not in query:
            # Probe barato do get(): só a versão da tupla, sem o JSONB pesado.
            self._result = {"row_version": row["row_version"]}
        else:
            self._result = copy.deepcopy(row)

    def fetchone(self) -> dict[str, Any] | None:
        return self._result


@pytest.fixture
def publications_db(monkeypatch: pytest.MonkeyPatch) -> FakePublicationsDb:
    # O cache de linha é module-level: cada teste começa sem linhas materializadas.
    clear_snapshot_row_cache(namespace=PUBLISHED_NAMESPACE)
    db = FakePublicationsDb()
    monkeypatch.setattr(publication_module, "get_connection", db.connection)
    return db


def _publish(repo: PostgresMachineLoadPublicationRepository, branch: str, generation: str, payload: dict[str, Any]) -> dict[str, Any]:
    return repo.upsert(
        branch=branch,
        generation_id=generation,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        payload=payload,
        source_refreshed_at=datetime(2026, 9, 19, 10, tzinfo=timezone.utc),
        source_refreshed_by="pcp",
        published_by="pcp",
    )


def test_publication_roundtrip_keeps_payload_and_metadata(
    publications_db: FakePublicationsDb,
) -> None:
    repo = PostgresMachineLoadPublicationRepository()
    generation = str(uuid.uuid4())
    _publish(repo, "01", generation, {"operations": [{"work_center": "CT-12"}]})

    row = repo.get(branch="01")

    assert row is not None
    assert row["generation_id"] == generation
    assert row["payload_json"]["operations"][0]["work_center"] == "CT-12"
    # Fatos distintos: refresh da origem x instante da publicação.
    assert row["source_refreshed_at"] == datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    assert row["published_at"] is not None
    assert row["published_by"] == "pcp"
    assert row["source_refreshed_by"] == "pcp"


def test_publication_is_a_single_row_per_branch(
    publications_db: FakePublicationsDb,
) -> None:
    repo = PostgresMachineLoadPublicationRepository()
    _publish(repo, "01", str(uuid.uuid4()), {"operations": []})
    second_generation = str(uuid.uuid4())
    row = _publish(repo, "01", second_generation, {"operations": [{"n": 1}]})

    assert set(publications_db.rows) == {"01"}
    assert row["generation_id"] == second_generation


def test_refresh_does_not_touch_the_published_queue(
    publications_db: FakePublicationsDb,
) -> None:
    snapshots = FakeSnapshotRepo()
    publications = PostgresMachineLoadPublicationRepository()
    service = _service(FakeGateway(), snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    generation_a = snapshots.rows["01"]["generation_id"]
    _publish(publications, "01", generation_a, {"operations": [{"work_center": "CT-12"}]})

    service.refresh(_user(*FULL_PERMS), branch="01")

    working = snapshots.get(branch="01")
    published = publications.get(branch="01")
    assert working["generation_id"] != generation_a
    assert published["generation_id"] == generation_a
    assert published["payload_json"] == {"operations": [{"work_center": "CT-12"}]}


def test_working_payload_change_does_not_leak_into_publication(
    publications_db: FakePublicationsDb,
) -> None:
    repo = PostgresMachineLoadPublicationRepository()
    published = _publish(repo, "01", str(uuid.uuid4()), {"operations": [{"qty": 7}]})

    # O JSON gravado é uma cópia serializada: mutar o dict retornado não toca
    # o payload durável. O cache de linha compartilha referência por desempenho
    # (mesma convenção do WORKING), então simulamos um novo ciclo de leitura.
    published["payload_json"]["operations"][0]["qty"] = 999

    clear_snapshot_row_cache(namespace=PUBLISHED_NAMESPACE)
    fresh = repo.get(branch="01")
    assert fresh["payload_json"]["operations"][0]["qty"] == 7


def test_publications_are_isolated_per_branch(
    publications_db: FakePublicationsDb,
) -> None:
    repo = PostgresMachineLoadPublicationRepository()
    generation_01 = str(uuid.uuid4())
    _publish(repo, "01", generation_01, {"operations": [{"work_center": "CT-12"}]})

    assert repo.get(branch="02") is None
    assert repo.get(branch="01")["generation_id"] == generation_01


# --- E2 — fronteira de leitura WORKING x PUBLISHED ------------------------------
#
# Regra: PCP lê WORKING; cockpit/chão de fábrica lê PUBLISHED. O teste monta
# duas gerações divergentes e prova que cada consumidor enxerga a sua.

from production_control_app.application.services.machine_load_service import (
    MachineLoadService,
)
from production_control_app.domain.errors import SnapshotNotFound
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)
from tests.test_machine_load import (
    _OPERATION,
    _WORK_CENTERS,
    _machine_load_client,
    FakePublicationRepo,
    RecordingNotifier,
)


def _queue_payload(operations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "work_centers": _WORK_CENTERS,
        "operations": operations,
        "summary": {
            "work_center_count": len(_WORK_CENTERS),
            "operation_count": len(operations),
        },
    }


def _upsert_working(
    snapshots: FakeSnapshotRepo, operations: list[dict[str, Any]], branch: str = "01"
) -> None:
    snapshots.upsert(
        branch=branch,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        payload=_queue_payload(operations),
        refreshed_by="planner-1",
        generation_id=str(uuid.uuid4()),
    )


def _op(
    order: str,
    code: str,
    work_center: str = "CT-01A",
    **extra: Any,
) -> dict[str, Any]:
    return {
        **_OPERATION,
        "work_center": work_center,
        "production_order": order,
        "operation_code": code,
        **extra,
    }


def _divergent_service() -> tuple[MachineLoadService, FakeSnapshotRepo]:
    """WORKING B (OP-B/CT-02) x PUBLISHED A (OP-A/CT-01A) — draft não publicado."""
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01", pa_product_code="90262910",
                                  product_code="50320064", resource="R-A",
                                  pending_qty=5.0, produced_qty=1.0,
                                  pieces_conversion_factor=1000.0)])
    snapshots.publish("01")
    _upsert_working(snapshots, [_op("24640401003", "01", work_center="CT-02",
                                    pa_product_code="PA-DRAFT",
                                    product_code="PROD-DRAFT", resource="R-B")])
    return _service(FakeGateway(), snapshots), snapshots


def test_pcp_reads_working_and_cockpit_reads_published() -> None:
    service, _snapshots = _divergent_service()

    pcp = service.build(_user(*FULL_PERMS), branch="01", work_center="CT-02")
    cockpit = service.build_public(branch="01", work_center="CT-01A")

    assert [i["production_order"] for i in pcp["selected"]["items"]] == ["24640401003"]
    assert [i["production_order"] for i in cockpit["selected"]["items"]] == [
        "24640401002"
    ]


def test_refresh_moves_working_and_keeps_cockpit_on_published() -> None:
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    snapshots.publish("01")
    generation_a = snapshots.published["01"]["generation_id"]

    service.refresh(_user(*FULL_PERMS), branch="01")

    assert snapshots.rows["01"]["generation_id"] != generation_a
    assert snapshots.published["01"]["generation_id"] == generation_a
    # Polling repetido do cockpit continua vendo a mesma fila publicada.
    for _ in range(3):
        cockpit = service.build_public(branch="01", work_center="CT-02")
        assert cockpit["selected"]["items"]


def test_public_reads_fail_when_no_publication_exists() -> None:
    """Filial só com WORKING: cockpit recebe erro controlado, nunca o draft."""
    snapshots = FakeSnapshotRepo()
    service = _service(FakeGateway(), snapshots)
    _upsert_working(snapshots, [_op("24640401002", "01")])

    with pytest.raises(SnapshotNotFound, match="ainda não foi enviada pelo PCP"):
        service.build_public(branch="01", work_center="CT-01A")
    with pytest.raises(SnapshotNotFound):
        service.public_snapshot_contains_operation(
            branch="01", production_order="24640401002", operation_code="01"
        )


def test_public_lookups_follow_published_not_working() -> None:
    service, _snapshots = _divergent_service()

    # OP-A só existe no PUBLISHED; OP-B só existe no WORKING draft.
    assert service.public_snapshot_contains_operation(
        branch="01", production_order="24640401002", operation_code="01"
    ) is True
    assert service.public_snapshot_contains_operation(
        branch="01", production_order="24640401003", operation_code="01"
    ) is False
    assert service.public_snapshot_contains_pa(branch="01", pa_code="90262910") is True
    assert service.public_snapshot_contains_pa(branch="01", pa_code="PA-DRAFT") is False
    assert service.public_snapshot_contains_product(
        branch="01", product_code="50320064"
    ) is True
    assert service.public_snapshot_contains_product(
        branch="01", product_code="PROD-DRAFT"
    ) is False

    # Recursos do CT: WORKING B moveu a operação para CT-02; a bancada segue em A.
    assert service.public_snapshot_work_center_resources(
        branch="01", work_center="CT-01A"
    ) == ("R-A",)
    assert (
        service.public_snapshot_work_center_resources(branch="01", work_center="CT-02")
        is None
    )


def test_public_run_context_uses_published_queue() -> None:
    service, _snapshots = _divergent_service()

    context = service.public_operation_run_context(
        branch="01", production_order="24640401002", operation_code="01"
    )

    assert context is not None
    assert context["pending_qty"] == 5.0
    assert context["pieces_conversion_factor"] == 1000.0


def test_published_only_operation_remains_startable_by_cockpit() -> None:
    """E2/L-A: OP saiu do WORKING B, mas continua no PUBLISHED → run válido."""
    service, _snapshots = _divergent_service()

    context = service.public_operation_run_context(
        branch="01", production_order="24640401002", operation_code="01"
    )

    assert context is not None


def test_draft_only_operation_cannot_start_a_run() -> None:
    """E2/L-B: OP só existe no draft WORKING B → cockpit não pode iniciar run."""
    service, _snapshots = _divergent_service()

    assert (
        service.public_operation_run_context(
            branch="01", production_order="24640401003", operation_code="01"
        )
        is None
    )


def test_publications_are_isolated_between_branches() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")], branch="01")
    _upsert_working(snapshots, [_op("24640401099", "01")], branch="02")
    snapshots.publish("02")
    _upsert_working(snapshots, [_op("24640401088", "01")], branch="02")
    service = _service(FakeGateway(), snapshots)

    # Branch 01 sem publicação: draft não vaza. Branch 02: cockpit no A.
    with pytest.raises(SnapshotNotFound):
        service.build_public(branch="01", work_center="CT-01A")
    cockpit_02 = service.build_public(branch="02", work_center="CT-01A")
    assert [i["production_order"] for i in cockpit_02["selected"]["items"]] == [
        "24640401099"
    ]


def test_publication_get_reuses_cached_row_until_upsert(
    publications_db: FakePublicationsDb,
) -> None:
    """Polling do cockpit: probe de xmin barato, JSONB só quando a linha muda."""
    repo = PostgresMachineLoadPublicationRepository()
    _publish(repo, "01", str(uuid.uuid4()), {"operations": []})

    # Simula um novo ciclo de vida (o RETURNING do upsert já aqueceu o cache).
    clear_snapshot_row_cache("01", namespace=PUBLISHED_NAMESPACE)

    repo.get(branch="01")
    repo.get(branch="01")
    repo.get(branch="01")

    # 3 leituras → 1 fetch do JSONB + probes de versão; o payload nunca volta.
    assert publications_db.full_reads == 1
    assert publications_db.probes == 3

    new_generation = str(uuid.uuid4())
    _publish(repo, "01", new_generation, {"operations": [{"n": 2}]})

    # xmin mudou no write → o get rebusca e materializa a linha nova.
    assert repo.get(branch="01")["generation_id"] == new_generation
    assert publications_db.full_reads == 1

    # Cache frio após o write: a linha volta com a nova versão.
    clear_snapshot_row_cache("01", namespace=PUBLISHED_NAMESPACE)
    assert repo.get(branch="01")["generation_id"] == new_generation
    assert publications_db.full_reads == 2


def test_working_and_published_caches_do_not_mix(
    publications_db: FakePublicationsDb,
) -> None:
    """Mesmo branch nos dois namespaces: cada fila tem seu próprio cache."""
    from production_control_app.infrastructure.persistence.machine_load_snapshot_row_cache import (
        WORKING_NAMESPACE,
        get_snapshot_row_cache,
        put_snapshot_row_cache,
    )

    put_snapshot_row_cache(
        "01", row_version="w1", row={"origin": "working"}, namespace=WORKING_NAMESPACE
    )
    put_snapshot_row_cache(
        "01",
        row_version="p1",
        row={"origin": "published"},
        namespace=PUBLISHED_NAMESPACE,
    )

    assert get_snapshot_row_cache("01", row_version="w1", namespace=WORKING_NAMESPACE)[
        "origin"
    ] == "working"
    assert get_snapshot_row_cache(
        "01", row_version="p1", namespace=PUBLISHED_NAMESPACE
    )["origin"] == "published"
    clear_snapshot_row_cache("01", namespace=WORKING_NAMESPACE)
    assert (
        get_snapshot_row_cache("01", row_version="p1", namespace=PUBLISHED_NAMESPACE)
        is not None
    )


# --- E3 — «Enviar para máquinas»: publicação explícita e transacional -----------


def _publish_service(
    snapshots: FakeSnapshotRepo,
    notifier: RecordingNotifier | None = None,
    publications: FakePublicationRepo | None = None,
) -> MachineLoadService:
    return MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=publications or FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        change_notifier=notifier,
    )


def test_publish_promotes_working_to_published() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401003", "01", work_center="CT-02")])
    snapshots.published["01"] = {
        **copy.deepcopy(snapshots.rows["01"]),
        "generation_id": str(uuid.uuid4()),  # geração A — anterior ao WORKING B
        "source_refreshed_at": datetime(2026, 9, 19, 10, tzinfo=timezone.utc),
        "published_at": datetime(2026, 9, 19, 10, 30, tzinfo=timezone.utc),
        "published_by": "pcp-antigo",
    }
    notifier = RecordingNotifier()
    publications = FakePublicationRepo(snapshots.published)
    service = _publish_service(snapshots, notifier, publications)
    working_gen = snapshots.rows["01"]["generation_id"]

    result = service.publish(_user(*FULL_PERMS), branch="01")

    publication = result["publication"]
    assert publication["changed"] is True
    assert publication["generation_id"] == working_gen
    assert publication["published_by"] == "user-1"
    published = publications.get(branch="01")
    assert published["generation_id"] == working_gen
    assert published["payload_json"] == snapshots.rows["01"]["payload_json"]
    # Fatos distintos: refresh da origem preservado; publicação é instante novo.
    assert published["source_refreshed_at"] == snapshots.rows["01"]["refreshed_at"]
    assert published["published_at"] is not None
    assert notifier.events == [{"branch": "01", "reason": "publish", "work_center": None}]


def test_cockpit_switches_to_published_queue_after_publish() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")])
    snapshots.publish("01")
    _upsert_working(snapshots, [_op("24640401003", "01")])
    service = _publish_service(snapshots)

    assert [
        i["production_order"]
        for i in service.build_public(branch="01", work_center="CT-01A")["selected"]["items"]
    ] == ["24640401002"]

    service.publish(_user(*FULL_PERMS), branch="01")

    assert [
        i["production_order"]
        for i in service.build_public(branch="01", work_center="CT-01A")["selected"]["items"]
    ] == ["24640401003"]


def test_first_publish_creates_the_publication() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")])
    service = _publish_service(snapshots)

    with pytest.raises(SnapshotNotFound):
        service.build_public(branch="01", work_center="CT-01A")

    result = service.publish(_user(*FULL_PERMS), branch="01")

    assert result["publication"]["changed"] is True
    cockpit = service.build_public(branch="01", work_center="CT-01A")
    assert [i["production_order"] for i in cockpit["selected"]["items"]] == [
        "24640401002"
    ]


def test_publish_without_working_fails() -> None:
    service = _publish_service(FakeSnapshotRepo())

    with pytest.raises(SnapshotNotFound, match="enviar às máquinas"):
        service.publish(_user(*FULL_PERMS), branch="01")


def test_republish_same_generation_is_idempotent() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")])
    snapshots.publish("01")
    notifier = RecordingNotifier()
    publications = FakePublicationRepo(snapshots.published)
    service = _publish_service(snapshots, notifier, publications)
    before = publications.get(branch="01")

    result = service.publish(_user(*FULL_PERMS), branch="01")

    assert result["publication"]["changed"] is False
    assert publications.upserts == 0
    after = publications.get(branch="01")
    assert after["published_at"] == before["published_at"]
    assert after["published_by"] == before["published_by"]
    assert notifier.events == []


def test_publish_reads_working_under_row_lock() -> None:
    """A publicação captura WORKING via get_for_update (serialização no Postgres)."""
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")])
    service = _publish_service(snapshots)

    service.publish(_user(*FULL_PERMS), branch="01")

    assert snapshots.for_update_reads == 1


class _ExplodingPublications(FakePublicationRepo):
    def upsert(self, conn: Any = None, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("banco fora do ar")


def test_failed_publish_rolls_back_and_never_notifies() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")])
    snapshots.publish("01")
    _upsert_working(snapshots, [_op("24640401003", "01")])
    publications = _ExplodingPublications(snapshots.published)
    notifier = RecordingNotifier()
    service = _publish_service(snapshots, notifier, publications)
    working_before = copy.deepcopy(snapshots.rows["01"])

    with pytest.raises(RuntimeError):
        service.publish(_user(*FULL_PERMS), branch="01")

    assert snapshots.rows["01"] == working_before
    assert snapshots.published["01"]["generation_id"] != working_before["generation_id"]
    assert notifier.events == []


def test_refresh_after_publish_reopens_draft() -> None:
    snapshots = FakeSnapshotRepo()
    service = _publish_service(snapshots)
    service.build(_user(*FULL_PERMS), branch="01")
    service.publish(_user(*FULL_PERMS), branch="01")
    generation_b = snapshots.published["01"]["generation_id"]

    service.refresh(_user(*FULL_PERMS), branch="01")

    assert snapshots.rows["01"]["generation_id"] != generation_b
    assert snapshots.published["01"]["generation_id"] == generation_b


def test_publish_does_not_touch_other_branch() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")], branch="01")
    _upsert_working(snapshots, [_op("24640401099", "01")], branch="02")
    snapshots.publish("02")
    service = _publish_service(snapshots)
    published_02 = copy.deepcopy(snapshots.published["02"])

    service.publish(_user(*FULL_PERMS), branch="01")

    assert snapshots.published["02"] == published_02


def test_publish_route_returns_publication_metadata() -> None:
    snapshots = FakeSnapshotRepo()
    _upsert_working(snapshots, [_op("24640401002", "01")])
    service = _publish_service(snapshots)
    client = _machine_load_client(service)

    response = client.post("/machine-load/publish?branch=01")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Carga máquina enviada para as máquinas."
    assert body["data"]["publication"]["changed"] is True
    assert body["data"]["publication"]["generation_id"]

    # Republicação idempotente pelo HTTP também.
    again = client.post("/machine-load/publish?branch=01")
    assert again.json()["message"] == "A carga máquina atual já está enviada para as máquinas."
    assert again.json()["data"]["publication"]["changed"] is False


# ---------------------------------------------------------------------------
# E4 — mutações PCP transacionais: LIVE dual-write / DRAFT working-only
# ---------------------------------------------------------------------------

E4_GENERATION = "gen-e4-1"


def _e4_queue() -> list[dict[str, Any]]:
    """CT-01A: A,B,conjunto 108404 | CT-02: conjunto 108404 (2ª op)."""
    return [
        _op("99900001001", "01", work_center="CT-01A", due_date="2026-09-30"),
        _op("88800001001", "02", work_center="CT-01A", due_date="2026-08-21"),
        _op("10840401003", "03", work_center="CT-01A", due_date=None, pa_due_date=None),
        _op("10840402001", "05", work_center="CT-02", due_date="2026-08-25"),
    ]


def _e4_seed(snapshots: FakeSnapshotRepo, generation: str = E4_GENERATION) -> None:
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 3),
        payload=_queue_payload(_e4_queue()),
        refreshed_by="seed",
        generation_id=generation,
    )


def _e4_setup(
    *,
    live: bool,
    notifier: RecordingNotifier | None = None,
    publications: FakePublicationRepo | None = None,
) -> tuple[MachineLoadService, FakeSnapshotRepo]:
    """LIVE: publish copia a mesma geração. DRAFT: WORKING nova geração."""
    snapshots = FakeSnapshotRepo()
    _e4_seed(snapshots)
    snapshots.publish("01")
    if not live:
        snapshots.upsert(
            branch="01",
            start_date=date(2026, 8, 19),
            end_date=date(2026, 9, 3),
            payload=_queue_payload(_e4_queue()),
            refreshed_by="seed",
            generation_id="gen-e4-2",
        )
    service = _publish_service(snapshots, notifier=notifier, publications=publications)
    return service, snapshots


def _e4_mutate(service: MachineLoadService, mutation: str) -> dict[str, Any]:
    user = _user(*FULL_PERMS)
    if mutation == "reorder":
        return service.reorder_sequence(
            user,
            branch="01",
            work_center="CT-01A",
            ordered_keys=[
                {"production_order": "10840401003", "operation_code": "03"},
                {"production_order": "88800001001", "operation_code": "02"},
                {"production_order": "99900001001", "operation_code": "01"},
            ],
        )
    if mutation == "prioritize":
        return service.prioritize_conjunto(user, branch="01", order_number="108404")
    if mutation == "optimize":
        return service.optimize_delivery_sequence(user, branch="01")
    if mutation == "withdraw":
        return service.withdraw_conjunto(user, branch="01", order_number="108404")
    if mutation == "restore":
        service.withdraw_conjunto(user, branch="01", order_number="108404")
        return service.restore_conjunto(user, branch="01", order_number="108404")
    if mutation == "transfer_op":
        return service.transfer_operation(
            user,
            branch="01",
            production_order="10840401003",
            operation_code="03",
            target_work_center="CT-02",
        )
    if mutation == "transfer_conjunto":
        return service.transfer_conjunto(
            user,
            branch="01",
            order_number="108404",
            source_work_center="CT-01A",
            target_work_center="CT-02",
        )
    raise AssertionError(f"Mutação desconhecida: {mutation}")


_E4_CASES = [
    ("reorder", "sequence"),
    ("prioritize", "priority"),
    ("optimize", "delivery_sequence"),
    ("withdraw", "withdrawal"),
    ("restore", "withdrawal"),
    ("transfer_op", "transfer"),
    ("transfer_conjunto", "transfer"),
]


def _payload(row: dict[str, Any]) -> dict[str, Any]:
    return row["payload_json"]


@pytest.mark.parametrize("mutation,reason", _E4_CASES)
def test_live_mutation_dual_writes_and_notifies_after_commit(
    mutation: str, reason: str
) -> None:
    notifier = RecordingNotifier()
    service, snapshots = _e4_setup(live=True, notifier=notifier)
    published_before = copy.deepcopy(snapshots.published["01"])

    _e4_mutate(service, mutation)

    working = snapshots.rows["01"]
    published = snapshots.published["01"]
    assert _payload(working) == _payload(published)
    # geração e metadados da publicação intactos
    assert working["generation_id"] == E4_GENERATION
    assert published["generation_id"] == E4_GENERATION
    assert published["published_at"] == published_before["published_at"]
    assert published["published_by"] == published_before["published_by"]
    assert published["source_refreshed_at"] == published_before["source_refreshed_at"]

    expected_count = 2 if mutation == "restore" else 1
    assert len(notifier.events) == expected_count
    assert notifier.events[-1]["branch"] == "01"
    assert notifier.events[-1]["reason"] == reason


@pytest.mark.parametrize("mutation,_reason", _E4_CASES)
def test_draft_mutation_writes_only_working_and_stays_silent(
    mutation: str, _reason: str
) -> None:
    notifier = RecordingNotifier()
    service, snapshots = _e4_setup(live=False, notifier=notifier)
    published_before = copy.deepcopy(snapshots.published["01"])

    _e4_mutate(service, mutation)

    working = snapshots.rows["01"]
    published = snapshots.published["01"]
    assert working["generation_id"] == "gen-e4-2"
    assert published == published_before
    assert notifier.events == []


def test_mutation_without_publication_behaves_as_draft() -> None:
    """WORKING A, PUBLISHED inexistente: mutação funciona, nada é publicado."""
    notifier = RecordingNotifier()
    snapshots = FakeSnapshotRepo()
    _e4_seed(snapshots)
    service = _publish_service(snapshots, notifier=notifier)

    _e4_mutate(service, "reorder")

    assert snapshots.rows["01"]["payload_json"]["operations"][0]["production_order"] == (
        "10840401003"
    )
    assert snapshots.published.get("01") is None
    assert notifier.events == []


class _ExplodingPayloadPublications(FakePublicationRepo):
    def update_payload(self, conn: Any = None, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("falha no write do PUBLISHED")


def test_failed_published_write_rolls_back_working_and_never_notifies() -> None:
    notifier = RecordingNotifier()
    snapshots = FakeSnapshotRepo()
    _e4_seed(snapshots)
    snapshots.publish("01")
    publications = _ExplodingPayloadPublications(snapshots.published)
    service = _publish_service(snapshots, notifier=notifier, publications=publications)
    working_before = copy.deepcopy(snapshots.rows["01"]["payload_json"])
    published_before = copy.deepcopy(snapshots.published["01"])

    with pytest.raises(RuntimeError):
        _e4_mutate(service, "reorder")

    assert snapshots.rows["01"]["payload_json"] == working_before
    assert snapshots.published["01"] == published_before
    assert notifier.events == []


class _BrokenNotifier(RecordingNotifier):
    def notify_machine_load_changed(self, **kwargs: Any) -> None:
        raise RuntimeError("websocket fora do ar")


def test_notify_failure_after_commit_keeps_the_dual_write() -> None:
    service, snapshots = _e4_setup(live=True, notifier=_BrokenNotifier())

    _e4_mutate(service, "reorder")

    assert _payload(snapshots.rows["01"]) == _payload(snapshots.published["01"])
    assert snapshots.rows["01"]["payload_json"]["operations"][0]["production_order"] == (
        "10840401003"
    )


def test_live_mutation_reconciles_transient_divergence() -> None:
    """E3→E4: mesma geração nos dois lados com payloads diferentes — a próxima
    mutação LIVE grava o payload final do WORKING também no PUBLISHED."""
    service, snapshots = _e4_setup(live=True)
    divergent = _queue_payload([_op("11100001001", "01", work_center="CT-02")])
    snapshots.published["01"]["payload_json"] = divergent  # estado transitório E3
    assert _payload(snapshots.rows["01"]) != _payload(snapshots.published["01"])

    _e4_mutate(service, "reorder")

    assert _payload(snapshots.rows["01"]) == _payload(snapshots.published["01"])
    assert snapshots.published["01"]["generation_id"] == E4_GENERATION


def test_draft_changes_cross_to_published_only_on_publish() -> None:
    """Reorder + transfer + withdraw em DRAFT acumulam; publish carrega tudo junto."""
    service, snapshots = _e4_setup(live=False, notifier=RecordingNotifier())
    published_before = copy.deepcopy(snapshots.published["01"])

    _e4_mutate(service, "reorder")
    _e4_mutate(service, "transfer_op")
    _e4_mutate(service, "withdraw")

    assert snapshots.published["01"] == published_before

    service.publish(_user(*FULL_PERMS), branch="01")

    assert _payload(snapshots.published["01"]) == _payload(snapshots.rows["01"])
    assert snapshots.published["01"]["generation_id"] == "gen-e4-2"


def test_refresh_after_live_mutation_reopens_draft() -> None:
    """LIVE → mutação → refresh (nova geração C) → mutação em C não toca PUBLISHED."""
    service, snapshots = _e4_setup(live=True)
    _e4_mutate(service, "reorder")
    published_live = copy.deepcopy(snapshots.published["01"])

    # refresh cria WORKING C, PUBLISHED fica B'
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 3),
        payload=_queue_payload(_e4_queue()),
        refreshed_by="seed",
        generation_id="gen-e4-3",
    )
    _e4_mutate(service, "transfer_op")

    assert snapshots.published["01"] == published_live
    assert _payload(snapshots.rows["01"]) != _payload(snapshots.published["01"])


def test_publish_then_mutation_and_mutation_then_publish_converge() -> None:
    """publish × mutação: as duas ordens válidas terminam WORKING == PUBLISHED."""
    # reorder primeiro (DRAFT) → publish depois
    service, snapshots = _e4_setup(live=False)
    _e4_mutate(service, "reorder")
    service.publish(_user(*FULL_PERMS), branch="01")
    assert _payload(snapshots.rows["01"]) == _payload(snapshots.published["01"])

    # publish primeiro (LIVE) → reorder depois
    service2, snapshots2 = _e4_setup(live=True)
    _e4_mutate(service2, "reorder")
    assert _payload(snapshots2.rows["01"]) == _payload(snapshots2.published["01"])


def test_live_mutation_is_isolated_per_branch() -> None:
    service, snapshots = _e4_setup(live=True)
    snapshots.upsert(
        branch="02",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 3),
        payload=_queue_payload([_op("55500001001", "01", work_center="CT-02")]),
        refreshed_by="seed",
        generation_id="gen-e4-branch2",
    )
    snapshots.publish("02")
    branch2_before = copy.deepcopy(snapshots.published["02"])

    _e4_mutate(service, "reorder")

    assert snapshots.published["02"] == branch2_before


def test_noop_prioritize_in_live_does_not_write_or_notify() -> None:
    notifier = RecordingNotifier()
    snapshots = FakeSnapshotRepo()
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 3),
        payload=_queue_payload(
            [
                _op("10840401003", "03", work_center="CT-01A"),
                _op("99900001001", "01", work_center="CT-01A"),
            ]
        ),
        refreshed_by="seed",
        generation_id=E4_GENERATION,
    )
    snapshots.publish("01")
    service = _publish_service(snapshots, notifier=notifier)
    publications = FakePublicationRepo(snapshots.published)
    published_before = copy.deepcopy(snapshots.published["01"])

    service.prioritize_conjunto(_user(*FULL_PERMS), branch="01", order_number="108404")

    assert snapshots.payload_updates == 0
    assert snapshots.published["01"] == published_before
    assert notifier.events == []


def test_remote_status_call_happens_before_the_working_lock() -> None:
    """prioritize: HTTP do live status fora da transação; lock só no write."""
    snapshots = FakeSnapshotRepo()
    _e4_seed(snapshots)
    snapshots.publish("01")
    gateway = FakeGateway()
    order_log: list[str] = []

    original_get_for_update = snapshots.get_for_update

    def spy_get_for_update(**kwargs: Any) -> Any:
        order_log.append("lock")
        return original_get_for_update(**kwargs)

    snapshots.get_for_update = spy_get_for_update  # type: ignore[method-assign]

    original_fetch = gateway.fetch_machine_load_appointment_status

    def spy_fetch(*args: Any, **kwargs: Any) -> Any:
        order_log.append("http")
        return original_fetch(*args, **kwargs)

    gateway.fetch_machine_load_appointment_status = spy_fetch  # type: ignore[method-assign]

    service = MachineLoadService(
        gateway,
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
    )
    service.prioritize_conjunto(_user(*FULL_PERMS), branch="01", order_number="108404")

    assert "http" in order_log
    assert "lock" in order_log
    assert order_log.index("http") < order_log.index("lock")


def test_published_row_cache_reflects_live_payload_update(
    publications_db: FakePublicationsDb,
) -> None:
    """update_payload no PUBLISHED: xmin muda e o get() serve a nova versão sem TTL."""
    repo = PostgresMachineLoadPublicationRepository()
    _publish(repo, "01", "gen-e4-1", _queue_payload(_e4_queue()))

    first = repo.get(branch="01")
    assert first["payload_json"]["operations"][0]["production_order"] == "99900001001"

    new_payload = _queue_payload(_e4_queue())
    new_payload["operations"].reverse()
    updated = repo.update_payload(branch="01", payload=new_payload)

    assert updated["generation_id"] == "gen-e4-1"
    assert updated["published_at"] == first["published_at"]
    assert updated["published_by"] == first["published_by"]
    assert updated["row_version"] != first["row_version"]

    reread = repo.get(branch="01")
    assert reread["payload_json"]["operations"][0]["production_order"] == "10840402001"
