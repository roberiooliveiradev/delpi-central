# SURI OTD Canonical Parity Fix — Execution Ledger

TASK: SUPPLIES-OTD-STRATEGIC-INDICATORS-CANONICAL-PARITY-FIX-001
BASE_HEAD: a8e7a4e903 · CODE_SHA: fdd4699395 · DOCS_SHA: (push)
GO: Product Owner explicit — corrigir consumidor divergente

## Root cause

OtdAggregateService computava otdPct=_mean(per_branch_pct) —
média simples de percentuais, método não homologado. O realizado
consolidado oficial do SI = source_consolidated do producer
(api-delpi branch=None), ponderado por denominadores reais.

## Fix (minimal diff, owner=supplies-api)

otd_aggregate_service.py: escopo consolidado agora chama
get_otd(branch=None) — mesmo contrato que o SI usa — e publica
otdPct=source_consolidated + onTime/total consolidados reais
(362/384-style counts) + consolidationMethod (additive field).
Single-branch inalterado. Falha do consolidado → partialFailure
+ otdPct=None (não fabrica média). byBranch preservado.

## Runtime proof (user, OAuth real)

AGG_CONS 08-04→11-02: otdPct=91.12, method=source_consolidated,
  branches {95.86, 88.14} — ERA 92.00 (média)
SEP_CONS 2026-09:    otdPct=94.27 = SI oficial = tela do PO
AGG_B01:             otdPct=95.86 method=branch (inalterado)

PARITY: SI=Overview=OTDpage=SURI = 91.12/94.27 ✓
TESTS: ~429 green (application+interface); teste de paridade
  assimétrico (86.67≠85.00) prova o método
MCP_TOOL_COUNT=5 inalterado · AUTHZ/escopo preservados
ROLLBACK: infra-supplies-mcp:pre-otd-fix-rollback
