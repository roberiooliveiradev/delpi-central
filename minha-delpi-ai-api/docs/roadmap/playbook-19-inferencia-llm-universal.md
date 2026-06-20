# Playbook 19 — Inferência LLM universal (100% prosa)

**Projeto:** Minha DELPI Chat IA  
**Status:** P5.6 parcial — smokes matriz + fixtures pipeline (jun/2026)  
**Pré-requisito:** [Playbook 18 — desacoplamento template×LLM](./playbook-18-prosa-template-llm-desacoplamento.md) (P0–P4.4 ✅)

---

## 1. Objetivo

Substituir **toda** prosa template/direct por **inferência LLM** ancorada em fatos estruturados (`dataAnswer`, tabelas, KPI, SQL, erros), mantendo visuais nativos no MFE (render-only).

| Antes (P18) | Depois (P19) |
|-------------|--------------|
| Template em listagem/KPI/playbook | LLM interpreta; tabela/KPI = evidência |
| `operational_direct` factual | LLM mesmo em consulta estreita |
| `humanizedSummary.linhas` na UI | Arquivo legado / fatos LLM apenas |
| Síntese só em rotas narrativas | Síntese em **qualquer** tool operacional ok/falha |

**Trade-offs aceitos:** maior latência e custo por turno; ganho em assertividade consultiva uniforme.

---

## 2. Arquitetura alvo

```mermaid
flowchart TD
  A[ExecuteExternalAction ok|fail] --> B[Pipeline data-only]
  B --> C[Presenter: título + visuais — sem linhas prosa]
  C --> D[ChatPresentationProseDeliveryService]
  D --> E{llmProseEverywhere}
  E -->|sim| F[mode=llm + decouple]
  F --> G[ChatOperationalNarrativeSynthesisService]
  G --> H{kind}
  H -->|overview| I[product-overview-*.md]
  H -->|evidence| J[operational-synthesis-*.md]
  H -->|playbook/kpi| K[operational_data]
  H -->|sql| L[sql_result]
  H -->|erro| M[error_recovery]
  K --> J
  L --> J
  M --> J
  J --> N[ChatOperationalLlmSynthesisContextService]
  N --> O[LLM Rápida/Normal/Pensador]
  O --> P[MFE: lead=assistantMessage + visuais]
```

### Gate canônico (estendido P18)

| Flag JSON | Efeito |
|-----------|--------|
| `settings.llmProseEverywhere` | Todo `execute_external_action` ok → `proseDeliveryMode=llm` |
| `settings.deprecateHumanizedLinhasAsProse` | Pipeline não persiste `linhas` como prosa UI |
| `proseDeliveryByTier` A/B/C = `llm` | Perfis KPI/listagem/playbook |
| `proseDeliveryByEntitySet.*` = `llm` | Playbook TOP N, listagens produto |

Bundles: `presentation_prose_delivery.json`, `operational_narrative_synthesis.json`, `operational_llm_synthesis_context.json`, `response_mode_synthesis_quality.json`.

---

## 3. Matriz de rotas (escopo 100%)

| Domínio | Entity / perfil | Kind síntese | Fatos LLM | Visual MFE |
|---------|-----------------|--------------|-----------|------------|
| Produto narrativo | factory_status, stock, … | `summary_then_evidence` | dataAnswer + archive | stack |
| Overview | product_* multi-rota | `product_overview` | multi-tool facts | multiRoute |
| Playbook TOP N | `production_*`, playbookOperational | `operational_data` | tabela + paginação + summary | table |
| KPI escalar/série | kpi_series, kpi_dashboard | `operational_data` | kpiPresentation + dataAnswer | kpi/chart |
| SQL | `/data/sql` | `sql_result` | sqlRows + erro SQL | table |
| Erro API/SQL | tool `ok=false` | `error_recovery` | status, message, preview | banner |
| Direct answer legado | — | — (removido) | — | — |

---

## 4. Roadmap

### P5 — Inferência default global ✅ parcial

| # | Entrega | Status |
|---|---------|--------|
| P5.1 | `llmProseEverywhere: true` + tiers/entitySets/profiles → `llm` | ✅ |
| P5.2 | `resolve_mode` / `operational_direct` desligado quando everywhere | ✅ |
| P5.3 | Pipeline data-only para **qualquer** path com everywhere | ✅ |
| P5.4 | Kinds `operational_data`, `sql_result`, `error_recovery` + policies | ✅ P5.1 |
| P5.5 | Fatos LLM: SQL rows, KPI, paginação playbook, erro tool | ✅ P5.1 |
| P5.6 | Smoke matriz: factory_status, top-items, KPI, SQL, erro | ✅ script + fixtures unit |

### P6 — Deprecar `humanizedSummary.linhas` como prosa

| # | Entrega | Status |
|---|---------|--------|
| P6.1 | `deprecateHumanizedLinhasAsProse` no JSON + pipeline | ✅ P5.1 |
| P6.2 | Presenters upstream: só título; linhas → archive automático | ✅ parcial (SQL sqlRows + title-only) |
| P6.3 | Audit: flag `linhas` em presenter como legado upstream | ✅ |
| P6.4 | Remover `operational_direct` e authorized template persist | ✅ |
| P6.5 | MFE: zero fallback markdown template | ✅ |

### P7 — Qualidade assertiva por modo

| # | Entrega | Status |
|---|---------|--------|
| P7.1 | Limites por modo em `response_mode_synthesis_quality.json` | ✅ existente |
| P7.2 | Smoke ladder Rápida/Normal/Pensador (distância + latência) | ✅ parcial (SMOKE_STRICT + teste estrutural) |
| P7.3 | Gates CI: min chars, max templateSimilarity, anti-deflection | ✅ parcial |
| P7.4 | Ajuste prompts `operational-synthesis-*.md` por domínio (SQL/playbook) | 🔲 |

### P8 — Remoção de legado template

| # | Entrega | Status |
|---|---------|--------|
| P8.1 | Modo `template` só em fallback offline (modos OFF + flag) | 🔲 |
| P8.2 | Remover geração de `textPresentation.markdown` no formatter | 🔲 |
| P8.3 | Documentar contrato metadata v2 (sem linhas prosa) | 🔲 |

---

## 5. Contrato metadata (P19)

| Campo | Semântica |
|-------|-----------|
| `proseDeliveryMode` | Sempre `llm` em turnos operacionais (P5+) |
| `llmProseDecoupled` | true |
| `dataOnlyPresentation` | true — pipeline não emitiu prosa template |
| `templateProseArchive` | Fatos históricos; **nunca** renderizar |
| `humanizedSummary.linhas` | `[]` na UI; fatos via archive |
| `responseModeEffect` | `llm_synthesis` \| `llm_synthesis_brief` — nunca `operational_direct` |

---

## 6. Gates CI / smoke

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/audit_presentation_prose_delivery.py --check
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_presentation_prose_delivery_service.py \
  tests/unit/domain/services/test_chat_operational_llm_synthesis_context_service.py \
  tests/unit/domain/services/test_chat_operational_narrative_synthesis_service.py \
  tests/unit/domain/services/test_chat_response_mode_synthesis_quality_service.py -q

# Smoke por domínio (live)
SMOKE_SCENARIO=factory_status .venv/bin/python scripts/smoke_llm_universal_prose.py
SMOKE_SCENARIO=playbook_top_items .venv/bin/python scripts/smoke_llm_universal_prose.py
SMOKE_SCENARIO=kpi_cpv .venv/bin/python scripts/smoke_llm_universal_prose.py
SMOKE_SCENARIO=sql .venv/bin/python scripts/smoke_llm_universal_prose.py
SMOKE_SCENARIO=api_error .venv/bin/python scripts/smoke_llm_universal_prose.py
SMOKE_SCENARIO=all .venv/bin/python scripts/smoke_llm_universal_prose.py
# Qualidade LLM (latência/chars/ladder) — opcional:
SMOKE_STRICT=1 SMOKE_SCENARIO=factory_status .venv/bin/python scripts/smoke_llm_universal_prose.py
```

### Critérios smoke (todos os modos)

- `llmProseDecoupled: true`, `dataOnlyPresentation: true`, `templateSimilarity < 0.72`
- Sem marcadores de deflexão (`preciso acessar`, …)
- Ladder: Rápida ≤ Normal em chars; distância pairwise ≥ 0.06
- Latência: Rápida ≤ 1.25× Normal (tolerância configurável)

---

## 7. O que NÃO fazer

- Reintroduzir prosa template no presenter **e** LLM no mesmo turno.
- Ler `humanizedSummary.linhas` em consumidores pós-gate (usar helpers P18).
- `operational_direct` quando `llmProseEverywhere` ativo.
- Texto PT / limites / markers em Python — só JSON + loaders.

---

## 8. Referências

- [Playbook 18](./playbook-18-prosa-template-llm-desacoplamento.md)
- [chat-response-modes.md](../architecture/chat-response-modes.md)
- Changelog: [`2026-06-playbook-18-prosa-template-llm.md`](../changelog/2026-06-playbook-18-prosa-template-llm.md)
- Regras: `presentation-operational-decoupling.mdc`, `centralized-rules-first.mdc`
