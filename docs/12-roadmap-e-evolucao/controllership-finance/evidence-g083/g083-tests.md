# G083 — Relatório de testes

| Suíte | Comando | Resultado |
|---|---|---|
| Auditoria semântica claim-level | `python tests/clara_semantic_audit.py` (AUDIT_MANUAL=g083 decisions) | 2.208 itens: 88 CV · 1.312 HIST · 237 NA · 571 UNVERIFIED · 0 REVIEW · 0 STALE; 13.479 claims |
| Adversarial (16 cenários + 3 defeitos corrigidos RW02) | `pytest tests/test_clara_semantic_audit_adversarial.py` | **16/16 PASS** |
| Golden set 105 + 10 negativos + guardas SUPERSEDED/INTERNAL/report_id | `pytest tests/test_pg_clara_retrieval.py` (banco efêmero + reingestão do manifest) | **15/15 PASS** |
| Varredura padrões superados | SQL ILIKE `stale_patterns` Gates 080/081 + G083 | 0 ocorrências PUBLISHED; 141 SUPERSEDED preservados |

Defeitos reais encontrados por evidência durante o gate: 1) `demais respondem report_not_implemented` (doc-121) — falhou no invariante Gate 081, corrigido; 2) variante `Bloqueados R03/R04/R13/R14` (doc-86 §9) — corrigida; 3) índice doc-00 Ciclo 2 com bloqueios datados — corrigido.
