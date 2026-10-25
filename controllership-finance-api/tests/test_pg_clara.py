"""CLARA — integração PostgreSQL real (V011 + governed writes).

Cobre: base de conhecimento (ingestão, dedup, supersede, recuperação
com citação, escopo de acesso, corpus versionado) e o ciclo
PREPARE→ACT governado (sem efeito colateral no PREPARE, wrong actor,
expirada, stale, single-use, auditoria `mcp/clara`, delegação às
regras canônicas — nunca bypass).

Ativado com CF_TEST_PG_* + CF_TEST_PG_CLUSTER=test +
CF_TEST_PG_ALLOW_DESTRUCTIVE=1 — banco efêmero com prova de ownership.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from controllership_finance_app.application.clara.corpus_ingestion import (
    segment_markdown,
)
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
    ProposalStale,
    UnknownCapability,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.clara_knowledge_repository import (
    ClaraKnowledgeRepository,
    KnowledgeNotFound,
)
from controllership_finance_app.infrastructure.persistence.clara_proposal_repository import (
    ClaraProposalRepository,
    ProposalActorMismatch,
    ProposalConsumed,
    ProposalExpired,
    handle_hash,
)
from decimal import Decimal

from psycopg.rows import dict_row

from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    RECONCILIATION_DOMAINS,
    ClosingP3Repository,
)
from controllership_finance_app.infrastructure.persistence.closing_document_repository import (
    ClosingDocumentRepository,
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

ADMIN = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-admin-clara-test"))
UPLOADER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-uploader-clara-test"))
REVIEWER_C = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-reviewer-c-clara"))
OUTSIDER = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cf-outsider-clara"))
PERIOD = "2028-03"

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
    assert applied[-1] == "V012__clara_batch_orchestration.sql"
    checklist = ClosingChecklistRepository()
    template_id = str(checklist.list_templates()[0]["template_id"])
    checklist.submit_version_for_review(template_id, 1, actor=ADMIN)
    checklist.publish_version(
        template_id, 1, effective_from_period="2028-01", actor=ADMIN
    )
    checklist.open_competence(PERIOD, actor=UPLOADER)
    # Estado mínimo para P5: todos os itens aceitos (a decisão
    # canônica já é exercida nas suítes P2/validations; aqui o foco
    # é o envelope governado).
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
    # P3 vigente (cutoff + fontes + conciliação) — finalize exige
    # readiness real, como no fluxo E2E canônico.
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
        "knowledge": ClaraKnowledgeRepository(),
        "proposals": ClaraProposalRepository(),
        "writes": ClaraGovernedWrites(),
        "version_id": version_id,
    }


def _item(env, item_key: str) -> dict:
    items = env["checklist"].list_competence_items(PERIOD)
    return next(i for i in items if i["item_key"] == item_key)


# == Knowledge base ========================================================


def test_knowledge_ingest_and_retrieve_with_citation(env):
    repo = env["knowledge"]
    repo.register_source(
        source_id="test-doc-01",
        source_type="DOCUMENT",
        name="Documento de teste",
        source_version="abc123",
        source_hash="h" * 64,
        origin_authority="OWNER",
    )
    item = repo.ingest_item(
        source_id="test-doc-01",
        topic="paridade-monetaria",
        title="Paridade monetária exata",
        content=(
            "A conciliação P3 exige divergência monetária exatamente "
            "igual a zero — qualquer centavo bloqueia o readiness."
        ),
        business_step="P3",
        related_report_ids=["R04"],
        evidence_classification="APPROVED_RULE",
        citation_locator={
            "key": "doc.md::secao-paridade",
            "document": "doc.md",
            "heading_path": "Regras > Paridade",
        },
    )
    assert item["status"] == "PUBLISHED"

    hits = repo.search(query="divergência monetária")
    assert any(
        h["knowledge_id"] == item["knowledge_id"] for h in hits
    )
    hit = next(
        h for h in hits if h["knowledge_id"] == item["knowledge_id"]
    )
    assert hit["citation_locator"]["document"] == "doc.md"
    assert hit["evidence_classification"] == "APPROVED_RULE"

    fetched = repo.get_item(str(item["knowledge_id"]))
    assert "Paridade" in fetched["title"]
    assert fetched["source_name"] == "Documento de teste"


def test_knowledge_internal_only_never_leaks_to_portal(env):
    repo = env["knowledge"]
    repo.register_source(
        source_id="test-internal",
        source_type="CONTRACT",
        name="Contrato interno",
        origin_authority="OWNER",
    )
    secret = repo.ingest_item(
        source_id="test-internal",
        topic="segredo",
        title="Nota interna restrita",
        content="Detalhe interno que não pode sair para o Portal.",
        evidence_classification="TO_INVENTORY",
        access_scope="INTERNAL_ONLY",
        citation_locator={"key": "k1", "document": "internal.md"},
    )
    hits = repo.search(query="restrita", access_scope="PORTAL_ACCESS")
    assert not any(
        h["knowledge_id"] == secret["knowledge_id"] for h in hits
    )
    hits_manage = repo.search(
        query="restrita", access_scope="PORTAL_MANAGE"
    )
    assert not any(
        h["knowledge_id"] == secret["knowledge_id"] for h in hits_manage
    )
    with pytest.raises(KnowledgeNotFound):
        repo.get_item(
            str(secret["knowledge_id"]),
            access_scope="PORTAL_ACCESS",
        )


def test_knowledge_dedup_and_supersede(env):
    repo = env["knowledge"]
    repo.register_source(
        source_id="test-supersede",
        source_type="DOCUMENT",
        name="Doc com revisão",
        origin_authority="OWNER",
    )
    locator = {"key": "doc2.md::s1", "document": "doc2.md"}
    v1 = repo.ingest_item(
        source_id="test-supersede",
        topic="t",
        title="Versão 1",
        content="Conteúdo original da seção.",
        citation_locator=locator,
    )
    again = repo.ingest_item(
        source_id="test-supersede",
        topic="t",
        title="Versão 1",
        content="Conteúdo original da seção.",
        citation_locator=locator,
    )
    assert again.get("_deduplicated") is True
    v2 = repo.ingest_item(
        source_id="test-supersede",
        topic="t",
        title="Versão 2",
        content="Conteúdo revisado da seção.",
        citation_locator=locator,
    )
    assert v2.get("_superseded") is True
    hits = repo.search(query="Conteúdo", topic="t")
    ids = [h["knowledge_id"] for h in hits]
    assert v2["knowledge_id"] in ids
    assert v1["knowledge_id"] not in ids  # SUPERSEDED não retorna


def test_corpus_version_publish(env):
    repo = env["knowledge"]
    corpus = repo.publish_corpus_version(
        actor="test-runner", manifest={"run": "pg-test"}
    )
    assert corpus["item_count"] > 0
    assert repo.current_corpus_version()["corpus_version_id"] == (
        corpus["corpus_version_id"]
    )


def test_segment_markdown_heading_paths():
    text = "# Título\n\nintro\n\n## Seção A\n\ncorpo A\n\n## Seção B\n\ncorpo B\n"
    segs = segment_markdown(text)
    assert len(segs) == 3
    assert segs[1].heading_path == "Título > Seção A"
    assert segs[2].content.strip() == "corpo B"


# == Governed writes (PREPARE → ACT) =======================================


def test_prepare_has_no_business_side_effect(env):
    writes = env["writes"]
    before = env["pkg"].list_packages(
        PERIOD, viewer=ADMIN, is_manage=True
    )
    proposal = writes.prepare(
        capability="clarification.open",
        params={
            "period": PERIOD,
            "package_version_id": env["version_id"],
            "question": "Confirma a amostra de conciliação?",
            "area": "CONTABIL",
        },
        actor_sub=REVIEWER_C,
    )
    after = env["pkg"].list_packages(
        PERIOD, viewer=ADMIN, is_manage=True
    )
    assert before == after
    assert proposal["proposal_handle"]
    assert proposal["execution_policy"] == "confirm_before_act"
    assert "clarification" not in str(
        env["pkg"].get_package(
            PERIOD, env["pkg"].list_packages(
                PERIOD, viewer=ADMIN, is_manage=True
            )["packages"][0]["package_id"],
            viewer=ADMIN, is_manage=True,
        ).get("clarifications") or []
    )


def test_commit_wrong_actor_rejected(env):
    writes = env["writes"]
    proposal = writes.prepare(
        capability="clarification.open",
        params={
            "period": PERIOD,
            "package_version_id": env["version_id"],
            "question": "Pergunta do reviewer",
            "area": "CONTABIL",
        },
        actor_sub=REVIEWER_C,
    )
    with pytest.raises(ProposalActorMismatch):
        writes.commit(
            handle=proposal["proposal_handle"], actor_sub=OUTSIDER
        )


def test_commit_expired_proposal_rejected(env):
    writes = env["writes"]
    proposal = writes.prepare(
        capability="clarification.open",
        params={
            "period": PERIOD,
            "package_version_id": env["version_id"],
            "question": "Pergunta expirada",
            "area": "CONTABIL",
        },
        actor_sub=REVIEWER_C,
    )
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE controllership_finance.clara_proposal
               SET expires_at = %s
             WHERE handle_hash = %s
            """,
            (
                datetime.now(timezone.utc) - timedelta(minutes=1),
                handle_hash(proposal["proposal_handle"]),
            ),
        )
    with pytest.raises(ProposalExpired):
        writes.commit(
            handle=proposal["proposal_handle"], actor_sub=REVIEWER_C
        )


def test_commit_executes_and_verifies_outcome(env):
    writes = env["writes"]
    proposal = writes.prepare(
        capability="clarification.open",
        params={
            "period": PERIOD,
            "package_version_id": env["version_id"],
            "question": "Confirma evidência da filial 01?",
            "area": "CONTABIL",
        },
        actor_sub=REVIEWER_C,
    )
    result = writes.commit(
        handle=proposal["proposal_handle"], actor_sub=REVIEWER_C
    )
    assert result["executed"] is True
    assert result["result"]["clarification_id"]
    # Pós-condição visível pelo mesmo leitor que o Portal usa.
    state = env["pkg"].derive_closing_state(PERIOD)
    assert "open_clarification:CONTABIL" in state["blocking_reasons"]
    # Single-use: segundo commit é stale.
    with pytest.raises(ProposalConsumed):
        writes.commit(
            handle=proposal["proposal_handle"], actor_sub=REVIEWER_C
        )
    # Auditoria marcada com o canal MCP.
    with plugins_db_connect() as conn, conn.cursor(
        row_factory=None
    ) as cur:
        cur.execute(
            """
            SELECT detail->>'channel'
              FROM controllership_finance.closing_audit_event
             WHERE event_type = 'CLARA_GOVERNED_ACT'
             ORDER BY created_at DESC LIMIT 1
            """
        )
        row = cur.fetchone()
    assert row is not None and row[0] == "mcp/clara"


def test_commit_stale_proposal_rejected(env):
    writes = env["writes"]
    clarification_id = _open_clarification(env)
    proposal = writes.prepare(
        capability="clarification.resolve",
        params={
            "period": PERIOD,
            "clarification_id": clarification_id,
            "response": "Resposta selada.",
        },
        actor_sub=ADMIN,
    )
    # Mudança externa entre PREPARE e ACT: a clarification é
    # resolvida diretamente pelo fluxo canônico — a proposta selada
    # não pode executar sobre o estado novo.
    env["pkg"].resolve_clarification(
        PERIOD,
        clarification_id,
        actor=ADMIN,
        response="Resolvido fora da CLARA.",
    )
    with pytest.raises((ProposalStale, ChecklistDomainError)):
        writes.commit(
            handle=proposal["proposal_handle"], actor_sub=ADMIN
        )


def _open_clarification(env) -> str:
    clarif = env["pkg"].open_clarification(
        PERIOD,
        env["version_id"],
        actor=REVIEWER_C,
        question="Pergunta para o teste de staleness",
        area="CONTABIL",
    )
    return str(clarif["clarification_id"])


def test_prepare_unknown_capability_rejected(env):
    with pytest.raises(UnknownCapability):
        env["writes"].prepare(
            capability="totvs.write_stock",
            params={"period": PERIOD},
            actor_sub=ADMIN,
        )


def test_act_delegates_domain_rules_fail_closed(env):
    """O ACT nunca contorna as regras da BFF: reviewer de área errada
    recebe o erro tipado de domínio (ReviewerNotAssigned), não um
    sucesso fabricado."""
    writes = env["writes"]
    proposal = writes.prepare(
        capability="review.record_decision",
        params={
            "period": PERIOD,
            "package_version_id": env["version_id"],
            "area": "FISCAL",
            "outcome": "ACCEPTED",
        },
        actor_sub=REVIEWER_C,
    )
    with pytest.raises(ChecklistDomainError) as excinfo:
        writes.commit(
            handle=proposal["proposal_handle"], actor_sub=REVIEWER_C
        )
    assert excinfo.value.code in {
        "reviewer_not_assigned",
        "reviewer_not_eligible",
    }
