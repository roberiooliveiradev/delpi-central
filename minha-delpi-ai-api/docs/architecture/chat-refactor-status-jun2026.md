# Status da refatoração arquitetural — chat API (jun/2026)

**Status:** vigente  
**Última atualização:** jun/2026  
**Público:** backend, revisores, agentes Cursor  

**North star de produto:** [playbook-22](../roadmap/playbook-22-schema-first-api-actions-jun2026.md) + [presentation-delivered-pure-jun2026.md](./presentation-delivered-pure-jun2026.md)  
**Inventário histórico completo:** [playbook-21](../roadmap/playbook-21-desacoplamento-refatoracao-completa-jun2026.md)  
**Pipeline de inteligência:** [chat-intelligence-base.md](./chat-intelligence-base.md)

---

## 1. Prioridade atual (jun/2026)

A onda **W1–W3** de desacoplamento estrutural está **concluída** o suficiente para estabilizar o pipeline. O foco imediato do time **não** é continuar refatoração arquitetural em larga escala.

| Prioridade agora | O que fazer |
|------------------|-------------|
| **Correção de bugs** | Regressões em apresentação, roteamento operacional, duplicação de conteúdo, fixtures quebradas |
| **Qualidade de resposta ao usuário** | Prosa, `dataAnswer`, modos Texto/Painel/Automático, narrativa operacional, coerência factual |
| **Regressão dirigida** | `chat_intelligence_regression_cases.py`, `operational_presentation_quality_cases.py`, `test_presentation_response_quality.py` |

| Adiar (backlog arquitetural) | Ver §4 |
|------------------------------|--------|

> Regra: novos fixes de comportamento transversal → **módulo canônico** + teste (`.cursor/rules/centralized-rules-first.mdc`). Não reabrir god classes nem duplicar `if path` em use cases.

---

## 2. O que foi entregue

### 2.1 W3 — God classes e clean architecture ✅

| Entrega | Detalhe |
|---------|---------|
| Fatiamento de serviços grandes | `ChatIntentRouter*`, `ChatTurnCompletion*`, `ChatDocumentVision*`, `ChatOperationalRefinement*`, `ExternalActionOperationalRouteSelection*`, `ChatProductQueryIntent*`, `ChatOperationalDataCommentary*`, `ChatAdvancedSqlSpecialist*`, `KpiChart*`, `ChatPresentationProfile*`, `ChatPresentationDecision*`, `ExternalActionResultPresenter` |
| Stream | `StreamChatMessageUseCase` ~115L → `ChatStreamTurnExecutionService` |
| Clean architecture | `domainInfrastructureImports` **0**, `domainApplicationImports` **0** (`scripts/audit_clean_architecture.py`) |
| Commit de referência | `eef91c1af` (stream + W3) |

### 2.2 W1 — Commentary registry e síntese declarativa ✅

| Entrega | Detalhe |
|---------|---------|
| `commentaryProfiles` | 10 perfis em `humanized_data_response.json` com `builderStrategy` |
| Registry | `ChatOperationalCommentaryBuilderRegistryService` + orquestração genérica |
| Síntese | `questionSynthesisStrategy` declarativo no JSON |
| Gate | `audit_commentary_profiles_registry` em `audit_presentation_prose_delivery.py` |
| Commit | `1a3cf5c22` |

### 2.3 W2 — Perfil e JSON como fonte única ✅

| Entrega | Detalhe |
|---------|---------|
| `entitySets.textFirstProfiles` | Substitui `_TEXT_FIRST_PROFILES` em Python |
| `entitySets.tierAProfileKeys` | Fonte única para tier A (derivado em `ChatPresentationVocabularyService`) |
| `entitySets.visualHintProfileKeys` | Perfis com `routeNamespace` obrigatório |
| `entityTableProfiles` | Entidade → `tableProfile` declarativo |
| `routeNamespace` | Nos perfis operacionais (`presentation_profiles.json`) |
| `refinementVocabulary.paginatedPathFragments` | No `operational_route_registry.json` |
| Serviço | `ChatPresentationProfileDeclarativeService` |
| Gate | `audit_presentation_profile_declarative_w2` |
| Commit | `1aebbf66a` |

### 2.4 Entregas transversais anteriores (contexto)

| Tema | Artefato |
|------|----------|
| Exclusividade MPs (modelo) | `structure_exclusivity` + `dataAnswerLeadAlignment` + `operational_factual_verdict.json` |
| Delivered pure | `presentationStrategy: as_delivered`, `richStackProfiles: []` |
| Path markers síntese | `factualProfileSynthesisKinds` / `narrativePolicySynthesisKinds` (sem duplicar em narrative_synthesis) |
| Diretrizes Cursor | `chat-intelligence-base.mdc`, `presentation-operational-decoupling.mdc`, `centralized-rules-first.mdc` |

---

## 3. Gates CI que passam hoje (escopo W1–W2)

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/audit_presentation_prose_delivery.py --check
.venv/bin/python scripts/audit_presentation_coverage.py --check-profiles
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_presentation_profile_declarative_w2.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_operational_commentary_registry_w1.py -q
.venv/bin/python scripts/audit_clean_architecture.py --check
```

---

## 4. Backlog arquitetural — implementar depois

Itens **documentados** para uma próxima onda; **não** bloqueiam correções de bug nem melhorias de resposta.

### 4.1 W4 — Path literals residuais (média–baixa)

Migrar `if "/rota"` restantes para registry, `api_route_domains.json` ou perfil. Inventário completo em [playbook-21 §W4](../roadmap/playbook-21-desacoplamento-refatoracao-completa-jun2026.md).

**Application (amostra):** `chat_structure_comparison_service`, `chat_composite_direct_answer_service`, `chat_data_interpretation_answer_service`, `external_action_route_selection_service`, …

**Domain (amostra):** `chat_route_context_service`, `chat_presentation_route_policy_service`, `chat_product_structure_presentation_service`, `chat_operational_llm_synthesis_context_service`, …

**Gate alvo:** `scripts/audit_presentation_path_ifs.py --check` (escopo estreito, 0 condicionais por path).

### 4.2 W2 — itens remanescentes (baixa prioridade)

| # | Item | Estado | Notas |
|---|------|--------|-------|
| 1 | Rich stack flags → `stackPlan` / flags no perfil | Parcial | `richStackProfiles` vazio (delivered pure); reativar só com `presentationStrategy: legacy` |
| 3 | `_KPI_PROFILE_KEYS` em schema-driven | Pendente | Ver `chat_schema_driven_presentation_service.py` |
| 9 | Unificar `operational_route_registry` × `api_route_domains` | Pendente | Domínios internos (`domainLmp`, `productionOperational`) ≠ chaves de `api_route_domains.json`; exige mapeamento explícito, não lint ingênuo |
| — | Veredito Sim/Não único entre bundles JSON | Parcial | Âncora `presenter_content`; refs em `operational_factual_verdict` |
| — | `product_operational_content.json` vs presenter | Pendente | Dedup de scope/framing |

### 4.3 Registry e cobertura OpenAPI

| Débito | Sintoma | Ação futura |
|--------|---------|-------------|
| Rotas PAC quality sem `autoTierCRoutes` | `lint_operational_route_registry.py --check` falha (9 erros) | Gerar entradas: `my-queue`, `export/pdf`, `export/rnc-8d/pdf` |
| `generate_operational_route_registry.py --check` | Drift tier C | Sincronizar após novas rotas api-delpi |
| Baseline refactor Playbook 12 | `test_presentation_refactor_baseline` quebra | Atualizar `playbook12Refactor.auditFiles` (arquivo `chat_presentation_visual_bundle_service.py` removido) |

### 4.4 Qualidade de apresentação (overlap bug × arquitetura)

Regressões conhecidas — **prioridade para correção de produto**, não para nova refatoração:

| Teste / caso | Sintoma | Módulo canônico alvo |
|--------------|---------|----------------------|
| `test_presentation_response_quality.py` | `textPresentation.markdown` vazio em delivered pure; narrativa em `dataCommentary` | `ChatPresentationProseDeliveryService`, pipeline metadata |
| `operational_presentation_quality_cases.py` | Casos tier A / exclusividade / stock text-first | Fixtures + `ChatPresentationMetadataPipelineService` |
| Modos Texto/Painel/Automático | Fallback MFE ou `explicitSessionFormat` ambíguo | `ChatPresentationTextModeService`, contrato metadata |

### 4.5 Vocabulário e conteúdo JSON

Ver também [vocabulary-centralization-jun2026.md § Pendências](./vocabulary-centralization-jun2026.md):

- Filtro família/prefixo SQL (`LIKE '9026%'`)
- Regex temporais → JSON
- Narrativa/insights em rotas SQL/operacionais adicionais
- Sync MFE `plugins/minha-delpi-chat/src/content/` para textos compartilhados

---

## 5. Como trabalhar agora (bugs e respostas)

### 5.1 Fluxo recomendado

```
1. Reproduzir com fixture ou mensagem de regressão
2. Localizar módulo canônico (tabela centralized-rules-first.mdc)
3. Corrigir no serviço base — não no agente nem só no MFE
4. Texto novo → assistant/*.json + loader
5. Teste que falha sem a regra (fixture ou test_presentation_response_quality)
```

### 5.2 Testes prioritários antes de merge (qualidade UX)

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/application/use_cases/test_presentation_response_quality.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_presentation_decoupling.py -q
.venv/bin/python -m pytest tests/fixtures/chat_intelligence_regression_cases.py -q  # quando aplicável
```

### 5.3 O que evitar nesta fase

- Nova god class ou presenter por entidade para regra transversal
- `if path` novo em use case (`Send*` / `Stream*`)
- Patch só no MFE para comportamento que nasce na API
- Reintroduzir `richStackProfiles` / table assembly sem playbook-22 explícito

---

## 6. Mapa de commits de referência

| Commit | Conteúdo |
|--------|----------|
| `eef91c1af` | W3 stream + clean architecture |
| `1a3cf5c22` | W1 commentary registry |
| `1aebbf66a` | W2 perfis declarativos |
| `d11d1d3c8` | PAC Onda 1 (fora do escopo chat base) |

---

## Changelog deste documento

| Data | Nota |
|------|------|
| jun/2026 | Criado após conclusão W1–W3; pausa arquitetural; foco bugs + qualidade de resposta |
