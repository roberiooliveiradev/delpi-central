# 117 — S4 Redistribuição da orquestração — análise e SKIP_WITH_DECISION

**Track:** `DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01` / STEP=S4
**Plano:** [112](./112-self-awareness-finite-delivery-plan.md) §9 ·
**Matriz:** [113](./113-s0-contract-freeze-and-responsibility-matrix.md)
**Status:** `SKIP_WITH_DECISION` — `INDEPENDENT_REVIEW_PENDING`

---

## 1. Pergunta da etapa

Existem responsabilidades de apresentação em `orchestration.py` com
destino legítimo **comprovado** (owner, consumidores, contrato,
regressão mapeados)? A diretriz §9 proíbe mover por LOC/estética e
proíbe inventar abstração para viabilizar extração.

## 2. O que já foi redistribuído em S3 (evidência, não opção)

| Responsabilidade | Destino | Estado |
|---|---|---|
| Vocabulário de rótulos (`_FIELD_CLAUSE_LABELS`, 183 entradas) | `config/cri_presentation.delpi.json` v4 `field_labels` | MOVIDO |
| Validação do vocabulário | `cri_instruction_resource.py` `_field_label_entries` | MOVIDO |
| Resolução de rótulos (display + clause + fallback) | `conversational_response.py` (leaf existente) | MOVIDO |
| Loader wiring | `root_composer.py` (incondicional) | ESTENDIDO |

A única resolução de rótulos para CRI, detalhe, cláusula, lista e
comparação já reside no componente de apresentação legítimo — o AC
§9(b) de paridade CRI/não-CRI está verde na suíte.

## 3. Candidatos restantes e por que não há destino

### G-SA5 — família guidance (`_guidance_family_for_key`,
`_render_guidance_value`, `_deterministic_guidance_content`,
`_select_guidance_records`, `_guidance_section_records`)

Depende de `_canonical_key`, `_sanitize_renderable`, `_redact_text`,
`_CONTROL_PLANE_KEYS`, `_GUIDANCE_META_KEYS`,
`_CAPABILITY_VOCABULARY_KEYS` — utilitários compartilhados usados
~103× por filtragem de control-plane, evidência, resolver e records
(não são apresentação). `conversational_response.py` é leaf que
orchestration importa — mover a família para lá exige importar
orchestration → **ciclo**. `paginated_result_semantics.py` é leaf
com contrato de paginação, não de projeção de guidance. Nenhum leaf
existente é destino legítimo — **confirma o veredito prévio do doc
113 (MOVE_CANDIDATE→PENDING_S4)**.

### G-SA6 remanescente — construção de frases
(`_compose_answer`, `_detail_header`, `_detail_lines`,
`_proven_field_differences`, `_list_header`, `_render_synthesis`,
`_synthesis_selections`, `_record_identifier`)

Mesma barreira: `_canonical_key`, `_redact_text`,
`_sanitize_renderable`, `_IDENTIFIER_KEYS`, `_UUID_VALUE_RE`,
`_PRESENTATION_INTENTS`, `MAX_RENDER_CONTENT_CHARS`,
`_synthesis_selections`. A resolução de rótulos (a parte que o §9
apontou como desvio) já saiu; o restante é projeção estrutural
acoplada à sanitização/seleção de evidência — responsabilidade
central do orquestrador ("coordenação das capabilities e do fluxo
operacional", plano §4 S4).

### Criar um novo leaf (`record_presentation.py`)?

Avaliado e **rejeitado**: o plano §9 exige destino
"existente/legítimo" e proíbe abstração só para reduzir o arquivo.
Um novo módulo arrastaria `_canonical_key` + sanitizers para um
local com nome errado (não são de apresentação) ou criaria um
segundo canônico para eles — ambas divergências proibidas.

## 4. Decisão

**SKIP_WITH_DECISION.** Extração legítima realizada (rótulos, S3);
demais famílias permanecem no orquestrador por ausência de destino
legítimo sem nova abstração. Nenhuma mudança em B1, AuthZ,
PREPARE/ACT, Policy ou contratos congelados.

Mapa de consumidores (inalterado pela decisão):
`root_composer` → `OperationalCapabilityOrchestrator` →
`SupportsGovernedCapabilityAttempt` → `HandleInteractiveConversationTurn`;
apresentação: `conversational_response.compose_cri_response` +
resolvers de rótulos importados por orchestration.

## 5. Resíduos

- Se um futuro trabalho separar sanitização/seleção de evidência em
  um leaf próprio (contrato próprio, não este plano), a família de
  frases ganha destino legítimo — `TO_INVENTORY` fora do escopo.
- `INDEPENDENT_REVIEW_PENDING`.
