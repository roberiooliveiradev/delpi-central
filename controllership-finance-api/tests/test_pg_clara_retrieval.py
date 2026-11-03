"""Gate 076 — recuperação da base de conhecimento CLARA.

Dois níveis:

1. Fixture controlada — prova o contrato de recuperação: AND
   preferencial, fill OR aditivo marcado ``full_match=False``,
   SUPERSEDED/escopo/relatório fora do universo continuam zerados.
2. Golden set R01–R15 (105 casos) — ingere o manifest real no banco
   efêmero e classifica cada caso ``PASS_RETRIEVED | RETRIEVAL_MISS |
   SOURCE_GAP``, separando falso negativo de busca de lacuna real de
   fonte.

Ativado com CF_TEST_PG_* + CF_TEST_PG_CLUSTER=test +
CF_TEST_PG_ALLOW_DESTRUCTIVE=1.
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import psycopg
import pytest

from controllership_finance_app.application.clara.corpus_ingestion import (
    ingest_manifest,
)
from controllership_finance_app.application.clara.corpus_manifest import (
    AUTHORIZED_SOURCES,
)
from controllership_finance_app.infrastructure.persistence import (
    migrations_runner as mr,
)
from controllership_finance_app.infrastructure.persistence.clara_knowledge_repository import (  # noqa: E501
    ClaraKnowledgeRepository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (  # noqa: E501
    plugins_db_connect,
)

from clara_golden_set_r01_r15 import GOLDEN_SET, NEGATIVE_SET

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

from pg_test_isolation import (  # noqa: E402
    assert_safe_test_prefix,
    create_owned_test_database,
    drop_owned_test_database,
    require_test_environment,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
def repo(_configure_db):
    mr.run_migrations()
    return ClaraKnowledgeRepository()


@pytest.fixture(scope="module")
def corpus(repo):
    """Corpus real do manifest — compartilhado pelo golden set."""
    outcome = ingest_manifest(
        AUTHORIZED_SOURCES,
        docs_root=_REPO_ROOT,
        repository=repo,
        publish=True,
        actor="test-g076",
    )
    assert outcome["failed"] == 0, outcome["failures"]
    return repo


def _item(repo, *, source_id, topic, title, content, rids=None,
          scope="PORTAL_ACCESS", locator_key=None):
    repo.register_source(
        source_id=source_id, source_type="DOCUMENT", name=source_id,
    )
    return repo.ingest_item(
        source_id=source_id,
        topic=topic,
        title=title,
        content=content,
        related_report_ids=rids or [],
        citation_locator={
            "key": locator_key or f"{source_id}::{uuid.uuid4().hex[:8]}",
            "document": f"{source_id}.md",
        },
        access_scope=scope,
    )


# ------------------------------------------------------------------
# Fixture controlada — contrato de recuperação
# ------------------------------------------------------------------


def test_and_preferred_or_fill_is_additive(repo):
    """AND mantém posição/ordem; fill OR é anexado depois, marcado."""
    _item(
        repo, source_id="t-and", topic="t", title="Completo",
        content="O Kardex exclui estornos quando MV_D3ESTOR ativo.",
        rids=["R06"],
    )
    partial = _item(
        repo, source_id="t-partial", topic="t", title="Parcial",
        content="Estornos do Kardex apenas.",
        rids=["R06"],
    )
    hits = repo.search(
        query="Kardex estornos MV_D3ESTOR",
        report_id="R06",
    )
    assert hits[0]["title"] == "Completo"
    assert hits[0]["full_match"] is True
    ids = [h["knowledge_id"] for h in hits]
    assert partial["knowledge_id"] in ids
    fill = next(
        h for h in hits if h["knowledge_id"] == partial["knowledge_id"]
    )
    assert fill["full_match"] is False


def test_or_fill_when_and_yields_zero(repo):
    """Consulta multi-conceito com termos em segmentos distintos
    deixa de retornar zero."""
    _item(
        repo, source_id="t-a", topic="t", title="A",
        content="Data de apontamento H6_DTAPONT dentro do período.",
        rids=["R04"],
    )
    _item(
        repo, source_id="t-b", topic="t", title="B",
        content="Ordenação sort_by na listagem de ordens.",
        rids=["R04"],
    )
    hits = repo.search(
        query="data apontamento sort_by ordenação", report_id="R04",
    )
    assert len(hits) == 2
    assert {h["full_match"] for h in hits} == {False}


def test_zero_when_no_lexeme_matches(repo):
    """Ausência real de evidência continua zerada — o fill não
    inventa resultado para termos sem correspondência."""
    _item(
        repo, source_id="t-c", topic="t", title="C",
        content="Relatório de fechamento mensal da controladoria.",
        rids=["R05"],
    )
    hits = repo.search(
        query="zzqxy unicorno inexistente total", report_id="R05",
    )
    assert hits == []


def test_report_id_filter_fail_closed_with_fill(repo):
    """report_id inexistente zera mesmo com termos presentes — o
    universo autorizado não é ampliado pelo fallback."""
    _item(
        repo, source_id="t-d", topic="t", title="D",
        content="Fechamento com MV_ULMES por filial.",
        rids=["R15"],
    )
    assert repo.search(query="MV_ULMES filial", report_id="R99") == []


def test_superseded_never_returned_by_fill(repo):
    """Versões SUPERSEDED não voltam nem pelo caminho OR."""
    _item(repo, source_id="t-s", topic="t", title="S", content="x")
    v1 = repo.ingest_item(
        source_id="t-s", topic="t", title="V1",
        content="Versão antiga com termo_unico_alfa.",
        citation_locator={"key": "t-s::k", "document": "t-s.md"},
    )
    v2 = repo.ingest_item(
        source_id="t-s", topic="t", title="V2",
        content="Versão nova com termo_unico_beta.",
        citation_locator={"key": "t-s::k", "document": "t-s.md"},
    )
    assert v2.get("_superseded") is True
    hits = repo.search(query="termo_unico_alfa beta")
    ids = [h["knowledge_id"] for h in hits]
    assert v1["knowledge_id"] not in ids


def test_internal_only_never_returned_by_fill(repo):
    """Escopo permanece fail-closed — INTERNAL_ONLY não vaza no fill."""
    secret = _item(
        repo, source_id="t-i", topic="t", title="I",
        content="Detalhe restrito com palavra_unica_gama.",
        scope="INTERNAL_ONLY",
    )
    hits = repo.search(
        query="palavra_unica_gama", access_scope="PORTAL_ACCESS",
    )
    assert all(h["knowledge_id"] != secret["knowledge_id"] for h in hits)


# ------------------------------------------------------------------
# Golden set — 105 casos contra o corpus real ingerido
# ------------------------------------------------------------------


def _corpus_has_evidence(markers: list[str]) -> bool:
    """Algum item PUBLISHED contém TODOS os markers (fonte existe?)."""
    clauses = " AND ".join("content ILIKE %s" for _ in markers)
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM controllership_finance.clara_knowledge_item"
            f" WHERE status='PUBLISHED' AND {clauses} LIMIT 1",
            tuple(f"%{m}%" for m in markers),
        )
        return cur.fetchone() is not None


def _evaluate(case, repo) -> str:
    hits = repo.search(
        query=case["q"], report_id=case["report_id"], limit=12,
    )
    for h in hits:
        content = h["content"].lower()
        if all(m.lower() in content for m in case["markers"]):
            return "PASS_RETRIEVED"
    return (
        "RETRIEVAL_MISS"
        if _corpus_has_evidence(case["markers"])
        else "SOURCE_GAP"
    )


def test_golden_set_105(corpus):
    results = {case["id"]: _evaluate(case, corpus) for case in GOLDEN_SET}
    for case in GOLDEN_SET:
        print(f"{case['id']}: {results[case['id']]}")
    misses = {k: v for k, v in results.items() if v == "RETRIEVAL_MISS"}
    gaps = {k: v for k, v in results.items() if v == "SOURCE_GAP"}
    print(
        f"SUMMARY: {len(results)} casos — "
        f"retrieved={sum(v == 'PASS_RETRIEVED' for v in results.values())}"
        f" retrieval_miss={len(misses)} source_gap={len(gaps)}"
    )
    if gaps:
        print("SOURCE_GAP:", sorted(gaps))
    # Todo caso deve bater a expectativa declarada — misses conhecidos
    # (limitação de ranking OR, DECISION_REQUIRED pendente) são
    # registrados no golden set; qualquer miss ou gap novo falha.
    unexpected = {
        cid: v
        for cid, v in results.items()
        if v != next(
            c for c in GOLDEN_SET if c["id"] == cid
        ).get("expect", "PASS_RETRIEVED")
    }
    assert not unexpected, f"resultados inesperados: {unexpected}"


# ------------------------------------------------------------------
# Gate 077 — aceitação semântica (nível evidência/citação)
#
# O canal conversacional real é o conector ChatGPT externo — não
# automatizável neste ambiente. O que se homologa aqui: a evidência
# recuperada é SUFICIENTE e LIMPA para uma resposta correta —
# fonte citável (`cite`), asserções exigidas (`asserts`/`markers`)
# e ausência de asserções enganosas no item de suporte (`forbids`).
# ------------------------------------------------------------------


def _evaluate_semantic(case, repo) -> str:
    hits = repo.search(
        query=case["q"], report_id=case["report_id"], limit=12,
    )
    required = case.get("asserts") or case.get("markers") or []
    forbids = [f.lower() for f in case.get("forbids", [])]
    cite = case.get("cite")
    supporting = None
    for h in hits:
        content = h["content"].lower()
        if all(
            re.search(
                r"(?<!\w)" + re.escape(m.lower()) + r"(?!\w)", content,
            )
            for m in required
        ):
            supporting = h
            break
    if supporting is not None:
        if any(f in supporting["content"].lower() for f in forbids):
            return "EVIDENCE_WEAK"
        if cite and supporting["source_id"] not in cite:
            # evidência existe mas fora das fontes canônicas aceitáveis
            return "CITATION_MISS"
        return "PASS_RETRIEVED"
    return (
        "RETRIEVAL_MISS"
        if _corpus_has_evidence(required)
        else "SOURCE_GAP"
    )


def test_semantic_acceptance_105(corpus):
    results = {
        case["id"]: _evaluate_semantic(case, corpus)
        for case in GOLDEN_SET
    }
    for case in GOLDEN_SET:
        print(f"{case['id']}: {results[case['id']]}")
    by = {}
    for v in results.values():
        by[v] = by.get(v, 0) + 1
    print("SEMANTIC SUMMARY:", by)
    allowed = {"PASS_RETRIEVED", "RETRIEVAL_MISS"}  # misses já triados
    unexpected = {
        cid: v
        for cid, v in results.items()
        if v not in allowed
        and v != next(
            c for c in GOLDEN_SET if c["id"] == cid
        ).get("expect", "PASS_RETRIEVED")
    }
    weak = {k: v for k, v in results.items() if v in ("EVIDENCE_WEAK", "CITATION_MISS")}
    assert not unexpected, f"vereditos inesperados: {unexpected}"
    assert not weak, f"evidência fraca/citação incorreta: {weak}"


def test_negative_contradictory_set(corpus):
    """Os 10 casos contraditórios: a evidência que corrige a premissa
    falsa deve ser recuperável das fontes canônicas; itens stale que
    sustentam a premissa são registrados como risco informacional."""
    for case in NEGATIVE_SET:
        verdict = _evaluate_semantic(case, corpus)
        hits = corpus.search(
            query=case["q"], report_id=case["report_id"], limit=12,
        )
        stale = [
            h["source_id"]
            for h in hits
            if h["source_id"] in case.get("stale_risk", [])
        ]
        print(
            f"{case['id']}: {verdict} stale_hits={stale}"
        )
        expect = case.get("expect", "PASS_RETRIEVED")
        assert verdict == expect, (
            f"{case['id']}: {verdict} != {expect}"
        )
