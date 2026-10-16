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
- `_contract_declares_omit_returns_index` — sinal textual omit/omitted + index/available/list na descrição da capability (provider-neutral; sem field-name hardcode).
- Se elegível e (contrato omit→index **ou** `probe_index=true`): invoke `{}` → `owner_vocabulary` → arguments → segundo READ.
- `_post_self_index_argument_gaps`: após o índice, rejeita `{}` ou identificador inventado (fail closed / clarificação); impede re-fetch do índice como resposta “grounded”.
- Envelope DISCOVERY peer permanece prioritário quando aplicável.
- Opcional sem sinal de índice **não** autoriza probe (RW-S03-01 preservado).

## 4. Compatibilidade MCP / ausência de acoplamento

- Classificação/descrição do provider informam seleção; AuthZ/Policy/Decision permanecem donos.
- Sem hardcode de `get_product_guide`, `topic`, TÉO/DAVI/VISTA.
- Sem novo planner, registry ou workflow por provider.
- PREPARE/ACT inalterados; MESSAGE ≠ ACT.

## 5. Testes

- `tests/test_mcp_iterative_index_probe.py` — Orion unseen MCP (index→guide); contract omit→index mesmo com `probe_index=false`; search required sem probe; descrição sem sinal omit/index + `probe_index=false` não invoca vazio.
- Stage 03 / envelope / TÉO analyze regression preservados.
- Suíte `delia-api` pytest completa verde neste HEAD.

## 6. Live SSH

Registrado no ledger §6.209 (atualização pós contract-gate) após deploy do SHA desta correção em `srv-api` (MESSAGE-only; zero ACT). Resultados LIVE-A/B/C e timeouts constam no ledger, não neste doc.

## 7. Outcome

```text
REUSE_DECISION=EXTEND
NEW_PLANNER=NO NEW_REGISTRY=NO PROVIDER_HARDCODE=NO
STAGE_03_ACCEPTED=NO
C3_EXECUTED=NO
NEXT=INDEPENDENT_ARCHITECTURE_REVIEW
```
