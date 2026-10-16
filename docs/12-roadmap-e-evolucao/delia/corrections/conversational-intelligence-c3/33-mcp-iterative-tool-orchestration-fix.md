# 33 — MCP Iterative Tool Orchestration Fix

**TASK:** `DELIA-C3-MCP-ITERATIVE-TOOL-ORCHESTRATION-FIX-01`  
**MODE:** minimal EXTEND — governed LLM index probe + validated continuation  
**STATUS:** `FIX_EVIDENCE_RECORDED` · `STAGE_03_ACCEPTED=NO`

---

## 1. Gargalo

Após RW-S03-01, `_requires_owner_vocabulary` só abre DISCOVERY para envelopes opacos. Capabilities READ com identificador opcional (ex.: guia cujo contrato declara “omit → index”) ficavam em `plan=direct`; o modelo inventava o identificador e o owner rejeitava.

## 2. Reuse

| Mecanismo | Decisão |
|---|---|
| Semantic select / `_build_plan` / `_build_arguments` / Evidence / Policy | REUSE |
| Opaque-envelope + same-group DISCOVERY | REUSE (inalterado) |
| RW-S03-01 (required free string ≠ discovery) | PRESERVED |
| Self-index probe (eligible + model `probe_index`) | **EXTEND** |
| Novo planner / registry / hardcode TÉO | **NO** |

## 3. Menor alteração

`orchestration.py`:

- `INDEX_PROBE_INSTRUCTION` (v10) — modelo propõe `probe_index`.
- `_eligible_self_index_probe` — READ/ANALYSIS, sem required, string livre opcional, não envelope.
- Se elegível e `probe_index=true`: invoke `{}` → `owner_vocabulary` → arguments → segundo READ.
- Envelope DISCOVERY peer permanece prioritário quando aplicável.

## 4. Testes

- `tests/test_mcp_iterative_index_probe.py` — Orion unseen MCP (index→guide); search required sem probe; `probe_index=false`.
- Stage 03 / envelope / TÉO analyze regression preservados.

## 5. Live SSH

Registrado no ledger §6.209 após deploy do SHA desta correção (MESSAGE-only; zero ACT).

## 6. Outcome

```text
REUSE_DECISION=EXTEND
NEW_PLANNER=NO NEW_REGISTRY=NO PROVIDER_HARDCODE=NO
STAGE_03_ACCEPTED=NO
C3_EXECUTED=NO
NEXT=INDEPENDENT_ARCHITECTURE_REVIEW
```
