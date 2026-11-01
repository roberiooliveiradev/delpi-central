# 28 — VISTA DESIGN INTELLIGENCE — DI-0.1 DEPTH AUDIT & AUTONOMOUS DESIGN BASELINE

**Data:** 2026-10-31 · **HEAD:** `a607aac255` (doc 27) / worktree rebased
**Escopo:** auditoria pura — sem código, sem deploy, sem tools novas.

## Descoberta central — a inteligência é CONSUMIDA no runtime (não só declarada)

`DesignIntelligenceService` (`application/services/data/
design_intelligence_service.py`) é importado pelo
`dispatch_service.py:18` e invocado em caminhos vivos:

| Método | Uso | Profundidade |
|---|---|---|
| `design_intent_for_message` (:3479) | classifica intenção de design por mensagem NL | **N2** — decisão contextual por input |
| `evaluate_methodology` (:3281) | avalia metodologia com tracking epistêmico (`_known`/`_miss` + `epistemic` reason) | **N3→N4** — decisão operacional com tracking verificável |
| `semantic_digest` (:3235) | digest do contexto semântico | **N3** |
| `visual_recommendation` (:3250) | produz recomendação de visual consumida pela resposta | **N3** — conectado a components reais |
| `design_audit` (:3528, :2573) | audita `native_config` — verificável | **N4** — condições de aceitação |
| `_solution_intelligence_on_miss` (:2906, :2999) | gap handling quando dados faltam | **N3** — epistemologia em runtime |

Consumo adicional confirmado: `PresentationRecipeService.
catalog_projection_for_actions` (catálogo projetado para Actions),
`solution_intelligence_service` (gap handling), `vista_agent_
intelligence_service` (persona + orchestration + 16 seções de
conhecimento projetadas).

**KNOWLEDGE_DELIVERY_GAP: não confirmado** — a inteligência é projetada
via `vista_agent_intelligence_service.projection` e consumida por
`DesignIntelligenceService` dentro do dispatch (não apenas arquivo
morto). O modelo recebe metodologia via projeção aprovada (`catalog`/
`knowledge`/`analyze` responses), não por acesso direto ao JSON.

## Estado da orquestração — matriz honesta

| Transição | Estado | Evidência |
|---|---|---|
| intent → design_intent | N2 PROVEN | `design_intent_for_message` |
| intent → visual | N3 PROVEN | `visual_recommendation` em `analyze` |
| context → methodology | N3/N4 PROVEN | `evaluate_methodology` + epistemic |
| compose → propose | N3 PROVEN | `composition_order`, `composed_visuals` |
| proposal → prepare → commit | N4 PROVEN | six-verbs + A5 (B1–B5 certified) |
| read-back → verify | N4 PROVEN | VERIFIED pattern (todos os waves) |
| quality → visual verify | N3 TO_INVENTORY | `design_audit` existe; rubrica Q1–Q10 objetiva não calibrada |
| NL → E2E authoring | N2 TEST_NOT_RUN | caminho existe, benchmark A–E não executado (sem mutations prod) |

## Componentes / design system

`design_intelligence.json.componentSpecs` existe — inventário detalhado
por componente não auditado nesta onda (recomendo DI-1 cobrir).
Design tokens DELPI canônicos: `TO_INVENTORY` — não presumir.

## Rubrica Q1–Q10 (proposta — hipótese a calibrar)

Objetivo, indicadores, escolha visual, hierarquia, legibilidade,
densidade, semântica de cores, integridade de dados, adequação TV,
paridade — `design_audit` já audita parte delas; pesos/notas =
`PLANNED` (calibração requer evidência visual real).

## Benchmark A–E — `TEST_NOT_RUN`

Não executado nesta fase: não há caminho para invocar `analyze`
com os 5 cenários e observar a proposta sem side-effects + sem
credenciais de homologação autenticadas nesta sessão — evidência
a coletar em ambiente autorizado (mesmo canal do handoff A5).

## Matriz de lacunas definitiva

| Gap ID | Lacuna | Camada | Nível | Reuse |
|---|---|---|---|---|
| DG-1 | Auditoria tópico-a-tópico da profundidade prescritiva | knowledge | N1→N3 | EXTEND |
| DG-2 | Rubrica Q1–Q10 calibrada + objetiva | analyze/quality | N3→N4 | EXTEND (`design_audit`) |
| DG-3 | Catálogo de indicadores por domínio (owner dados) | data contract | TO_INVENTORY | owner `api-delpi` |
| DG-4 | Design tokens DELPI canônicos | design system | TO_INVENTORY | `componentSpecs`? |
| DG-5 | Benchmark A–E E2E certificado | authoring | TEST_NOT_RUN | EXTEND |
| DG-6 | Visual verification motor (screenshot/diff paridade) | verify | TO_INVENTORY | `visual_verification` tópico |

## Decisão DI-1–DI-5

| Onda | Decisão | Justificativa |
|---|---|---|
| DI-1 Knowledge profissional | **GO_WITH_PREREQUISITES** | camada existe (N2–N3); precisa auditoria de profundidade + extensão de conteúdo — **não é reescrita** |
| DI-2 Design reasoning | **HOLD** | `visual_recommendation`/`design_intent` já N3 — reavaliar após DI-1 |
| DI-3 Composição assistida | **GO_WITH_PREREQUISITES** | `composition_order`/`composed_visuals` existem; E2E do benchmark é o pré-requisito |
| DI-4 Quality verification | **GO** | `design_audit` é a base — evoluir para rubrica Q1–Q10 com evidência |
| DI-5 Governed authoring | **GO_WITH_PREREQUISITES** | pipeline + A5 + six-verbs já certificados (B1–B5); precisa benchmark E2E primeiro |

## Veredito

**`DI01_AUDIT_PARTIAL`** — auditoria confirmou inteligência profunda e
consumida (N2–N4 em várias regras); lacunas identificadas (DG-1–DG-6);
benchmark E2E e inventário por componente pendentes como pré-requisitos
para DI-3/DI-5. **Nenhuma onda justifica engine/registry/tool novo —
todos os gaps são EXTEND sobre mecanismos existentes.**
