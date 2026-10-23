# 113 — S0 freeze: contratos e responsabilidades (self-awareness)

`DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01` / `STEP=S0` · 2026-10-23 · executor: Devin · `BASE_HEAD=417f44fcd3` · READ_ONLY, zero diff de runtime.
Autorização: doc 112 §7 (`PO_DECISION=S0_AUTHORIZED_READ_ONLY`, commit `417f44fcd3`). Fontes reutilizadas: auditorias 56–57, ADR 58, roadmap 59 (Q03 encerrado `ACCEPT_WITH_RESIDUAL`, B1 formalmente diferido — não reaberto), relatórios 108–111, ledger até §6.393. Nenhum inventário geral novo foi executado — apenas o mapa por-função dos grupos afetados exigido pelo plano.

## 1. Estado verificado no HEAD

| item | evidência |
|---|---|
| `orchestration.py` | 11.819 linhas, 194 declarações (auditorias cobriam 10.592/179 em `8fc45e21`) — delta de +1.227 linhas explicado por Q02-A/B/C + CRI E1–E3 + budgets 60/3/300 + RC1/RC2 |
| Consumidor produtivo | único import: `app/composition/root_composer.py` → `OperationalCapabilityOrchestrator` → `HandleInteractiveConversationTurn(capability_orchestration=…)` via protocol `SupportsGovernedCapabilityAttempt` (`capability_attempt.py`). `capability_attempt.py` cita o módulo em comentário, sem import |
| Cadeia | `attempt` → `_admit_conversational_turn` → `_groups` (surface viva) → `_select_target` (`_select_group` + `_select_capability[_with_goal]`, proposta tipada + revalidação determinística) → `_build_plan`/`_invoke_selected` → `_invoke` → `_maybe_aggregate_paginated_count` → `_outcome_facts` → `assess_outcome` → `_compose_cri_response` (CRI) **ou** `_synthesize_content` → `_apply_outcome_assessment` → `_outcome_attempt` (`render_specialist_outcome_rich`) |
| Baseline | `test_c3_contextual_discovery.py` = 30/30 GREEN no HEAD (caracterização read-only executada) |
| Congelamentos | `selection-only` (§6.145), `MODEL_AUTHORED_FACTUAL_PROSE=NONE`, 60/3/300, cap conversacional 12s pós-orquestração, PREPARE/ACT, Core/Domain AuthZ, `READ != ACT` — preservados; B1 (`classify_result_intent`/`unique_structural_ticket_list_capability`) = `ARCHITECTURE_DECISION_REQUIRED` formalmente diferido |

## 2. Matriz de responsabilidade — grupos afetados

Formato: `RESPONSIBILITY → OWNER → SOURCE → CONSUMERS → CONTRACT → CURRENT_PATH → KEEP|MOVE|EXTEND`. Somente grupos afetados por S1–S4; as 194 funções fora destes grupos permanecem `CONTRACT_INVENTORY` da auditoria 57 sem reclassificação.

### G-SA1 — Seleção semântica admission/group/capability (rotas D4/D5/D8)

| Função (linha) | Contrato | KEEP/MOVE/EXTEND |
|---|---|---|
| `_admit_conversational_turn` (10573) | proposta tipada `requires_owner_surface` + `interaction_class` ∈ {conversation, explanation, hypothetical, operational, ambiguous} | **KEEP**; EXTEND somente via classe tipada nova na proposta existente (S1), nunca keyword |
| `_select_group` (10670) · `_resolve_live_group_key` (4052) · `_group_summaries` (4076) | proposta `applicable`/`capability_group_id` + membership live | **KEEP** |
| `_select_capability` (10784) · `_select_capability_with_goal` (10847) · `_capability_from_selection_proposal` (10736) · `_capability_payload` (4149) | proposta `applicable`/`remote_name` (+goal tipado I02-R3B); instruções já tratam *coverage inquiry* → DISCOVERY | **KEEP** |
| `_select_target` (9413) · `_find_capability` (1447) · `_groups` (9347) · `_fresh_group` (9384) · `_project_surface` (4031) | hierarquia group→capability com revalidação live; `ProviderSurface.failures` = indisponibilidade verdadeira | **KEEP** |
| `_propose` (9882) · `_model_stage_proposal` (9613) | única via de chamada de modelo (InvokeModel), budget/stage/lineage | **KEEP** (consolidação Q02-A já aplicada) |

- OWNER: `capability_provision/orchestration.py` (boundary semântico LLM↔determinístico, ADR 58). SOURCE: `ProviderSurface`/`CapabilityGroup` vivos via `CapabilityProviderPort`. CONSUMERS: `attempt` (main path). `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` para o subescopo D4 (nova classe/goal tipado dentro da proposta existente — contrato novo de proposta, não de transporte).

### G-SA2 — Projeção da superfície viva ao usuário (conteúdo D4)

| Função (linha) | Contrato | KEEP/MOVE/EXTEND |
|---|---|---|
| `_discovery_capability` (1293) · `_owner_eligible_action_count` (1307) · `_discovery_empty_result_class` (1327) | classificação de envelope discovery (NOT_MATCHED/UNAVAILABLE/NOT_ENUMERABLE) | **KEEP** |
| `_live_interop_surface_lines` (1343) | linhas bounded de tools DISCOVERY/READ/ANALYSIS de **um** grupo, com redaction | **KEEP** — precedente canônico de projeção surface→usuário |
| `_render_zero_candidate_discovery` (1374) | terminal honesto zero-candidatos, um grupo | **KEEP**; EXTEND (S1) para projeção cross-grupo se gate aprovar |

- CONSUMERS: `_invoke` (11358, único call-site de `_render_zero_candidate_discovery`; `_live_interop_surface_lines` só por ele). `EXISTING_EQUIVALENT=YES` (padrão de projeção de superfície já existe); `REUSE_DECISION=EXTEND`.

### G-SA3 — Fronteira de projeção de evidência (RC1/RC2 — congelar)

| Função (linha) | Contrato | KEEP/MOVE/EXTEND |
|---|---|---|
| `_is_capability_descriptor` (1758) · `_without_control_plane` (1776) · `_contract_fact_rows` (1795) · `_compact_evidence` (1935) · `_evidence_rows` (1974) · `_unwrap_owner_payload` (2962) · `_resolver_entities` (2977) · `_synthesis_records` (3486) · `_explicit_empty_business_collection` (3442) · `_bound_owner_evidence` (1655) · conjuntos `_CONTROL_PLANE_KEYS`/`_CAPABILITY_VOCABULARY_KEYS`/`_DISCOVERY_ENVELOPE_KEYS`/`_ENVELOPE_SCALAR_KEYS`/`_canonical_key` (4231) | projeção typed: business evidence ≠ controle ≠ catálogo ≠ transporte; `contract_facts` só DISCOVERY | **KEEP** — remediado (docs 110/111); EXTEND (S2) somente para classificação evidência×vocabulário-técnico dentro do mesmo boundary |

- CONSUMERS: `_outcome_facts` (8937), `_synthesize_content` (10167), `_render_synthesis` (2408). `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`.

### G-SA4 — Outcome assessment E2 (veredito de suficiência)

| Módulo/função | Contrato | KEEP/MOVE/EXTEND |
|---|---|---|
| `outcome_assessment.py` — `assess_outcome`, `EvidenceFacts`, `parse_answer_requirements`, `verified_ordering_event`, `ordering_proof_fields`, `distinct_delivered_count` | leaf: typed facts → `answered/empty_result/envelope_only/insufficient/contract_facts` + reasons | **KEEP**; EXTEND (S2) somente reasons/vocabulário de insuficiência se necessário |
| `_outcome_facts` (8937) · `_apply_outcome_assessment` (8890) | extração de facts + marcação de limitação no outcome | **KEEP** |

- CONSUMERS: main path (6772–6807). `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`.

### G-SA5 — Projeção de guidance do owner (conteúdo D5)

| Função (linha) | Contrato | KEEP/MOVE/EXTEND |
|---|---|---|
| `_GUIDANCE_SECTION_FAMILIES` (3030) + `_GUIDANCE_NESTED_KEYS`/`_GUIDANCE_META_KEYS`/`_GUIDANCE_FAMILY_ORDER` | vocabulário de seções do owner (prereq/steps/objective/when/criteria/limitations; `displayformats`/`formatos`/`visualization`/`legibility`/`blocktypes` ∈ criteria) | **F27/D7 — MOVE_CANDIDATE**, decisão em S4 |
| `_guidance_family_for_key` (3179) · `_render_guidance_value` (3193) · `_guidance_section_records` (3275) · `_pack_guidance_sections` (3335) · `_omitted_sections_line` (3312) · `_iter_guidance_doc_items` (3235) · `_guidance_hit_count` (3227) · `_mapping_items_excluding_control` (3217) | projeção determinística de seções guidance; copia texto do owner, nunca inventa | idem |
| `_deterministic_guidance_content` (3390) · `_md_guidance_content` (4634) · `_select_guidance_records` (4613) | composição guidance p/ texto/markdown | idem |

- CONSUMERS: `render_specialist_outcome_rich` (4739/4750/4793/4804), `_synthesize_content` (10220/10269/10326), `_synthesis_records` (3501). Destino de eventual extração: módulo leaf existente **não identificado** — `conversational_response.py` é compositor E3 render-only (escopo diverso); `paginated_result_semantics.py` é semântica de paginação. Sem destino legítimo existente, `SKIP_WITH_DECISION` é o veredito correto em S4 (criar módulo novo exigiria Abstraction Gate + doc 52 subárea PLANNED). `EXISTING_EQUIVALENT=PARTIAL`; `REUSE_DECISION=PENDING_S4`.

### G-SA6 — Apresentação/rótulos (D8 PT-BR, D5 texto)

| Função (linha) | Contrato | KEEP/MOVE/EXTEND |
|---|---|---|
| `render_specialist_outcome`/`_rich` (4684/4698) | render terminal baseline + markdown | **KEEP** |
| `_sanitize_renderable` (4302) · `_redact_text` (4291) · `_is_sensitive_key`/`_SENSITIVE_KEY_NAMES` (4235/4205) | redaction gate — **PRESERVE**, nunca MOVE | **KEEP** |
| `_FIELD_CLAUSE_LABELS` (2653) + uso em `_proven_field_differences` (2487), `_cri_presented_record` (9026) | mapa in-code de ~16 rótulos PT-BR; fallback `key.replace("_"," ").capitalize()` = texto técnico cru | **KEEP + EXTEND (S3)** — gap `LABEL_VOCABULARY_GAP` tipado |
| `_format_structured`/`_format_list`/`_format_records`/`_business_lines` (4347–4495) · `_md_*` (4497–4612) · `_detail_header`/`_detail_lines`/`_list_header` (2803–2854) | projeção key:value do payload sanitizado — chaves owner cruas | **KEEP**; EXTEND (S3) mesma decisão de rótulos |
| `_cri_presented_record` (9026) · `_cri_scalar_text` (9001) · `_compose_cri_response` (9109) + `conversational_response.py::compose_cri_response` | E3 composer: `PresentedRecord` com `(label, value)` | **KEEP** |
| `_compose_answer` (2757) · `_render_synthesis` (2408) · `_synthesis_selections` (2346) · `_selected_proven_differences` (2511) | seleção-only synthesis; comparação tipada (B2 fechado) | **KEEP** |
| `_clarification_content` (2319) · `_candidate_clarification_content` (3643) · `_insufficiency_content` (2537) | terminais honestos | **KEEP** |
| `config/cri_presentation.delpi.json` | recurso governado (owner DELPI, version 3): leads/temporal/insufficiency/labels — **sem** seção `field_labels` | **KEEP**; EXTEND = candidato de destino canônico p/ rótulos de campo (S3, via `cri_instruction_resource.py`) |

- CONSUMERS: `_outcome_attempt` (9210), `_execute_prepared_act`/`_attempt_confirmation`/`_confirm_proposal` (7999/8245/8835), `_invoke` (9291), `_synthesize_content` (6785+). `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`.

### G-SA7 — Síntese model-driven (congelada)

| `_synthesize_content` (10167) · `_repair_once` (10383) · `_recover_owner_contract` (10459) | seleção-only; prosa factual do modelo proibida | **KEEP** — FROZEN (D6 ADR 58) |

### G-SA8 — Paginação/escopo pessoal (R4/R5)

| `paginated_result_semantics.py` (801 linhas) · `_project_paginated_personal_or_count` (2877) · `_maybe_aggregate_paginated_count` (10036) | envelope paginação + semântica count/list/pessoal | **KEEP** — B1 formalmente diferido; `classify_result_intent`/`unique_structural_ticket_list_capability` = `ARCHITECTURE_DECISION_REQUIRED`, não tocar em S1–S4 sem decisão |

### G-SA9 — Cadeia governada (fora de escopo, registrada)

| `_attempt_prepare`/`_attempt_direct_act`/`_attempt_confirmation`/`_confirm_proposal`/`_execute_prepared_act`/`_invoke_act`/`_provenance`/`_audit`/`_select_prepare_continuation` | PREPARE/ACT, confirmação, idempotência, audit | **PRESERVE** (ADR D8) — nenhuma alteração em S1–S4 |

### G-SA10 — Contratos/catálogo/workspace

| Módulo | Contrato | KEEP |
|---|---|---|
| `contracts.py` — `ProviderCapability`/`CapabilityGroup`/`ProviderSurface` | superfície viva; `grants_* = False`; display_name/owner_ref legit | **KEEP** — fonte elegível de D4 |
| `capability_catalog/model.py` — `CapabilityProjection`/`OperationCharacter` | projeção C3-T5 OpenAPI→semântica | **KEEP** |
| `capability_catalog_adapter.py` — `project_openapi_document` | projeção determinística OpenAPI, rejeição tipada | **KEEP** |
| `workspace_context.py` — `WorkspaceContext`/`parse_workspace_context` | hints client-supplied não confiáveis | **KEEP** — não é fonte de identidade nem de especialistas |

## 3. Contratos legítimos para D4/D5/D8 e gaps tipados

### D4 — "Quais especialistas estão disponíveis?"

- **Fonte legítima existente:** `ProviderSurface.groups` (live `tools/list` por provider): `CapabilityGroup{display_name, owner_ref, capabilities[].remote_name/description/operation_class, source}` + `failures[]` (indisponibilidade verdadeira). Doc 17: DÉLIA consome superfície viva — não é owner de registry; aprovação do provider (approved|enabled|disabled) é Core (projeção futura — `TO_INVENTORY`). `_live_interop_surface_lines` prova precedente: nomes/descrições owner-declared podem ser projetados ao usuário com redaction.
- **GAP tipado = `PROJECTION_PATH_GAP` (não falta dado do owner):** pergunta meta sobre o *conjunto* de especialistas não tem classe tipada em admission (`interaction_class`) nem em goal (`goal_class`); a instrução de coverage-inquiry roteia para DISCOVERY do grupo — que responde "o que esta fonte cobre", não "quais especialistas". Nenhuma projeção cross-grupo user-facing existe. **Não é** `ARCHITECTURE_DECISION_REQUIRED`: o contrato elegível existe; falta apenas uma via de projeção dentro dos owners existentes (S1).
- **Aceite legítimo:** enumeração da superfície elegível viva (nomes declarados + escopo), distinção publicado/disponível/permitido (RQ-SA03: permitido = AuthZ em invoke, declarado honestamente), `failures` declarados; nunca catálogo de *operations* internas nem `agent_directives`.

### D5 — "Quais formatos de dados/visualizações nos painéis?"

- **Fonte legítima existente:** capacidades READ do owner VISTA verificadas na superfície viva (probe dev doc 109/110): `get_product_guide`, `inspect_data_model`, `search_data_routes`, `preview_data_model`, `suggest_change` — `get_catalog` (DISCOVERY) devolve catálogo de mutações/descritores (control-plane). `_GUIDANCE_SECTION_FAMILIES` já cobre `displayformats`/`formatos`/`visualization`/`blocktypes`/`choicecriteria` na família `criteria` — a via de projeção existe.
- **GAP tipado = `SELECTION_EVIDENCE_CLASSIFICATION`:** o modelo selecionou `get_catalog` (vocabulário técnico do produto) e a projeção tratou descritores como evidência (RC2 remediado) — resta garantir que perguntas de vocabulário/produto alcancem a capability legítima **e** que conteúdo técnico (schema `entities.playlist`, allowedOps) nunca vire resposta mesmo quando legítimo de ser retornado pela capability escolhida. Conteúdo do guide (`get_product_guide` realmente publica formatos?) = `TO_INVENTORY` em S2; se o owner não publicar → insuficiência específica com fonte nomeada (RQ-SA04 aceita).
- **Aceite legítimo:** formatos declarados pelo owner renderizados via projeção guidance **ou** insuficiência específica — nunca dump de catálogo/schema.

### D8 — "Descrição do material 10080043" (regressão PT-BR)

- **Fonte legítima existente:** evidência de negócio do owner (DAVI `execute_delpi_information`), projeção `_synthesis_records` → CRI `_cri_presented_record`/labels.
- **GAP tipado = `LABEL_VOCABULARY_GAP`:** `_FIELD_CLAUSE_LABELS` cobre ~16 campos; qualquer chave owner fora do mapa renderiza `key.replace("_"," ").capitalize()` (ex.: `Unit` → rótulo técnico) no CRI, e `_format_structured` renderiza a chave crua no baseline — ambos produzem rótulos em inglês/técnicos. Recurso governado `cri_presentation.delpi.json` não tem seção `field_labels`.
- **Aceite legítimo:** rótulos naturais PT-BR quando declarados; fallback humanizado honesto sem expor chave técnica; dados/IDs/unidades verbatim. Destino preferido: extensão do recurso governado (contrato evoluído, version bump + validação em `cri_instruction_resource.py`) — decisão final em S3.

## 4. Golden D4/D5/D8 (baseline de aceite local; modelo Kimi prod pode divergir de Ollama)

| Caso | Entrada | Outcome mínimo | Proibido |
|---|---|---|---|
| G-D4 | "Quais especialistas estão disponíveis para me ajudar com informações da DELPI?" | enumeração fundamentada na superfície viva elegível (grupos+escopo), indisponibilidade declarada, distinção disponível×permitido; ou insuficiência honesta | roteamento a READ de negócio, nomes inventados, `agent_directives`/contadores/catálogo como resposta |
| G-D4-neg | idem com provider removido/renomeado/falhando | mesma honestidade via `failures`/relista live | resposta fabricada, stale cache como autoridade |
| G-D5 | "Quais formatos de dados e visualizações estão disponíveis nos painéis operacionais?" | vocabulário de formatos publicado pelo owner (via guidance/READ legítimo) **ou** insuficiência específica com fonte nomeada | dump JSON de catálogo/allowedOps/schema `entities.*` como resposta; filtro global de `entities.playlist` (proibido pelo plano) |
| G-D8 | "Qual é a descrição do material de código 10080043?" | descrição fundamentada + proveniência + rótulos PT-BR naturais | rótulos técnicos crus, perda de records legítimos por filtragem excessiva |

Baseline RED por etapa (a escrever na etapa autorizada, não agora): S1 = meta-pergunta produz projeção de superfície ou gap honesto, nunca READ de negócio; S2 = pergunta de formato nunca renderiza catálogo/schema como resposta; S3 = chave owner fora do mapa nunca aparece como rótulo cru quando vocabulário cobre, e fallback não inventa; S4 = caracterização caller-parity se e somente se extração for executada.

## 5. Cobertura RQ-SA/AC → etapas e gates de entrada

| RQ/AC | Coberto por | Gate de entrada preciso |
|---|---|---|
| RQ-SA01 identidade (24/50) | S1 | S0 aceito; fonte = `DELIA_INTERACTION_INSTRUCTION` (lineage hasheado) + projeção de superfície; sem capacidades inventadas |
| RQ-SA02 especialistas em contratos elegíveis | S1 | G-SA1/G-SA2 EXTEND aprovado; fonte = `ProviderSurface` viva |
| RQ-SA03 publicado×disponível×permitido | S1 | `failures` vivos + declaração AuthZ-em-invoke; negativo AuthZ testado |
| RQ-SA04 D5 formato autoritativo × insuficiência | S2 | S1 aceito; TO_INVENTORY `get_product_guide`; evidência×vocabulário em G-SA3 |
| RQ-SA05 D8 PT-BR/labels/unidades | S3 | S2 aceito; decisão rótulos (recurso governado × mapa in-code) |
| RQ-SA06 selection-only/provenance | transversal | inviolável em S1–S4; `MODEL_AUTHORED_FACTUAL_PROSE=NONE` |
| RQ-SA07 redistribuição funções | S4 | S1–S3 aceitos + matriz atualizada; só `MOVE` com destino existente comprovado; `SKIP_WITH_DECISION` permitido |
| RQ-SA08 generalização | S1–S3/S5 | perguntas inéditas/reformulações/rename+remove provider/multiturno no SHA avaliado |
| RQ-SA09 injection/AuthZ/READ≠ACT | transversal | negativos de segurança por etapa; metadata nunca instrução |

- S1 entra somente após coordenação `ACCEPT|ACCEPT_WITH_RESIDUAL` deste S0. Se S1 constatar ausência de contrato legítimo para listar especialistas (contradizendo §3), `STOP` subescopo → `ARCHITECTURE_DECISION_REQUIRED`.
- S2 exige S1 aceito. S3 exige S2 aceito. S4 exige S3 aceito + matriz §2 revalidada no HEAD da época (drift: reexecutar o mapa, não o inventário).
- Rework: máximo 1 bounded por etapa, restrito ao AC falho.

## 6. Veredicto

```text
STEP=S0
AC_S0_GROUPS_MAPPED=10/10
EXISTING_EQUIVALENT=YES (per-group em §2)
REUSE_DECISION=EXTEND (S1,S2,S3) / PENDING_S4_SKIP_ALLOWED (S4)
D4_GAP=PROJECTION_PATH_GAP (fonte elegível existe)
D5_GAP=SELECTION_EVIDENCE_CLASSIFICATION (contrato READ existe; conteúdo guide=TO_INVENTORY)
D8_GAP=LABEL_VOCABULARY_GAP
CONTRACT_NEW_REQUIRED=NO_DECISION_BY_S0 — proposta tipada nova de admission/goal e
    seção field_labels do recurso governado são evoluções de contratos existentes;
    validação final dos gates em S1/S3
ARCHITECTURE_DECISION_REQUIRED=NONE_EMITTED_BY_S0 (B1 permanece diferido externo)
RUNTIME_DIFF=NONE
TESTS_WRITTEN=0 (caracterização read-only apenas)
NEXT=COORDINATION_VERDICT_S0
```

STOP → RETURN_TO_ARCHITECTURE_COORDINATION

## 7. Parecer independente de coordenação — 2026-10-23

**REVIEWED_SHA:** `5dfdb095c234f3f1b108fec4c2448d9916115c66`. **VERDICT: ACCEPT_WITH_RESIDUAL.** S0 documental aceita: 10 grupos afetados, 3 gaps tipados, consumers mapeados, testes locais 30/30 reportados e zero diff de runtime. A verificação independente confirmou diff/documentação no GitHub; não repetiu os testes executados pelo Devin. S0 não avança C3, I04 ou Q03 e não reabre B1.

**Resíduos não bloqueantes de S0:** (1) `ProviderSurface.groups` declara superfície viva/eligible, mas não concede nem comprova Core/Domain AuthZ individual; metaconsulta sobre acesso deve ser precisa; (2) classe tipada nova de admission/goal é apenas candidata, sujeita a contract gate/reuse antes de diff; (3) conteúdo real de `get_product_guide` continua TO_INVENTORY para S2, não deve ser inferido na S1; (4) novos field_labels são tema S3, não autorização atual. Seleção-only e MODEL_AUTHORED_FACTUAL_PROSE=NONE continuam FROZEN.

**Próximo gate recomendado:** S1 bounded de autoconhecimento (RQ-SA01–03, RQ-SA06/08/09), com reuse de `ProviderSurface.groups`, `CapabilityGroup`, instrução de identidade e proposta LLM existentes, SEM novo engine/registry, SEM branches DAVI/TÉO/VISTA, SEM deploy. Antes do primeiro diff: compatibilidade da proposta tipada, consumers e AuthZ live; se exigir mudança congelada ou contrato owner inexistente, STOP → ARCHITECTURE_DECISION_REQUIRED. S2–S5 permanecem não autorizadas. Máximo 1 rework bounded após parecer independente.

```text
STEP=S0
COORDINATION_VERDICT=ACCEPT_WITH_RESIDUAL
S0_CLOSED=YES
S0_REWORK_USED=0
S1_ENTRY=ELIGIBLE_FOR_BOUNDED_AUTHORIZATION
S2_S5=NOT_AUTHORIZED
PRODUCTION_DEPLOY=NOT_AUTHORIZED
```
