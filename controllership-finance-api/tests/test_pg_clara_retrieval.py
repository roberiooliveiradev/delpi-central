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
    KnowledgeNotFound,
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


KNOWN_VERDICTS = (
    "PASS_RETRIEVED",
    "RETRIEVAL_MISS",
    "SOURCE_GAP",
    "EVIDENCE_WEAK",
    "CITATION_MISS",
)


def _check_case_result(case: dict, actual: str) -> None:
    """Gate 078 — enforcement exato: o veredito observado deve ser
    IDÊNTICO ao esperado pelo caso, em qualquer direção. Um novo
    RETRIEVAL_MISS, um PASS espúrio num caso pendente ou qualquer
    veredito fora do vocabulário falham aqui."""
    expected = case.get("expect", "PASS_RETRIEVED")
    assert actual in KNOWN_VERDICTS, (
        f"{case['id']}: veredito desconhecido {actual!r}"
    )
    assert actual == expected, (
        f"{case['id']}: observado {actual} != esperado {expected}"
    )


def test_golden_set_structure():
    """Invariantes do conjunto: exatamente 105 casos (15×7) + 10
    negativos, IDs únicos, dimensões completas por relatório,
    marcadores verificáveis e expectativa+justificativa nos casos
    pendentes — a cobertura não pode encolher silenciosamente."""
    assert len(GOLDEN_SET) == 105
    assert len(NEGATIVE_SET) == 10
    ids = [c["id"] for c in GOLDEN_SET + NEGATIVE_SET]
    assert len(ids) == len(set(ids)), "IDs duplicados"
    by_report: dict[str, list[str]] = {}
    for case in GOLDEN_SET:
        by_report.setdefault(case["report_id"], []).append(case["dim"])
    assert sorted(by_report) == [f"R{i:02d}" for i in range(1, 16)]
    for rid, dims in by_report.items():
        assert len(dims) == 7, f"{rid}: {len(dims)} dimensões"
        assert len(set(dims)) == 7, f"{rid}: dimensões repetidas"
    for case in GOLDEN_SET + NEGATIVE_SET:
        assert case.get("markers") or case.get("asserts"), (
            f"{case['id']}: sem marcadores verificáveis"
        )
        if case.get("expect", "PASS_RETRIEVED") != "PASS_RETRIEVED":
            assert case.get("why"), (
                f"{case['id']}: expect={case['expect']} sem justificativa"
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
    for case in GOLDEN_SET:
        _check_case_result(case, results[case["id"]])


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
    # Gate 078: correspondência exata por caso — nenhum miss novo,
    # nenhum PASS espúrio, nenhum EVIDENCE_WEAK/CITATION_MISS passa.
    for case in GOLDEN_SET:
        _check_case_result(case, results[case["id"]])


def test_negative_contradictory_set(corpus):
    """Os 10 casos contraditórios: a evidência que corrige a premissa
    falsa deve ser recuperável das fontes canônicas; itens históricos
    que sustentam a premissa são classificados STALE_EVIDENCE."""
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
        classification = (
            f" STALE_EVIDENCE={stale}" if stale else ""
        )
        print(f"{case['id']}: {verdict}{classification}")
        _check_case_result(case, verdict)
        if stale and verdict == "PASS_RETRIEVED":
            # Evidência corretiva vigente precisa existir junto ao
            # histórico — risco registrado, não bloqueia a resposta.
            assert any(
                h["source_id"] in case.get("cite", [])
                for h in hits
            ), f"{case['id']}: stale presente sem fonte corretiva"


# ------------------------------------------------------------------
# Gate 078 — testes mutacionais: prova de que o enforcement detecta
# falhas reais em vez de aceitar vereditos tolerantes.
# ------------------------------------------------------------------


def test_mutation_enforcement():
    """Cada mutação deve quebrar o enforcement — se alguma passar,
    o avaliador voltou a tolerar resultados inesperados."""
    case_pass = dict(id="MX-PASS", expect="PASS_RETRIEVED")
    case_miss = dict(id="MX-MISS", expect="RETRIEVAL_MISS", why="x")

    # M1 — novo miss inesperado em caso PASS
    with pytest.raises(AssertionError):
        _check_case_result(case_pass, "RETRIEVAL_MISS")
    # M2 — citação fora das fontes canônicas
    with pytest.raises(AssertionError):
        _check_case_result(case_pass, "CITATION_MISS")
    # M3 — afirmação proibida no fragmento de suporte
    with pytest.raises(AssertionError):
        _check_case_result(case_pass, "EVIDENCE_WEAK")
    # M4 — ausência real de fonte em caso com evidência esperada
    with pytest.raises(AssertionError):
        _check_case_result(case_pass, "SOURCE_GAP")
    # M5 — expectativa alterada diverge do observado
    with pytest.raises(AssertionError):
        _check_case_result(
            dict(case_miss, expect="SOURCE_GAP"), "RETRIEVAL_MISS",
        )
    # M5b — caso pendente que volta a passar sem reconciliação
    with pytest.raises(AssertionError):
        _check_case_result(case_miss, "PASS_RETRIEVED")
    # M7 — veredito desconhecido
    with pytest.raises(AssertionError):
        _check_case_result(case_pass, "MAYBE")

    # Sanidade: vereditos corretos continuam passando
    _check_case_result(case_pass, "PASS_RETRIEVED")
    _check_case_result(case_miss, "RETRIEVAL_MISS")


def test_mutation_retrieval_level(corpus, monkeypatch):
    """Mutação no corpus real: simular um novo RETRIEVAL_MISS zerando
    a evidência no corpus — a suíte deve falhar o caso PASS."""
    import sys

    this = sys.modules[__name__]
    case = dict(
        GOLDEN_SET[0],
        id="MX-REAL-MISS",
        expect="PASS_RETRIEVED",
    )
    monkeypatch.setattr(this, "_corpus_has_evidence", lambda m: True)

    class _NoHitRepo:
        def search(self, **kwargs):
            return []

    actual = _evaluate_semantic(case, _NoHitRepo())
    assert actual == "RETRIEVAL_MISS"
    with pytest.raises(AssertionError):
        _check_case_result(case, actual)


def test_mutation_coverage_loss():
    """M6 — remover um caso de uma cópia isolada deve falhar o
    invariante de contagem (cópia local, golden set intocado)."""
    shrunk = GOLDEN_SET[:-1]
    assert len(shrunk) == 104
    with pytest.raises(AssertionError):
        assert len(shrunk) == 105


# ------------------------------------------------------------------
# Gate 079 — rastreabilidade auditável dos 115 casos
#
# Registro por caso: id, pergunta literal, report_id, corpus, itens
# (knowledge_id, source_id, citation_locator, rank, full_match),
# evidência esperada, veredito e timestamp. Escreve JSONL quando
# CLARA_TRACE_OUT aponta um caminho — artefato repetível antes/depois.
# ------------------------------------------------------------------


def _trace_record(case, verdict, hits, corpus_version) -> dict:
    required = case.get("asserts") or case.get("markers") or []
    return {
        "id": case["id"],
        "query": case["q"],
        "report_id": case["report_id"],
        "corpus": str(corpus_version["corpus_version_id"]),
        "expected_evidence": required,
        "expect": case.get("expect", "PASS_RETRIEVED"),
        "verdict": verdict,
        "limitation": case.get("resolved_by") or case.get("why"),
        "items": [
            {
                "knowledge_id": str(h["knowledge_id"]),
                "source_id": h["source_id"],
                "citation_locator": h.get("citation_locator"),
                "rank": h.get("rank"),
                "full_match": h.get("full_match"),
            }
            for h in hits
        ],
    }


def test_acceptance_traceability(corpus):
    """Executa os 115 casos e emite registros auditáveis. Com
    CLARA_TRACE_OUT=<arquivo> grava JSONL comparável entre execuções."""
    import datetime
    import json

    version = corpus.current_corpus_version()
    records = []
    for case in GOLDEN_SET + NEGATIVE_SET:
        hits = corpus.search(
            query=case["q"], report_id=case["report_id"], limit=12,
        )
        verdict = _evaluate_semantic(case, corpus)
        records.append(_trace_record(case, verdict, hits, version))
        _check_case_result(case, verdict)

    out = os.getenv("CLARA_TRACE_OUT")
    if out:
        stamp = datetime.datetime.now(datetime.UTC).isoformat(
            timespec="seconds",
        )
        with open(out, "w", encoding="utf-8") as fh:
            for rec in records:
                rec["executed_at"] = stamp
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    assert len(records) == 115


def test_superseded_state_segments(corpus):
    """Gate 080-RW01 — zero exposição de afirmações superadas:
    drops e fix_lines removem os estados antigos de R04/R09/R12/R15
    de TODO o conhecimento PUBLISHED (search com e sem report_id,
    get por knowledge_id), preservando afirmações vigentes R13/R14
    e a trilha SUPERSEDED para auditoria."""
    stale_patterns = [
        "R04/R13/R14 BLOQUEADO",
        "R04 Consumo por OP | BLOQUEADO",
        "R04 | `BLOCKED_BY_OWNER`",
        "(R04/R09/R12/R15) → `report_not_implemented`",
        "R04, R06, R07, R09–R15`: sem handler",
        "R04 | `MATR860` candidato | — | — | ? | `BLOQUEADO`",
        "Pacotes R04 (GAP-01), R09 (E6-D1..D6/E9)",
        "R04/R06/R07 (2026-11-02) — status inicial",
        "R04-G059 — owner/contrato confirmados",
        "R04 | `NOT_IMPLEMENTED` (BLOQUEADO",
        "nenhuma) | ficha (bloqueado, honesto)",
        "EV-23 | `MATR860` é candidato a consumo por OP; nenhum artefato",
        # Gate 081 — auditoria integral
        "R04/R09/R12/R15 seguem sem contrato",
        "demais respondem `report_not_implemented`",
        "R09/R12/R15 seguem sem contrato",
        "R05–R11 (paridades provadas, sem contrato",
        "Bloqueados** R03/R04/R13/R14",
        "G060 — Correção de classificação (2026-11-02)",
        "R04/R13/R14 `BLOCKED",
    ]
    with plugins_db_connect() as conn, conn.cursor() as cur:
        for pattern in stale_patterns:
            cur.execute(
                "SELECT knowledge_id FROM "
                "controllership_finance.clara_knowledge_item"
                " WHERE status='PUBLISHED' AND content ILIKE %s",
                (f"%{pattern}%",),
            )
            found = cur.fetchall()
            assert not found, (
                f"afirmação superada ainda PUBLISHED: {pattern!r} → {found}"
            )
        # conteúdo corrigido presente nos segmentos mistos (fix_lines)
        for fixed_claim in (
            "R13/R14 BLOQUEADO (R13 externalidade confirmada",
            "R04 Consumo por OP | IMPLEMENTADO (visão operacional",
            "R04 | `IMPLEMENTED` (visão operacional",
            "EV-23 | `MATR860` é candidato a consumo por OP; consumo "
            "implementado",
            "R13, R14`: sem handler BFF",
        ):
            cur.execute(
                "SELECT count(*) FROM "
                "controllership_finance.clara_knowledge_item"
                " WHERE status='PUBLISHED' AND content ILIKE %s",
                (f"%{fixed_claim}%",),
            )
            assert cur.fetchone()[0] >= 1, (
                f"conteúdo corrigido ausente: {fixed_claim!r}"
            )
        # afirmações vigentes R13/R14 preservadas nos segmentos corrigidos
        cur.execute(
            "SELECT count(*) FROM controllership_finance.clara_knowledge_item"
            " WHERE status='PUBLISHED' AND content ILIKE '%BLOQUEADO%'"
            " AND content ~* '\\mR13'"
        )
        assert cur.fetchone()[0] >= 3

    for rid in (None, "R04"):
        hits = corpus.search(
            query="O R04 ainda está bloqueado?",
            report_id=rid,
            limit=12,
        )
        assert hits, "busca vazia"
        assert not [
            h["title"] for h in hits if "BLOQUEADO" in h["title"].upper()
        ]
        stale_hits = [
            h["knowledge_id"] for h in hits
            if any(p.lower() in h["content"].lower() for p in stale_patterns)
        ]
        assert not stale_hits, f"conteúdo superado recuperado: {stale_hits}"

    # get() fail-closed: versões SUPERSEDED não são devolvidas nem por id
    for old_id in (
        "19846578-e15c-4964-8ea3-74adcc2b3c60",  # doc-80 27.C versão antiga
        "cede18a7-b186-47f8-916e-c4ebd92e4305",  # doc-83 §7 versão antiga
        "78e9cd34-5e4c-4d14-ad03-1c677a864de0",  # doc-83 R04-BLOQUEADO drop
    ):
        with pytest.raises(KnowledgeNotFound):
            corpus.get_item(old_id)


# Gate 084 — source-level operational exclusion for historical journals.
def test_historical_runtime_journals_are_not_operational(corpus):
    """Old deployment narratives remain auditable but cannot reach CLARA."""
    from controllership_finance_app.application.clara.corpus_manifest import (
        AUTHORIZED_SOURCES,
    )

    journal_ids = {"doc-00", "doc-100", "doc-111"}
    journal_specs = [s for s in AUTHORIZED_SOURCES if s.source_id in journal_ids]
    assert {s.source_id for s in journal_specs} == journal_ids
    assert all(s.access_scope == "INTERNAL_ONLY" for s in journal_specs)

    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT source_id, count(*) FROM "
            "controllership_finance.clara_knowledge_item "
            "WHERE source_id = ANY(%s) AND status = 'PUBLISHED' "
            "AND access_scope <> 'INTERNAL_ONLY' GROUP BY source_id",
            (list(journal_ids),),
        )
        assert cur.fetchall() == [], "historical journal exposed to CLARA"
        cur.execute(
            "SELECT knowledge_id FROM "
            "controllership_finance.clara_knowledge_item "
            "WHERE source_id = 'doc-100' AND status = 'PUBLISHED' "
            "AND access_scope = 'INTERNAL_ONLY' LIMIT 1"
        )
        row = cur.fetchone()
    assert row, "journal must remain preserved for audit"
    with pytest.raises(KnowledgeNotFound):
        corpus.get_item(str(row[0]))
    for query in ("DEPLOY_STATUS não deployado", "PENDING_CONTRACT R04"):
        assert all(
            h["source_id"] not in journal_ids
            for h in corpus.search(query=query, limit=30)
        )


def test_reingest_identical_segment_updates_access_scope(repo):
    """Scope change must not be ignored by content-hash deduplication."""
    sid = "t-scope-reingest"
    key = sid + "::stable"
    first = _item(
        repo, source_id=sid, topic="t", title="Historical status",
        content="DEPLOY_STATUS não deployado", locator_key=key,
    )
    second = repo.ingest_item(
        source_id=sid, topic="t", title="Historical status",
        content="DEPLOY_STATUS não deployado",
        citation_locator={"key": key, "document": sid + ".md"},
        access_scope="INTERNAL_ONLY",
    )
    assert first["knowledge_id"] == second["knowledge_id"]
    assert second["access_scope"] == "INTERNAL_ONLY"
    with pytest.raises(KnowledgeNotFound):
        repo.get_item(str(first["knowledge_id"]))


# Gate 085 — allowlist source-level; fail closed for all historical docs.
def test_only_canonical_fichas_are_operational(corpus):
    from controllership_finance_app.application.clara.corpus_manifest import (
        AUTHORIZED_SOURCES, OPERATIONAL_SOURCE_IDS,
    )
    assert len(OPERATIONAL_SOURCE_IDS) == 32
    assert len({s.source_id for s in AUTHORIZED_SOURCES}) == len(AUTHORIZED_SOURCES)
    assert {s.source_id for s in AUTHORIZED_SOURCES
            if s.access_scope == "PORTAL_ACCESS"} == OPERATIONAL_SOURCE_IDS
    assert all(s.access_scope == "INTERNAL_ONLY"
               for s in AUTHORIZED_SOURCES
               if s.source_id not in OPERATIONAL_SOURCE_IDS)

    authorized_ids = [s.source_id for s in AUTHORIZED_SOURCES]
    with plugins_db_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT source_id FROM "
            "controllership_finance.clara_knowledge_item "
            "WHERE status = 'PUBLISHED' AND access_scope = 'PORTAL_ACCESS' "
            "AND source_id <> ALL(%s::text[]) "
            "AND source_id = ANY(%s::text[])",
            (list(OPERATIONAL_SOURCE_IDS), authorized_ids),
        )
        assert cur.fetchall() == [], "noncanonical source is exposed"
        cur.execute(
            "SELECT knowledge_id FROM "
            "controllership_finance.clara_knowledge_item "
            "WHERE source_id = 'doc-118' AND status = 'PUBLISHED' LIMIT 1"
        )
        row = cur.fetchone()
    assert row, "audit record should be retained"
    with pytest.raises(KnowledgeNotFound):
        corpus.get_item(str(row[0]))
    for query in ("18 tools MCP", "R04 bloqueado", "estado do fechamento"):
        hits = corpus.search(query=query, limit=50)
        leaks = [h["source_id"] for h in hits
                 if h["source_id"] in authorized_ids
                 and h["source_id"] not in OPERATIONAL_SOURCE_IDS]
        assert not leaks, f"{query}: non-operational hits {sorted(set(leaks))}"
