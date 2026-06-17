# Checklist — nova rota api-delpi exposta ao chat

> **Público:** backend api-delpi + minha-delpi-ai-api  
> **Cursor:** espelhado em `.cursor/rules/new-api-route-checklist.mdc` e índice `development-standards-index.mdc`  
> **Princípio:** rota nova = contrato HTTP + roteamento no chat + perfil de apresentação + gates CI — não só endpoint.

---

## Visão geral

```text
api-delpi (HTTP + meta)
    ↓
operational_route_registry + ExternalActionRouteSelectionService
    ↓
ExecuteExternalActionUseCase → ChatPresentationMetadataPipelineService.build
    ↓
ExternalActionResultPresenter + ChatPresentationDecisionService
    ↓
metadata.presentationDecision → MFE (render-only)
```

Referências cruzadas:

| Documento | Escopo |
|-----------|--------|
| [playbook-10-contrato-respostas-api-delpi.md](../roadmap/playbook-10-contrato-respostas-api-delpi.md) | Envelope, `meta.entity`, `meta.shape` |
| [playbook-15-rotas-operacionais-sem-sql.md](../roadmap/playbook-15-rotas-operacionais-sem-sql.md) | Rotas operacionais PB15 |
| [chat-intelligence-base.md](./chat-intelligence-base.md) | Pipeline e Playbook 09 |
| [assistant-content-catalog.md](./assistant-content-catalog.md) | Bundles JSON |
| [api-delpi/docs/api/](../api/) | Endpoints HTTP |

---

## 1. api-delpi

| # | Entrega | Arquivo / camada |
|---|---------|------------------|
| 1 | Resposta de sucesso | `api_delpi_success(data, operation_id=...)` em `route_response_helpers.py` |
| 2 | Contrato semântico | `route_contract_registry.py` — `entity` + `shape` |
| 3 | OpenAPI alinhado | `operation_id` idêntico no decorator e no registry |
| 4 | Chat-critical | `openapi_agent_metadata.agent_route()` |
| 5 | RBAC | `api_delpi_permissions.py` — sem strings literais no router |
| 6 | Teste | Smoke em `api-delpi/tests/` — `meta.operationId`, `meta.entity` |

**Shapes comuns:** `playbook_report`, `paged_list`, `scalar`, `composite_analysis`, `hierarchy` (playbook-10 § 4.3).

---

## 2. Chat — roteamento e seleção

| # | Entrega | Onde |
|---|---------|------|
| 1 | Catálogo operacional | `operational_route_registry.json` |
| 2 | Sincronização | `scripts/generate_operational_route_registry.py --check` |
| 3 | Domínio novo | `api_route_domains.json` (`pathMarkers`, `parameterStrategies`) |
| 4 | Seleção | `ExternalActionRouteSelectionService` (application) |
| 5 | Execução HTTP | `ExecuteExternalActionUseCase` + gateway |
| 6 | Regressão de intenção | `chat_intelligence_regression_cases.py` ou `production_operational_regression_cases.py` |

**Proibido:** `if "/products/"` ou `if kpi` em use case ou MFE para escolher action.

---

## 3. Chat — apresentação declarativa

### 3.1 Escolher perfil pela semântica dos dados

| Semântica | Perfil JSON | Políticas típicas |
|-----------|-------------|-------------------|
| Listagem auditável (`items[]`, várias colunas descritivas) | `playbook_report`, `table_list` | `defaultViewPolicy: table_when_available`, `chartPolicy: skip` |
| KPI / série temporal | `kpi_series`, `kpi_dashboard` | `kpi_when_available`, `chartPolicy: auto` |
| Hierarquia (BOM, pais) | `tree_hierarchy` | `tree_when_available` |
| Produto composto | `stock`, `analyser`, … | Ver `presentation_profiles.json` |

### 3.2 Arquivos JSON (obrigatório)

| Arquivo | O que registrar |
|---------|-----------------|
| `presentation_profiles.json` | `entityProfiles`, `entitySetProfileContracts`, `pathRules` (**específica antes de catch-alls**), `noChartEntities`, `entityPathHints`, `pathEntityFallbacks` |
| `presenter_content.json` | Títulos por fragmento de path / entidade |
| `column_labels.json` | Rótulos de colunas e perfis tabulares |
| `presentation_vocabulary.json` | Marcadores de score Automático (`automaticScoreMarkers`) se nova heurística de mensagem |

### 3.3 Pipeline canônico (código)

Ordem de execução após `ExecuteExternalAction`:

1. `ChatPresentationMetadataPipelineService.build` (application)
2. `ExternalActionResultPresenter` + perfil (`ChatPresentationProfileService`)
3. `ChatPresentationDataShapeAnalyzer.analyze` → `viewIntent` (`auditable_list`, `ranking`, `temporal_series`, …)
4. `ChatPresentationDecisionService.enrich_metadata` → `presentationDecision`
5. `ChatPresentationViewIntentService` — modo **Automático**: tabela vs gráfico (shape + perfil + mensagem)
6. MFE consome metadata — **não** redecide formato (`chatPresentation.ts`)

Serviços auxiliares: `ChatPresentationOperationalDecisionService`, `ChatPresentationProfileVisualBundleService`, `ChatPresentationFieldNormalizationService`.

Detalhe do contrato metadata: [chat-assistant-content-presentation.md](./chat-assistant-content-presentation.md).

### 3.4 Contratos entitySet × perfil

`entitySetProfileContracts` em `presentation_profiles.json` define famílias de entidades (ex.: `playbookOperational` → `playbook_report`) e perfis **proibidos** (ex.: `kpi_series` em listagem).

Validação: `ChatPresentationCoverageService.find_entity_set_profile_gaps()`.

---

## 4. Gates CI

```bash
cd minha-delpi-ai-api

# Perfis + contratos entitySet
.venv/bin/python scripts/audit_presentation_coverage.py --check-profiles

# Registry operacional
.venv/bin/python scripts/generate_operational_route_registry.py --check

# DOCIE (registry + path ifs)
.venv/bin/python scripts/lint_operational_route_registry.py --check
.venv/bin/python scripts/audit_presentation_path_ifs.py --check

# Regressão apresentação Automático
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_presentation_view_intent_service.py -q
```

`--check-profiles` falha quando:

- rota tier A resolve perfil `generic`;
- entidade quebra contrato `entitySetProfileContracts`;
- path sem `meta.entity` cai em perfil proibido (quando `validatePathWithoutEntity: true`).

Homologação manual: [presentation-homologation-jun2026.md](../testing/presentation-homologation-jun2026.md).

---

## 5. Teste mínimo de apresentação

Fixture ou teste unitário com payload representativo e **sem** preferência explícita do usuário:

| Cenário | `presentationDecision.selected` esperado |
|---------|------------------------------------------|
| Listagem (OPs, NF, movimentos) | `table` (ou `text` se perfil narrativa-first) |
| KPI / série | `kpi`, `line_chart` ou tipo chart adequado |
| Ranking agregado (filial × métrica) | chart pode vencer — `viewIntent: ranking` |

Exemplo: `tests/unit/domain/services/test_chat_presentation_view_intent_service.py`.

---

## Anti-padrões

| Erro | Consequência |
|------|--------------|
| Endpoint sem `entityProfiles` | Catch-all de path (ex.: `/production/` → `kpi_series`) em listagem |
| Gráfico default no MFE ou prompt de agente | Divergência send/stream; regressão Automático |
| Texto PT hardcoded em Python | Viola ADR 003 e gate de strings |
| Serviço de decisão não ligado ao pipeline | Implementação «morta» — ver guardrails clean architecture |
| `pathRules` genérica antes da específica | Perfil errado quando `meta.entity` ausente |

---

## Checklist rápido (PR)

- [ ] api-delpi: `api_delpi_success` + registry + teste meta
- [ ] `operational_route_registry.json` + `--check`
- [ ] `entityProfiles` + contrato entitySet (se aplicável)
- [ ] `pathRules` específica antes de catch-all do domínio
- [ ] Títulos/colunas em JSON
- [ ] Regressão intenção + apresentação Automático
- [ ] `--check-profiles` verde
- [ ] Send e stream usam o mesmo pipeline de metadata
