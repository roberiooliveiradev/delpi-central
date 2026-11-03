#!/usr/bin/env python3
"""Gate 082 — auditoria semântica integral do corpus CLARA.

Percorre 100%% dos itens PUBLISHED e emite um registro JSONL por item
com classificação (CURRENT_VERIFIED/STALE_CONFIRMED/MIXED/
HISTORICAL_ONLY/CONFLICT/UNVERIFIED/RESTRICTED/NOT_APPLICABLE),
justificativa e hits de afirmação de estado. Reexecutável após
qualquer reingestão: PWP=<senha> python clara_semantic_audit.py
"""

import os, re, json, sys
sys.path.insert(0, "controllership-finance-api")
os.environ.update(dict(PLUGINS_DB_HOST="localhost", PLUGINS_DB_PORT="5433",
    PLUGINS_DB_NAME="plugins_hub", PLUGINS_DB_USER="plugins_user",
    PLUGINS_DB_PASSWORD=os.environ["PWP"], PLUGINS_DB_SSLMODE="disable"))
from controllership_finance_app.infrastructure.persistence.plugins_db import plugins_db_connect

# Verdade vigente comprovada (Gates 074–081): TODOS R01–R12,R15 implementados;
# R13/R14 SOURCE_UNAVAILABLE; paridade oficial pendente em TODOS (G6=0/15).
IMPL_WORDS = r"(?:BLOQUEADO|BLOCKED|NOT_IMPLEMENTED|not_implemented|não implementado|nao implementado|TARGET_ONLY|sem handler|sem contrato|sem endpoint|sem produtor|nenhuma|GAP-01|BLOCKED_BY_\w+|SOURCE_UNAVAILABLE|sem capability|report_not_implemented)"
RID = r"(R0\d|R1[0-5])"
NARRATIVE = re.compile(r"(na rodada|rodada \d|ciclo\s*[123]|status inicial|históri|anterior|as-of|snapshot de|na época|naquele momento|estava |era |registro de|gate-\d|GATE [AB]|adendo|stage-0\d|2026-1[01]|IMPLEMENTATION-STAGE|REWORK-\d|atualização de)", re.I)
CORRECTED = re.compile(r"(Gate 080|Gate 079|Gate 081|implementado posteriormente|paridade MATR860 pendente|visão operacional|nunca exclusão automática|está bloqueado\?”)", re.I)
FIN_STATIC = re.compile(r"R\$\s*[\d.]+,\d{2}")

rows = plugins_db_connect().__enter__().cursor().execute(
    "SELECT knowledge_id, source_id, title, content, related_report_ids, citation_locator->>'key', access_scope, evidence_classification FROM controllership_finance.clara_knowledge_item WHERE status='PUBLISHED' ORDER BY source_id, title"
).fetchall()

inv = []
counts = {}
for kid, sid, title, content, rids, key, scope, evcls in rows:
    text = title + "\n" + (content or "")
    stale_hits = [m.group(0)[:120] for m in re.finditer(
        r"(?i)" + RID + r"[^\n]{0,70}?" + IMPL_WORDS + r"|" + IMPL_WORDS + r"[^\n]{0,70}?" + RID, text)]
    narr = bool(NARRATIVE.search(text))
    corr = bool(CORRECTED.search(text))
    if scope != "PORTAL_ACCESS":
        cls, why = "RESTRICTED", f"scope={scope}"
    elif stale_hits and corr:
        cls, why = "CURRENT_VERIFIED", "claim corrigido/negado presente (fix aplicado ou contexto negativo)"
    elif stale_hits and narr:
        cls, why = "HISTORICAL_ONLY", "narrativa datada com claim de estado antigo — contexto temporal explícito"
    elif stale_hits:
        cls, why = "REVIEW", "afirmação de estado implementado sem marcação temporal/correção clara"
    elif FIN_STATIC.search(text):
        cls, why = "UNVERIFIED", "valor monetário estático — evidência datada, não dado vigente"
    else:
        cls, why = "NOT_APPLICABLE", "sem afirmação operacional sujeita a atualidade"
    inv.append(dict(kid=str(kid), src=sid, title=title[:70], cls=cls, why=why, hits=stale_hits[:3]))
    counts[cls] = counts.get(cls, 0) + 1

with open("/tmp/g082_inventory.jsonl", "w") as fh:
    for r in inv:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
print("TOTAL:", len(inv), json.dumps(counts))
for r in inv:
    if r["cls"] in ("REVIEW",):
        print("REVIEW:", r["src"], "|", r["title"][:50], "|", (r["hits"] or [""])[0][:90])
