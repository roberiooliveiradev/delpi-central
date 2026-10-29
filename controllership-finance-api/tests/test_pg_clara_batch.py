"""CLARA batch — orquestração multiação em PostgreSQL real (V012).

Cobre o fluxo USER REQUEST → DISCOVERY → PLAN → PREPARE_BATCH →
VERIFIED CONSENT → EXECUTE → VERIFY → REPORT do Documento 106:

- plano classifica viable/blocked (capability desconhecida, params
  ausentes, recurso inexistente, competência errada);
- consentimento consolidado único por lote — sem consent, sem
  execução; plano divergente rejeitado (anti-ampliação);
- claim atômico por operação — duas execuções concorrentes têm um
  só corredor; duas ACTs numa proposta têm um só vencedor;
- dependentes de falhas bloqueiam; independentes continuam;
- retomada reconcilia CLAIMED por read-back e nunca repete efeito
  desconhecido;
- relatório por operação reflete o estado real (VERIFIED/FAILED/
  BLOCKED/UNKNOWN), não o retorno da função.
"""

from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg
import pytest
from psycopg.rows import dict_row

from controllership_finance_app.application.clara.batch_orchestrator import (
    ClaraBatchOrchestrator,
)
from controllership_finance_app.application.clara.step_up_consent import (
    ClaraStepUpConsent,
    ConsentRequired,
)
from controllership_finance_app.infrastructure.persistence.clara_consent_challenge_repository import (
    ClaraConsentChallengeRepository,
)
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.clara_batch_repository import (
    BatchActorMismatch,
    BatchNotConfirmed,
    BatchTerminal,
    ClaraBatchRepository,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    ClaraProposalRepository,
    ProposalConsumed,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_document_repository import (
    ClosingDocumentRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    RECONCILIATION_DOMAINS,
    ClosingP3Repository,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    ClosingPackageRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
    ClosingValidationRepository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)

PG_ENV = (
    "CF_TEST_PG_HOST",
    "CF_TEST_PG_NAME",
    "CF_TEST_PG_USER",
    "CF_TEST_PG_PASSWORD",
)

pytestmark = pytest.mark.skipif(
    not all(os.getenv(k) for k in PG_ENV),
    reason="CF_TEST_PG_* ausente — integração PostgreSQL não configurada",
)

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-admin-batch-test"))
UPLOADER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-uploader-batch-test"))
REVIEWER_C = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-reviewer-c-batch"))
OUTSIDER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-outsider-batch"))
PERIOD = "2028-05"

from pg_test_isolation import (  # noqa: E402
    assert_safe_test_prefix,
    create_owned_test_database,
    drop_owned_test_database,
    require_test_environment,
)


def _test_connect(dbname: str) -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["CF_TEST_PG_HOST"],
        port=int(os.getenv("CF_TEST_PG_PORT", "5432")),
        dbname=dbname,
        user=os.environ["CF_TEST_PG_USER"],
        password=os.environ["CF_TEST_PG_PASSWORD"],
        autocommit=True,
    )


@pytest.fixture(scope="module", autouse=True)
def _configure_db():
    import controllership_finance_app.config as cfg

    prefix = os.environ["CF_TEST_PG_NAME"]
    assert_safe_test_prefix(prefix)
    refusal = require_test_environment(os.environ)
    if refusal:
        pytest.skip(refusal)

    admin_db = os.getenv("CF_TEST_PG_ADMIN_DB", "postgres")
    owned = create_owned_test_database(_test_connect, admin_db, prefix)

    original = {
        k: getattr(cfg.settings, k)
        for k in (
            "PLUGINS_DB_HOST",
            "PLUGINS_DB_PORT",
            "PLUGINS_DB_NAME",
            "PLUGINS_DB_USER",
            "PLUGINS_DB_PASSWORD",
            "PLUGINS_DB_SSLMODE",
            "PLUGINS_DB_CONNECT_TIMEOUT",
        )
    }
    cfg.settings.PLUGINS_DB_HOST = os.environ["CF_TEST_PG_HOST"]
    cfg.settings.PLUGINS_DB_PORT = os.getenv("CF_TEST_PG_PORT", "5432")
    cfg.settings.PLUGINS_DB_NAME = owned.name
    cfg.settings.PLUGINS_DB_USER = os.environ["CF_TEST_PG_USER"]
    cfg.settings.PLUGINS_DB_PASSWORD = os.environ["CF_TEST_PG_PASSWORD"]
    cfg.settings.PLUGINS_DB_SSLMODE = os.getenv("CF_TEST_PG_SSLMODE", "prefer")
    cfg.settings.PLUGINS_DB_CONNECT_TIMEOUT = 10

    yield

    drop_owned_test_database(_test_connect, admin_db, owned)
    for k, v in original.items():
        setattr(cfg.settings, k, v)


@pytest.fixture(scope="module")
def env(_configure_db):
    applied = mr.run_migrations()
    assert applied[-1] == "V018__recipient_document_delivery.sql"
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(template_id, 1, actor=ADMIN)
    checklist.publish_version(
        template_id, 1, effective_from_period="2028-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD, actor=UPLOADER)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controllership_finance.competence_checklist_item
               SET state = 'ACCEPTED'
             WHERE competence_id = (
                 SELECT competence_id
                   FROM controllership_finance.monthly_competence
                  WHERE period = %s)
               AND state = 'EXPECTED'
            """,
            (PERIOD,),
        )
    p3 = ClosingP3Repository()
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        competence_id = p3._competence_id(cur, PERIOD)
        doc_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO controllership_finance.closing_document
                (document_id, competence_id, link_kind,
                 idempotency_key, request_hash, uploaded_by)
            VALUES (%s, %s, 'competence', %s, %s, %s)
            """,
            (
                doc_id, competence_id,
                f"official-{uuid.uuid4()}", "0" * 64, ADMIN,
            ),
        )
    for domain in RECONCILIATION_DOMAINS:
        p3.upsert_reconciliation(
            PERIOD,
            domain,
            actor=ADMIN,
            source_state="AVAILABLE",
            expected_amount=Decimal("1000.00"),
            reported_amount=Decimal("1000.00"),
            provenance={"source": "official"},
            provenance_kind="OFFICIAL",
            official_document_id=doc_id,
        )
    p3.confirm_cutoff(PERIOD, actor=ADMIN)
    p3.revalidate(PERIOD, actor=ADMIN)
    pkg = ClosingPackageRepository()
    pkg.assign_actor(
        PERIOD, actor=ADMIN, role="REVIEWER",
        subject=REVIEWER_C, recipient_area="CONTABIL", area="CONTABIL",
    )
    pkg_view = pkg.finalize_package(PERIOD, "CONTABIL", actor=ADMIN)
    version_id = str(pkg_view["current_version"]["package_version_id"])
    pkg.submit_for_review(
        PERIOD, version_id, actor=ADMIN, expected_revision=1
    )
    return {
        "checklist": checklist,
        "docs": ClosingDocumentRepository(),
        "val": ClosingValidationRepository(),
        "pkg": pkg,
        "proposals": ClaraProposalRepository(),
        "batches": ClaraBatchRepository(),
        "orchestrator": ClaraBatchOrchestrator(
            writes=ClaraGovernedWrites(
                identity_provider=lambda: {
                    "subject": ADMIN, "name": "cf-admin-test",
                    "is_manage": True, "is_dre": True,
                })),
        "writes": ClaraGovernedWrites(
            identity_provider=lambda: {
                "subject": ADMIN, "name": "cf-admin-test",
                "is_manage": True, "is_dre": True,
            }),
        "version_id": version_id,
    }


# -- helpers -----------------------------------------------------------------


def _clarify_op(env, question: str) -> dict:
    return {
        "capability": "clarification.open",
        "params": {
            "period": PERIOD,
            "package_version_id": env["version_id"],
            "question": question,
            "area": "CONTABIL",
        },
    }


def _resolve_op(clarification_id: str) -> dict:
    return {
        "capability": "clarification.resolve",
        "params": {
            "period": PERIOD,
            "clarification_id": clarification_id,
            "response": "Resposta via lote.",
        },
    }


def _open_clarification_direct(env, question="direta") -> str:
    clarif = env["pkg"].open_clarification(
        PERIOD,
        env["version_id"],
        actor=REVIEWER_C,
        question=question,
        area="CONTABIL",
    )
    return str(clarif["clarification_id"])


def _consent_batch(batch_id: str, actor: str) -> None:
    """Consentimento consolidado pela superfície confiável.

    Test double honesto: chama o MESMO serviço que a rota BFF de
    consentimento usa — token step-up com ``iat`` posterior ao
    PREPARE, como o Portal produz via refresh Keycloak. A assinatura
    JWT em si é validada na camada HTTP, não aqui.
    """
    challenge = ClaraConsentChallengeRepository().latest_for_batch(
        batch_id=batch_id
    )
    ClaraStepUpConsent().record_batch_consent(
        batch_id=batch_id,
        actor_sub=actor,
        token_claims={
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "sub": actor,
            "jti": uuid.uuid4().hex,
        },
        challenge_id=str(challenge["challenge_id"]),
    )


def _full_cycle(env, operations, actor=REVIEWER_C, resume=False):
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=operations, actor_sub=actor
    )
    _consent_batch(prepared["batch_id"], actor)
    orch.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=actor,
        plan_hash=prepared["plan_hash"],
    )
    return orch.execute_batch(
        handle=prepared["batch_handle"],
        actor_sub=actor,
        resume=resume,
    ), prepared


def _states(result):
    return {op["seq"]: op["state"] for op in result["operations"]}


# == PLAN / classificação ======================================================


def test_plan_classifies_viable_and_blocked(env):
    orch = env["orchestrator"]
    clarif_id = _open_clarification_direct(env)
    plan = orch.plan_batch(
        operations=[
            _clarify_op(env, "v1"),
            {"capability": "totvs.write_stock", "params": {}},
            {"capability": "clarification.resolve",
             "params": {"period": PERIOD}},
            _resolve_op(clarif_id),
            _resolve_op(str(uuid.uuid4())),
        ],
        actor_sub=ADMIN,
    )
    ops = {op["index"]: op for op in plan["operations"]}
    assert ops[0]["status"] == "viable"
    assert ops[1]["status"] == "blocked"
    assert ops[1]["block_reason"] == "unknown_capability"
    assert ops[2]["status"] == "blocked"
    assert ops[2]["block_reason"] == "missing_params"
    assert ops[3]["status"] == "viable"
    # clarification_id inexistente → snapshot sem conteúdo ⇒ blocked
    assert ops[4]["status"] == "blocked"
    assert plan["viable_count"] == 2
    assert plan["blocked_count"] == 3
    assert len(plan["plan_hash"]) == 64


def test_plan_implicit_dependency_same_resource(env):
    orch = env["orchestrator"]
    plan = orch.plan_batch(
        operations=[
            _clarify_op(env, "q-impl-1"),
            _clarify_op(env, "q-impl-2"),
        ],
        actor_sub=ADMIN,
    )
    ops = {op["index"]: op for op in plan["operations"]}
    # Mesma versão: a segunda é serializada atrás da primeira —
    # preserva a ordem pedida pelo usuário.
    assert 0 in ops[1]["depends_on"]


def test_plan_cycle_rejected(env):
    orch = env["orchestrator"]
    with pytest.raises(ChecklistDomainError):
        orch.plan_batch(
            operations=[
                {**_clarify_op(env, "c1"), "depends_on": [1]},
                {**_clarify_op(env, "c2"), "depends_on": [0]},
            ],
            actor_sub=ADMIN,
        )


# == CONSENT / confirmação consolidada =========================================


def test_execute_without_consent_rejected(env):
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "sem consentimento")],
        actor_sub=REVIEWER_C,
    )
    with pytest.raises(BatchNotConfirmed):
        orch.execute_batch(
            handle=prepared["batch_handle"], actor_sub=REVIEWER_C
        )


def test_plan_expansion_rejected(env):
    """Consentimento vale para o plan_hash exato — consentir o lote
    e depois apresentar outro plan_hash invalida a confirmação."""
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "plano A")],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    with pytest.raises(ChecklistDomainError) as excinfo:
        orch.confirm_batch(
            handle=prepared["batch_handle"],
            actor_sub=REVIEWER_C,
            plan_hash="f" * 64,
        )
    assert "divergente" in str(excinfo.value).lower()
    # Hash correto segue confirmando normalmente.
    out = orch.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    assert out["status"] == "CONFIRMED"


def test_direct_mcp_confirm_without_portal_consent_rejected(env):
    """§3.1: a chamada MCP autenticada NUNCA é prova de consentimento.

    Sem consent_record portal_step_up (nem attestation válida),
    confirm_batch rejeita com consent_required + URL da superfície
    confiável — texto do modelo ou boolean nunca bastam."""
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "bypass tentativa")],
        actor_sub=REVIEWER_C,
    )
    with pytest.raises(ConsentRequired) as excinfo:
        orch.confirm_batch(
            handle=prepared["batch_handle"],
            actor_sub=REVIEWER_C,
            plan_hash=prepared["plan_hash"],
        )
    assert excinfo.value.code == "consent_required"
    assert "clara-consent" in str(excinfo.value)
    # E a execução continua bloqueada.
    with pytest.raises(BatchNotConfirmed):
        orch.execute_batch(
            handle=prepared["batch_handle"], actor_sub=REVIEWER_C
        )


def test_batch_wrong_actor_rejected(env):
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "ator A")],
        actor_sub=REVIEWER_C,
    )
    with pytest.raises(BatchActorMismatch):
        orch.confirm_batch(
            handle=prepared["batch_handle"],
            actor_sub=OUTSIDER,
            plan_hash=prepared["plan_hash"],
        )


def test_host_attestation_fail_closed_without_secret(env, monkeypatch):
    monkeypatch.delenv("CLARA_HOST_ATTESTATION_SECRET", raising=False)
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "att")],
        actor_sub=REVIEWER_C,
    )
    from controllership_finance_app.application.clara.batch_orchestrator import (
        HostAttestationUnavailable,
    )
    with pytest.raises(HostAttestationUnavailable):
        orch.confirm_batch(
            handle=prepared["batch_handle"],
            actor_sub=ADMIN,
            plan_hash=prepared["plan_hash"],
            attestation={"signature": "fabricated"},
        )


def test_host_attestation_valid_hmac(env, monkeypatch):
    import hashlib
    import hmac
    from datetime import datetime, timedelta, timezone

    secret = "test-host-secret"
    monkeypatch.setenv("CLARA_HOST_ATTESTATION_SECRET", secret)
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "att-hmac")],
        actor_sub=REVIEWER_C,
    )
    expires = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()
    payload = f"{prepared['plan_hash']}|{REVIEWER_C}|{expires}".encode()
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    out = orch.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
        attestation={
            "plan_hash": prepared["plan_hash"],
            "actor_sub": REVIEWER_C,
            "expires_at": expires,
            "signature": sig,
        },
    )
    assert out["consent_mode"] == "HOST_ATTESTED"
    assert out["status"] == "CONFIRMED"


# == EXECUTE — independentes ====================================================


def test_batch_two_independent_operations(env):
    clarif_id = _open_clarification_direct(env, "alvo resolve")
    result, _ = _full_cycle(
        env,
        [
            _clarify_op(env, "independente nova"),
            _resolve_op(clarif_id),
        ],
    )
    assert result["status"] == "COMPLETED"
    assert result["summary"]["executed"] == 2
    states = _states(result)
    assert states[0] == "VERIFIED"
    assert states[1] == "VERIFIED"
    # read-back de negócio: a clarification alvo ficou RESOLVED de
    # verdade, não só no retorno.
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT state FROM controllership_finance.closing_clarification
             WHERE clarification_id = %s
            """,
            (clarif_id,),
        )
        assert cur.fetchone()[0] == "RESOLVED"


def test_batch_five_operations(env):
    targets = [
        _open_clarification_direct(env, f"alvo5-{i}") for i in range(4)
    ]
    ops = [_clarify_op(env, "quinta nova")] + [
        _resolve_op(c) for c in targets
    ]
    result, _ = _full_cycle(env, ops)
    assert result["summary"]["executed"] == 5
    assert result["status"] == "COMPLETED"


def test_batch_twenty_operations(env):
    targets = [
        _open_clarification_direct(env, f"alvo20-{i}")
        for i in range(19)
    ]
    ops = [_clarify_op(env, "vigésima nova")] + [
        _resolve_op(c) for c in targets
    ]
    result, _ = _full_cycle(env, ops)
    assert result["summary"]["executed"] == 20
    assert result["status"] == "COMPLETED"
    # Idempotency keys únicos por operação no lote.
    batch = env["batches"].get_batch(batch_id=result["batch_id"])
    keys = [op["idempotency_key"] for op in batch["operations"]]
    assert len(set(keys)) == len(keys)


# == EXECUTE — dependentes e falhas parciais ====================================


def test_batch_dependent_blocked_on_failure(env):
    clarif_id = _open_clarification_direct(env, "será resolvida 2x")
    independent_id = _open_clarification_direct(env, "indep recurso")
    # op0 resolve (sucesso); op1 resolve a MESMA (depende de op0:
    # depois que op0 aplica, o estado selado de op1 diverge ⇒
    # proposal_stale); op2 depende de op1 ⇒ BLOCKED; op3 é recurso
    # independente ⇒ VERIFIED.
    ops = [
        _resolve_op(clarif_id),
        {**_resolve_op(clarif_id), "depends_on": [0]},
        {**_clarify_op(env, "dep dependente"), "depends_on": [1]},
        _resolve_op(independent_id),
    ]
    result, _ = _full_cycle(env, ops)
    states = _states(result)
    assert states[0] == "VERIFIED"
    assert states[1] == "FAILED"
    assert states[2] == "BLOCKED"
    # Independente continua mesmo com falha na cadeia.
    assert states[3] == "VERIFIED"
    assert result["status"] == "COMPLETED_WITH_FAILURES"


def test_batch_unauthorized_op_fails_typed(env):
    """Operação fora da autorização do ator falha com erro de
    domínio tipado — nunca sucesso fabricado (S4)."""
    independent_id = _open_clarification_direct(env, "indep auth")
    result, _ = _full_cycle(
        env,
        [
            {
                "capability": "review.record_decision",
                "params": {
                    "period": PERIOD,
                    "package_version_id": env["version_id"],
                    "area": "FISCAL",
                    "outcome": "ACCEPTED",
                },
            },
            _resolve_op(independent_id),
        ],
        actor=REVIEWER_C,
    )
    states = _states(result)
    assert states[0] == "FAILED"
    failed = next(
        op for op in result["operations"] if op["state"] == "FAILED"
    )
    assert failed["error_code"] in {
        "reviewer_not_assigned",
        "reviewer_not_eligible",
        "missing_reason",
    }
    assert states[1] == "VERIFIED"


def test_batch_wrong_competence_op(env):
    """Operação em competência inexistente bloqueia no plano
    (snapshot sem conteúdo) — sem efeito lateral."""
    orch = env["orchestrator"]
    plan = orch.plan_batch(
        operations=[
            {
                "capability": "clarification.open",
                "params": {
                    "period": "2099-12",
                    "package_version_id": env["version_id"],
                    "question": "período errado",
                },
            }
        ],
        actor_sub=REVIEWER_C,
    )
    assert plan["operations"][0]["status"] == "blocked"


def test_batch_historical_version_op_fails(env):
    """Versão que não é a vigente SUBMITTED falha pelas regras
    canônicas de domínio, não pela CLARA."""
    pkg = env["pkg"]
    old_version = env["version_id"]
    # Complemento pós-submissão: v1 permanece SUBMITTED mas deixa de
    # ser a vigente → operações nela são rejeitadas pelo domínio.
    pkg_view = pkg.create_complement(
        PERIOD, old_version, actor=ADMIN,
        reason="correção estrutural do pacote",
    )
    env["version_id"] = str(
        pkg_view["current_version"]["package_version_id"]
    )
    # Finaliza e submete o complemento → volta a haver versão
    # vigente SUBMITTED para os testes seguintes.
    pkg_view = pkg.finalize_package(PERIOD, "CONTABIL", actor=ADMIN)
    env["version_id"] = str(
        pkg_view["current_version"]["package_version_id"]
    )
    pkg.submit_for_review(
        PERIOD, env["version_id"], actor=ADMIN,
        expected_revision=pkg_view["current_version"]["revision"],
    )
    orch = env["orchestrator"]
    plan = orch.plan_batch(
        operations=[
            {
                "capability": "clarification.open",
                "params": {
                    "period": PERIOD,
                    "package_version_id": old_version,
                    "question": "na histórica",
                    "area": "CONTABIL",
                },
            }
        ],
        actor_sub=REVIEWER_C,
    )
    op = plan["operations"][0]
    if op["status"] == "blocked":
        assert op["block_reason"] in {
            "snapshot_unavailable", "invalid_package_transition",
            "competence_not_found",
        }
    else:
        result, _ = _full_cycle(
            env,
            [
                {
                    "capability": "clarification.open",
                    "params": {
                        "period": PERIOD,
                        "package_version_id": old_version,
                        "question": "na histórica",
                        "area": "CONTABIL",
                    },
                }
            ],
        )
        assert _states(result)[0] == "FAILED"


# == EXECUTE — concorrência =====================================================


def test_two_concurrent_acts_single_winner(env):
    """S1: duas ACTs na mesma proposta — exatamente uma aplica."""
    writes = env["writes"]
    proposal = writes.prepare(
        capability="clarification.open",
        params={
            "period": PERIOD,
            "package_version_id": env["version_id"],
            "question": "corrida única",
            "area": "CONTABIL",
        },
        actor_sub=REVIEWER_C,
    )
    challenge = ClaraConsentChallengeRepository().latest_for_proposal(
        proposal_id=str(proposal["proposal_id"])
    )
    ClaraStepUpConsent().record_proposal_consent(
        proposal_id=str(proposal["proposal_id"]),
        actor_sub=REVIEWER_C,
        token_claims={
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "sub": REVIEWER_C,
        },
        challenge_id=str(challenge["challenge_id"]),
    )
    outcomes = []

    def run():
        try:
            writes.commit(
                handle=proposal["proposal_handle"],
                actor_sub=REVIEWER_C,
            )
            outcomes.append("executed")
        except ProposalConsumed:
            outcomes.append("consumed")
        except ChecklistDomainError as exc:
            outcomes.append(getattr(exc, "code", "error"))

    t1 = threading.Thread(target=run)
    t2 = threading.Thread(target=run)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert outcomes.count("executed") == 1
    assert outcomes.count("consumed") == 1


def test_concurrent_batch_execute_single_runner(env):
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "corrida batch")],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    orch.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    errors = []
    results = []

    def run():
        try:
            results.append(
                orch.execute_batch(
                    handle=prepared["batch_handle"],
                    actor_sub=REVIEWER_C,
                )
            )
        except BatchTerminal as exc:
            errors.append(exc)
        except ChecklistDomainError as exc:
            errors.append(exc)

    t1 = threading.Thread(target=run)
    t2 = threading.Thread(target=run)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    # Exatamente um corredor; o outro é rejeitado tipado (EXECUTING
    # ou terminal). Nunca dois lotes aplicados.
    assert len(results) + len(errors) == 2
    assert len(results) == 1
    batch = env["batches"].get_batch(batch_id=results[0]["batch_id"])
    verified = [
        op for op in batch["operations"] if op["state"] == "VERIFIED"
    ]
    assert len(verified) == 1


def test_batch_stale_op_fails_and_dependent_blocks(env):
    """Mudança externa entre PREPARE e EXECUTE: a operação stale
    falha e sua dependente bloqueia — sem efeito parcial oculto."""
    orch = env["orchestrator"]
    clarif_id = _open_clarification_direct(env, "será resolvida fora")
    prepared = orch.prepare_batch(
        operations=[
            _resolve_op(clarif_id),
            {**_clarify_op(env, "dep da stale"), "depends_on": [0]},
        ],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    orch.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    # Mutação externa entre consent e execute.
    env["pkg"].resolve_clarification(
        PERIOD, clarif_id, actor=ADMIN, response="fora da CLARA"
    )
    result = orch.execute_batch(
        handle=prepared["batch_handle"], actor_sub=REVIEWER_C
    )
    states = _states(result)
    assert states[0] == "FAILED"
    assert states[1] == "BLOCKED"


# == EXECUTE — retomada / estado desconhecido ===================================


def test_resume_reconciles_claimed_operation(env):
    """Operação CLAIMED de uma execução interrompida não repete
    efeito: reconcile marca UNKNOWN (efeito desconhecido) quando a
    pós-condição não pode ser comprovada."""
    orch = env["orchestrator"]
    clarif_id = _open_clarification_direct(env, "reconcile")
    prepared = orch.prepare_batch(
        operations=[_resolve_op(clarif_id)],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    orch.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    batch_id = prepared["batch_id"]
    # Simula crash após claim: força o estado CLAIMED.
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controllership_finance.clara_batch
               SET status = 'EXECUTING'
             WHERE batch_id = %s
            """,
            (batch_id,),
        )
        cur.execute(
            """
            UPDATE controllership_finance.clara_batch_operation
               SET state = 'CLAIMED'
             WHERE batch_id = %s
            """,
            (batch_id,),
        )
    result = orch.execute_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        resume=True,
    )
    states = _states(result)
    # Efeito desconhecido ⇒ UNKNOWN reportado, não repetido.
    assert states[0] == "UNKNOWN"
    # A clarification NÃO foi resolvida em duplicidade.
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT state FROM controllership_finance.closing_clarification
             WHERE clarification_id = %s
            """,
            (clarif_id,),
        )
        assert cur.fetchone()[0] == "OPEN"


def test_resume_reconciles_verified_effect(env):
    """Se o efeito aplicou mas o estado não gravou, o reconcile por
    read-back marca VERIFIED em vez de UNKNOWN."""
    orch = env["orchestrator"]
    clarif_id = _open_clarification_direct(env, "reconcile-applied")
    prepared = orch.prepare_batch(
        operations=[_resolve_op(clarif_id)],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    orch.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    batch_id = prepared["batch_id"]
    # Simula: efeito aplicado + op marcada CLAIMED + resultado
    # conhecido — o crash veio antes do set_operation_state.
    env["pkg"].resolve_clarification(
        PERIOD, clarif_id, actor=ADMIN, response="resolvida"
    )
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=dict_row
    ) as cur:
        cur.execute(
            """
            UPDATE controllership_finance.clara_batch
               SET status = 'EXECUTING'
             WHERE batch_id = %s
            """,
            (batch_id,),
        )
        cur.execute(
            """
            UPDATE controllership_finance.clara_batch_operation
               SET state = 'CLAIMED',
                   result = %s::jsonb
             WHERE batch_id = %s
            """,
            (
                '{"result": {"state": "RESOLVED"}}',
                batch_id,
            ),
        )
    result = orch.execute_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        resume=True,
    )
    assert _states(result)[0] == "VERIFIED"


def test_execute_terminal_batch_rejected(env):
    result, prepared = _full_cycle(
        env, [_clarify_op(env, "terminal")]
    )
    with pytest.raises(BatchTerminal):
        env["orchestrator"].execute_batch(
            handle=prepared["batch_handle"], actor_sub=REVIEWER_C
        )


# == EXECUTE — falha de infraestrutura ==========================================


def test_batch_db_failure_marks_failed_and_reports(env, monkeypatch):
    """Falha de banco dentro de uma operação: FAILED honesto,
    dependentes bloqueados, independentes continuam."""
    orch = env["orchestrator"]
    clarif_id = _open_clarification_direct(env, "alvo db fail")
    independent_id = _open_clarification_direct(env, "ind db")
    real_table = ClaraGovernedWrites()._capability_table()

    real_resolve = real_table["clarification.resolve"]["execute"]

    def broken_execute(params, actor, groups):
        if str(params.get("clarification_id")) == clarif_id:
            raise psycopg.OperationalError("connection lost")
        return real_resolve(params, actor, groups)

    def patched_table(self):
        table = real_table
        table["clarification.resolve"] = {
            **table["clarification.resolve"],
            "execute": broken_execute,
        }
        return table

    monkeypatch.setattr(
        ClaraGovernedWrites, "_capability_table", patched_table
    )
    # Orquestrador constrói sua própria tabela via self._writes —
    # usa um orchestrator cujo _writes é a classe monkeypatchada.
    orch2 = ClaraBatchOrchestrator(
            writes=ClaraGovernedWrites(
                identity_provider=lambda: {
                    "subject": ADMIN, "name": "cf-admin-test",
                    "is_manage": True, "is_dre": True,
                }))
    prepared = orch2.prepare_batch(
        operations=[
            _resolve_op(clarif_id),
            {**_clarify_op(env, "dep db"), "depends_on": [0]},
            _resolve_op(independent_id),
        ],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    orch2.confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    result = orch2.execute_batch(
        handle=prepared["batch_handle"], actor_sub=REVIEWER_C
    )
    states = _states(result)
    assert states[0] == "FAILED"
    assert states[1] == "BLOCKED"
    assert states[2] == "VERIFIED"


# == Relatório / status ==========================================================


def test_batch_status_reports_per_operation(env):
    result, _ = _full_cycle(
        env, [_clarify_op(env, "status check")]
    )
    status = env["orchestrator"].batch_status(
        batch_id=result["batch_id"], actor_sub=REVIEWER_C
    )
    assert status["status"] == "COMPLETED"
    assert status["consent_mode"] == "CONSOLIDATED"
    assert status["operations"][0]["state"] == "VERIFIED"
    assert len(status["plan_hash"]) == 64
    # Ator errado não enxerga o lote.
    with pytest.raises(BatchActorMismatch):
        env["orchestrator"].batch_status(
            batch_id=result["batch_id"], actor_sub=OUTSIDER
        )


# == Consent challenge (R-CLARA-01, V014) ========================================


def _challenge_for_batch(batch_id: str) -> dict:
    challenge = ClaraConsentChallengeRepository().latest_for_batch(
        batch_id=batch_id
    )
    assert challenge is not None
    return challenge


def _fresh_claims(actor: str) -> dict:
    return {
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "sub": actor,
        "jti": uuid.uuid4().hex,
    }


def test_challenge_issued_on_prepare(env):
    """O PREPARE emite o objeto de autorização vinculado ao plano."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "desafio emitido")],
        actor_sub=REVIEWER_C,
    )
    challenge = _challenge_for_batch(prepared["batch_id"])
    assert challenge["kind"] == "batch"
    assert str(challenge["batch_id"]) == prepared["batch_id"]
    assert challenge["actor_sub"] == REVIEWER_C
    assert challenge["plan_hash"] == prepared["plan_hash"]
    assert challenge["status"] == "PENDING"
    assert challenge["origin"] == "portal"


def test_consent_requires_challenge_id(env):
    """JWT fresco sozinho não basta: sem o desafio do plano, sem
    consentimento."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "sem challenge")],
        actor_sub=REVIEWER_C,
    )
    from controllership_finance_app.application.clara.step_up_consent import (
        ConsentChallengeRequired,
    )

    with pytest.raises(ConsentChallengeRequired):
        ClaraStepUpConsent().record_batch_consent(
            batch_id=prepared["batch_id"],
            actor_sub=REVIEWER_C,
            token_claims=_fresh_claims(REVIEWER_C),
            challenge_id=None,
        )


def test_consent_challenge_from_other_batch_rejected(env):
    """Um desafio emitido para outro lote não autoriza este plano."""
    orch = env["orchestrator"]
    prepared_a = orch.prepare_batch(
        operations=[_clarify_op(env, "lote A")], actor_sub=REVIEWER_C
    )
    prepared_b = orch.prepare_batch(
        operations=[_clarify_op(env, "lote B")], actor_sub=REVIEWER_C
    )
    challenge_b = _challenge_for_batch(prepared_b["batch_id"])
    from controllership_finance_app.infrastructure.persistence.clara_consent_challenge_repository import (
        ConsentChallengeMismatch,
    )

    with pytest.raises(ConsentChallengeMismatch):
        ClaraStepUpConsent().record_batch_consent(
            batch_id=prepared_a["batch_id"],
            actor_sub=REVIEWER_C,
            token_claims=_fresh_claims(REVIEWER_C),
            challenge_id=str(challenge_b["challenge_id"]),
        )


def test_consent_challenge_other_actor_rejected(env):
    """Outro usuário não pode utilizar a aprovação do requisitante."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "ator divergente")],
        actor_sub=REVIEWER_C,
    )
    challenge = _challenge_for_batch(prepared["batch_id"])
    with pytest.raises(BatchActorMismatch):
        ClaraStepUpConsent().record_batch_consent(
            batch_id=prepared["batch_id"],
            actor_sub=OUTSIDER,
            token_claims=_fresh_claims(OUTSIDER),
            challenge_id=str(challenge["challenge_id"]),
        )


def test_consent_idempotent_double_submit(env):
    """Dois cliques na página: o segundo devolve o estado vigente,
    não erro."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "duplo clique")],
        actor_sub=REVIEWER_C,
    )
    challenge = _challenge_for_batch(prepared["batch_id"])
    first = ClaraStepUpConsent().record_batch_consent(
        batch_id=prepared["batch_id"],
        actor_sub=REVIEWER_C,
        token_claims=_fresh_claims(REVIEWER_C),
        challenge_id=str(challenge["challenge_id"]),
    )
    assert first["status"] == "CONFIRMED"
    second = ClaraStepUpConsent().record_batch_consent(
        batch_id=prepared["batch_id"],
        actor_sub=REVIEWER_C,
        token_claims=_fresh_claims(REVIEWER_C),
        challenge_id=str(challenge["challenge_id"]),
    )
    assert second["status"] == "CONFIRMED"


def test_forged_consent_record_rejected(env):
    """consent_record escrito fora da superfície (sem desafio
    aprovado) não habilita a execução — o confirm rejeita."""
    orch = env["orchestrator"]
    prepared = orch.prepare_batch(
        operations=[_clarify_op(env, "forjado")], actor_sub=REVIEWER_C
    )
    # Injeta um consent_record que simula o formato do portal —
    # sem challenge_id válido, confirm_batch não confia.
    env["orchestrator"]._batches.record_consent(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
        mode="CONSOLIDATED",
        consent_record={
            "type": "portal_step_up",
            "confirmed_by": REVIEWER_C,
            "plan_hash": prepared["plan_hash"],
        },
    )
    with pytest.raises(ChecklistDomainError):
        orch.confirm_batch(
            handle=prepared["batch_handle"],
            actor_sub=REVIEWER_C,
            plan_hash=prepared["plan_hash"],
        )


def test_challenge_consumed_on_execute(env):
    """O desafio é single-use: a execução o consome."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "consumo único")],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    env["orchestrator"].confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    env["orchestrator"].execute_batch(
        handle=prepared["batch_handle"], actor_sub=REVIEWER_C
    )
    challenge = _challenge_for_batch(prepared["batch_id"])
    assert challenge["status"] == "CONSUMED"
    assert challenge["consumed_at"] is not None


def test_batch_summary_presents_full_plan(env):
    """R-CLARA-02: a superfície recebe o plano completo em
    linguagem funcional — resumo, descrições, impedimentos."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[
            _clarify_op(env, "Confirma a conciliação?"),
            {"capability": "nao.existe", "params": {}},
        ],
        actor_sub=REVIEWER_C,
    )
    summary = ClaraStepUpConsent().batch_summary(
        batch_id=prepared["batch_id"], actor_sub=REVIEWER_C
    )
    assert summary["consentable"] is True
    assert summary["totals"]["total"] == 2
    assert summary["totals"]["executable"] == 1
    assert summary["totals"]["blocked"] == 1
    assert summary["challenge"]["status"] == "PENDING"
    assert summary["challenge"]["challenge_id"]
    ops = summary["operations"]
    assert ops[0]["viability"] == "executable"
    assert "esclarecimento" in ops[0]["presentation"]["summary"].lower()
    assert ops[0]["presentation"]["displayable"] is True
    assert ops[0]["period"] == PERIOD
    assert ops[1]["viability"] == "blocked"
    assert ops[1]["block_reason"] == "unknown_capability"
    assert ops[1]["block_message"]


# == Contrato HTTP da superfície de consentimento (R-CLARA-01/02) ==============
#
# TestClient real sobre a app FastAPI: middleware de auth, rota BFF,
# serviço de consentimento e PostgreSQL efêmero — só a ASSINATURA do
# JWT é duplicada (responsabilidade do validator canônico, testada na
# própria suíte); claims refletem o que Keycloak emitiria.


@pytest.fixture
def http_client(monkeypatch):
    import delpi_auth.middleware.fastapi_auth as fa
    from fastapi.testclient import TestClient

    claims_holder = {
        "claims": {
            "sub": REVIEWER_C,
            "email": "reviewer@delpi.com.br",
            "name": "Revisor",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": uuid.uuid4().hex,
        }
    }
    rbac = {
        "id": REVIEWER_C,
        "email": "reviewer@delpi.com.br",
        "name": "Revisor",
        "roles": [],
        "groups": [],
        "permissions": ["controllership-finance.access"],
        "is_superadmin": False,
    }

    async def _rbac_result(token, *, force_refresh=False):
        return rbac

    monkeypatch.setattr(
        fa,
        "request_has_valid_internal_service_token",
        lambda request: False,
    )
    monkeypatch.setattr(
        fa, "validate_token", lambda token: claims_holder["claims"]
    )
    monkeypatch.setattr(fa, "load_user_rbac", _rbac_result)
    # A rota revalida o Bearer para obter iat/jti do step-up.
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes."
        "clara_consent_routes.validate_token",
        lambda token: claims_holder["claims"],
    )
    from controllership_finance_app.main import app

    client = TestClient(
        app, headers={"Authorization": "Bearer portal-token"}
    )
    return client, claims_holder


def test_http_get_batch_consent_view_full_plan(env, http_client):
    """GET devolve plano completo + desafio para a página."""
    client, _ = http_client
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "view http")],
        actor_sub=REVIEWER_C,
    )
    response = client.get(f"/clara/batches/{prepared['batch_id']}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["challenge"]["challenge_id"]
    assert data["consentable"] is True
    assert data["totals"]["executable"] == 1
    assert data["operations"][0]["presentation"]["summary"]


def test_http_post_consent_without_challenge_rejected(env, http_client):
    """JWT válido sem challenge_id ⇒ 400 — token sozinho não prova
    aprovação do plano."""
    client, _ = http_client
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "sem challenge http")],
        actor_sub=REVIEWER_C,
    )
    response = client.post(
        f"/clara/batches/{prepared['batch_id']}/consent", json={}
    )
    assert response.status_code == 400
    assert response.json()["data"]["error"]["code"] == (
        "consent_challenge_required"
    )


def test_http_post_consent_stale_token_rejected(env, http_client):
    """Token emitido ANTES do desafio não pode autorizá-lo."""
    client, holder = http_client
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "stale http")],
        actor_sub=REVIEWER_C,
    )
    holder["claims"]["iat"] = int(
        (datetime.now(timezone.utc) - timedelta(minutes=30)).timestamp()
    )
    challenge = _challenge_for_batch(prepared["batch_id"])
    response = client.post(
        f"/clara/batches/{prepared['batch_id']}/consent",
        json={"challenge_id": str(challenge["challenge_id"])},
    )
    assert response.status_code == 403
    assert response.json()["data"]["error"]["code"] == (
        "step_up_token_stale"
    )


def test_http_post_consent_happy_path(env, http_client):
    """challenge_id + token fresco ⇒ CONFIRMED em uma transação."""
    client, _ = http_client
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "happy http")],
        actor_sub=REVIEWER_C,
    )
    view = client.get(
        f"/clara/batches/{prepared['batch_id']}"
    ).json()["data"]
    response = client.post(
        f"/clara/batches/{prepared['batch_id']}/consent",
        json={"challenge_id": view["challenge"]["challenge_id"]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "CONFIRMED"
    challenge = _challenge_for_batch(prepared["batch_id"])
    assert challenge["status"] == "APPROVED"
    assert challenge["approved_by"] == REVIEWER_C


def test_http_get_batch_wrong_actor_forbidden(env, http_client):
    client, _ = http_client
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "outro ator http")],
        actor_sub=OUTSIDER,
    )
    response = client.get(f"/clara/batches/{prepared['batch_id']}")
    assert response.status_code == 403


# == GO ChatGPT: concorrência aprovação↔claim + motivos longos ================


def test_concurrent_double_approve_converges_single_consent(env):
    """Duas submissões concorrentes do MESMO desafio convergem:
    uma aprovação registrada, zero efeito duplicado — a segunda
    enxerga o estado vigente (idempotência honesta) ou recebe
    rejeição tipada, nunca um segundo consentimento."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "corrida aprovação")],
        actor_sub=REVIEWER_C,
    )
    challenge = _challenge_for_batch(prepared["batch_id"])
    claims = {
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "sub": REVIEWER_C,
        "jti": uuid.uuid4().hex,
    }
    results, errors = [], []

    def _approve():
        try:
            results.append(
                ClaraStepUpConsent().record_batch_consent(
                    batch_id=prepared["batch_id"],
                    actor_sub=REVIEWER_C,
                    token_claims=claims,
                    challenge_id=str(challenge["challenge_id"]),
                )
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_approve) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results, f"nenhuma aprovação convergiu: {errors}"
    # Toda repetição honesta devolve o MESMO estado; erros, se
    # houver, são tipados — nunca efeito duplicado.
    for error in errors:
        assert isinstance(error, ChecklistDomainError)
    batch = env["orchestrator"]._batches.get_batch(
        batch_id=prepared["batch_id"]
    )
    assert batch["status"] == "CONFIRMED"
    challenge_after = _challenge_for_batch(prepared["batch_id"])
    assert challenge_after["status"] == "APPROVED"


def test_approve_after_claim_consumed_rejected(env):
    """Corrida aprovação↔claim resolvida pelo lock: depois que o
    claim consumiu o desafio, uma aprovação tardia é rejeitada —
    o desafio não ressuscita e o estado permanece consumido."""
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, "aprovação tardia")],
        actor_sub=REVIEWER_C,
    )
    _consent_batch(prepared["batch_id"], REVIEWER_C)
    env["orchestrator"].confirm_batch(
        handle=prepared["batch_handle"],
        actor_sub=REVIEWER_C,
        plan_hash=prepared["plan_hash"],
    )
    env["orchestrator"].execute_batch(
        handle=prepared["batch_handle"], actor_sub=REVIEWER_C
    )
    challenge = _challenge_for_batch(prepared["batch_id"])
    assert challenge["status"] == "CONSUMED"
    with pytest.raises(ChecklistDomainError):
        ClaraStepUpConsent().record_batch_consent(
            batch_id=prepared["batch_id"],
            actor_sub=REVIEWER_C,
            token_claims={
                "iat": int(datetime.now(timezone.utc).timestamp()),
                "sub": REVIEWER_C,
                "jti": uuid.uuid4().hex,
            },
            challenge_id=str(challenge["challenge_id"]),
        )
    assert _challenge_for_batch(prepared["batch_id"])["status"] == (
        "CONSUMED"
    )


def test_presentation_preserves_full_long_motivation(env):
    """R-CLARA-02: motivo longo e material não pode ser truncado
    silenciosamente — o usuário precisa ler a justificativa
    integral que embasa a aprovação."""
    long_reason = (
        "Divergência de valores entre o extrato oficial e a "
        "conciliação importada na linha 42, com impacto no saldo "
        "de fechamento da competência; a rejeição preserva a "
        "evidência anterior para retrabalho pela área. " * 5
    )
    prepared = env["orchestrator"].prepare_batch(
        operations=[_clarify_op(env, long_reason)],
        actor_sub=REVIEWER_C,
    )
    view = ClaraStepUpConsent().batch_summary(
        batch_id=prepared["batch_id"], actor_sub=REVIEWER_C
    )
    op = view["operations"][0]
    presentation = op["presentation"]
    # O motivo exibido deve conter a justificativa INTEGRAL —
    # truncamento silencioso esconde escopo material da aprovação.
    assert presentation["motivation"] == f"«{long_reason.strip()}»", (
        "motivo truncado — usuário não vê a justificativa "
        f"integral: {presentation['motivation']!r}"
    )


def test_approve_claim_race_no_deadlock(env):
    """Doc 107 §6.1 — duplo-clique de consentimento concorrente com
    a execução: locks na ordem canônica batch→challenge em ambos os
    caminhos ⇒ nunca DeadlockDetected; estados finais consistentes.

    Executa o par em N lotes frescos com conexões reais concorrentes
    (a janela de corrida é real: o segundo approve re-trava o par
    batch+challenge enquanto o claim consome o desafio)."""
    import psycopg
    results = []
    for _ in range(8):
        prepared = env["orchestrator"].prepare_batch(
            operations=[_clarify_op(env, "corrida lock")],
            actor_sub=REVIEWER_C,
        )
        _consent_batch(prepared["batch_id"], REVIEWER_C)
        env["orchestrator"].confirm_batch(
            handle=prepared["batch_handle"],
            actor_sub=REVIEWER_C,
            plan_hash=prepared["plan_hash"],
        )
        challenge = _challenge_for_batch(prepared["batch_id"])
        errors = []

        def _reapprove():
            try:
                ClaraStepUpConsent().record_batch_consent(
                    batch_id=prepared["batch_id"],
                    actor_sub=REVIEWER_C,
                    token_claims={
                        "iat": int(
                            datetime.now(timezone.utc).timestamp()
                        ),
                        "sub": REVIEWER_C,
                        "jti": uuid.uuid4().hex,
                    },
                    challenge_id=str(challenge["challenge_id"]),
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        def _claim():
            try:
                env["orchestrator"].execute_batch(
                    handle=prepared["batch_handle"],
                    actor_sub=REVIEWER_C,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        t1 = threading.Thread(target=_reapprove)
        t2 = threading.Thread(target=_claim)
        t1.start()
        t2.start()
        t1.join(timeout=30)
        t2.join(timeout=30)
        assert not t1.is_alive() and not t2.is_alive(), (
            "thread travada — suspeita de deadlock não resolvido"
        )
        for error in errors:
            # Deadlock nunca é um resultado aceitável; erros tipados
            # de corrida honesta (estado, consumo) são legítimos.
            assert not isinstance(
                error, psycopg.errors.DeadlockDetected
            ), f"deadlock real: {error}"
        results.append(
            _challenge_for_batch(prepared["batch_id"])["status"]
        )
    assert set(results) <= {"CONSUMED"}
