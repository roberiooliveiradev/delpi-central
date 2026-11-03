"""Gate 082-RW02 — teste adversarial do auditor semântico.

Fixtures sintéticas isoladas (sem banco, sem corpus): provam que o
auditor detecta afirmações desatualizadas mesmo sem palavra-chave
óbvia, e que não gera falsos positivos nos casos legítimos.

Expectativas declaradas por cenário — não ajustadas para passar.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clara_semantic_audit import (  # noqa: E402
    _dated_context,
    _structural_profile,
    classify_item,
    extract_claims,
    verify_claim,
)


def _item(content, *, evcls="OWNER_REPORTED_VIA_PO", title="t",
          locator="doc-x::t"):
    return {
        "knowledge_id": "adv-" + str(abs(hash(content)) % 10**8),
        "source_id": "adv",
        "title": title,
        "content": content,
        "access_scope": "PORTAL_ACCESS",
        "evidence_classification": evcls,
        "related_report_ids": [],
        "locator": locator,
    }


def _run(item):
    dated = _dated_context(item)
    claims = extract_claims(item, dated)
    verdicts = [verify_claim(c["claim_text"], c["claim_type"])
                for c in claims]
    cls, _why = classify_item(item, claims, verdicts)
    return claims, verdicts, cls


def _cls_of(text, **kw):
    _c, v, _i = _run(_item(text, **kw))
    return v[0][3] if v else "NOT_APPLICABLE"


# 1. relatório implementado descrito como indisponível → STALE
def test_adv_implemented_as_unavailable():
    assert _cls_of("O relatório R04 está indisponível no Portal.") \
        == "STALE_CONFIRMED"


# 2. endpoint existente descrito como planejado → REVIEW
def test_adv_existing_endpoint_as_planned():
    assert _cls_of(
        "O endpoint de consumo por OP (R04) será implementado "
        "na próxima etapa."
    ) == "REVIEW"


# 3. capability existente descrita como ausente → STALE
def test_adv_capability_as_absent():
    assert _cls_of(
        "A CLARA não possui a capability "
        "production_order_consumption."
    ) == "STALE_CONFIRMED"


# 4. produtor/fonte incorretos → STALE
def test_adv_wrong_producer():
    assert _cls_of(
        "O R01 é produzido pela rotina MATR320."
    ) == "STALE_CONFIRMED"


# 5. regra de cálculo desatualizada → STALE
def test_adv_stale_calc_rule():
    assert _cls_of(
        "O fechamento mensal é executado automaticamente pelo "
        "sistema, sem intervenção."
    ) == "STALE_CONFIRMED"


# 6. filtro de consulta incorreto → STALE
def test_adv_wrong_filter():
    assert _cls_of(
        "A consulta operacional de baixas usa o eixo D2_EMISSAO "
        "por competência."
    ) == "STALE_CONFIRMED"


# 7. segmento misto — um claim correto + um superado → MIXED
def test_adv_mixed_segment():
    _c, _v, cls = _run(_item(
        "R13 permanece bloqueado por fonte externa.\n"
        "O relatório R04 está bloqueado sem handler."
    ))
    assert cls == "MIXED"


# 8. afirmação superada dentro de narrativa histórica → REVIEW
def test_adv_stale_in_dated_narrative():
    assert _cls_of(
        "Em 2026-10-23, o R04 estava bloqueado por ausência "
        "de artefato."
    ) == "REVIEW"


# 9. informação atual sem marcador de implementação → CURRENT_VERIFIED
def test_adv_current_unmarked():
    assert _cls_of(
        "R13 e R14 permanecem bloqueados por fonte externa."
    ) == "CURRENT_VERIFIED"


# 10. afirmação histórica legítima e datada → HISTORICAL_ONLY
def test_adv_legit_dated():
    assert _cls_of(
        "Em 2026-10-23, R13/R14 estavam bloqueados por "
        "externalidade."
    ) == "HISTORICAL_ONLY"


# 11. contrato TARGET ainda não implementado → NOT_APPLICABLE
def test_adv_target_unimplemented():
    assert _cls_of(
        "O endpoint /closing/futuro será implementado "
        "conforme o contrato TARGET."
    ) == "NOT_APPLICABLE"


# 12. dado monetário sem competência → UNVERIFIED
def test_adv_undated_money():
    assert _cls_of("O total apurado foi R$ 169.704,12.") \
        == "UNVERIFIED"


# 13. item sem afirmação operacional → NOT_APPLICABLE
def test_adv_structural_only():
    _c, _v, cls = _run(_item(
        "```sql\nSELECT D1_COD, D1_TOTAL FROM SD1010\n"
        "WHERE D1_FILIAL = '01'\n```\n"
        "| coluna | tipo |\n|---|---|\n"
    ))
    assert cls == "NOT_APPLICABLE"


# 14. documento antigo contradiz código vigente → STALE
def test_adv_old_doc_contradicts():
    assert _cls_of(
        "R04 não possui handler BFF nem contrato."
    ) == "STALE_CONFIRMED"


# 15. afirmação sem autoridade suficiente → UNVERIFIED/PENDING
def test_adv_unverifiable():
    _c, v, _i = _run(_item(
        "O relatório utiliza a fonte parametrizada pelo owner."
    ))
    assert v and v[0][3] == "UNVERIFIED"


# metadados do auditor — não é a mesma regex do G082
def test_adv_not_same_regex_as_g082():
    """O extrator emite claims tipadas — evidência por afirmação,
    não apenas classificação por match."""
    claims, verdicts, _c = _run(_item(
        "R05 usa MATR320 como produtor oficial."
    ))
    assert claims and verdicts
    for c, v in zip(claims, verdicts):
        assert c["claim_text"] and v[1] and v[2]
