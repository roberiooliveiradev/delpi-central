# I02 — Síntese fundamentada, aproveitamento de conhecimento MCP e orçamento

**DATA:** 2026-10-17
**TASK_ID:** `DELIA-C3-MCP-CONTEXTUAL-KNOWLEDGE-SYNTHESIS-I02-IMPLEMENTATION-01`
**TRACK:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-ORCHESTRATOR-QUALITY-01`
**BASE_HEAD:** `a7869a5d4527d251a3f99ef549aa81979ed6d535`
**CODE_COMMIT:** `55b0e9397100dadea10c0180e922afbc4afcaf1d` (+ nested fix `cc7d2c8e3ba0d70edd56088df72ee795976c2e2e`)
**LIVE_EVALUATED_SHA:** `55b0e9397100dadea10c0180e922afbc4afcaf1d`
**MODEL:** `moonshotai/kimi-k3`
**I02_ACCEPTED:** `NO`

## 1. CP/RQ e reuse

**CP/RQ materiais:** CP-094, CP-055, CP-263/264, CP-270, CP-130/134 (matriz 25). Contrato público inalterado.

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

Estendidos: `_synthesize_content`, `_synthesis_records`, `render_specialist_outcome` (input_text opcional), `_outcome_attempt`, `SYNTHESIS_INSTRUCTION`, helpers `_guidance_section_records` / `_deterministic_guidance_content`. Sem novo planner, memory engine ou registry.

## 2. Diagnóstico de truncamento (PROVEN)

| Estágio | Status |
|---|---|
| OWNER_RESULT_TRUNCATED | TO_INVENTORY (possível contribuição) |
| OWNER_PROJECTION / DETERMINISTIC_RENDER_LIMIT | **PROVEN** — `MAX_RENDER_CONTENT_CHARS=2000` + preferência por `content_text` meta-first quando o JSON estruturado estava embutido no texto |
| SYNTHESIS_SELECTION_SKIPPED / SYNTHESIS_TIMEOUT | **PROVEN** — `skip_budget` quando `remaining < 6s` demovia para dump truncado |
| MODEL_INPUT_TRUNCATED | PROVEN bound `MAX_SURFACE_CHARS=6000` (secundário) |
| CLIENT_PRESENTATION_TRUNCATED | TO_INVENTORY |

**Causa raiz I02:** sob orçamento apertado (ou com payload guidance-shaped), a projeção determinística preservava metadados/autoridade no início e cortava métodos/pré-requisitos/critérios úteis; a seleção pelo modelo frequentemente não era alcançada.

## 3. Solução

1. Projetar seções de orientação (provider-neutral) como registros selecionáveis.
2. Preferir projeção determinística alinhada à intenção **antes** da chamada de síntese ao modelo (economiza orçamento).
3. Em `skip_budget` / `budget_fallback`, tentar a mesma projeção antes do dump genérico.
4. `render_specialist_outcome(..., input_text=)` para demote com alinhamento de objetivo.
5. Suporte a envelope aninhado `guide`/`body` e aliases `use_when`/`how_to_use` (fix pós-live).

Invariantes: `MODEL_AUTHORED_FACTUAL_PROSE=NONE`, `GLOBAL_TURN_BUDGET_SECONDS=30`, `MESSAGE!=ACT`, sem memória global.

## 4. Testes

| Suite | Resultado |
|---|---|
| I02 S1–S5 + rename/non-MCP/security (13) | PASS |
| I01 continuity | PASS |
| render fidelity | PASS |
| `delia-api` full | PASS |

## 5. Live (3 turnos, MESSAGE-only, sem retry de PASS)

```text
K1: FAIL — turn_budget/model_timeout após seleção get_methodology_guide;
    delpi_source_unverified; 30025ms; sem outcome owner (cold path pré-síntese)

K2: PASS_WITH_LIMITATION — get_methodology_guide; synthesis=deterministic_guidance;
    methods/when_to_use/invariants projetados; 20373ms; owner reinvoke=YES
    (K1 sem evidência útil); não é path de continuidade I01 nesta amostra

K3: PASS_WITH_LIMITATION / PARTIAL — get_product_guide bound topic display_formats;
    skip_budget remaining_ms=3097; dump truncado no SHA live (envelope aninhado
    não projetado ainda); fix nested em cc7d2c8e (TEST_NOT_RUN live)
```

```text
UNAUTHORIZED_MATERIAL_ACT_COUNT=0
MAX_OBSERVED_LATENCY_MS=30025
GLOBAL_TURN_BUDGET_SECONDS=30
```

## 6. Residuais

- Latência pré-síntese (goal/selection/discovery/index) ainda consome o teto — K1 timeout.
- Seleção de tópico VISTA (display_formats vs legibilidade de painel) — I03/index.
- Live K3 pós-fix nested = `TEST_NOT_RUN` (limite de 3 turnos da task).
- Headroom estrutural amplo do orquestrador permanece na onda Q.

```text
I02_RECOMMENDATION=ACCEPT_WITH_RESIDUAL
I02_ACCEPTED=NO
I03_IMPLEMENTED=NO
C3_EXECUTED=NO
NEXT=INDEPENDENT_I02_ARCHITECTURE_ACCEPTANCE_REVIEW
```
