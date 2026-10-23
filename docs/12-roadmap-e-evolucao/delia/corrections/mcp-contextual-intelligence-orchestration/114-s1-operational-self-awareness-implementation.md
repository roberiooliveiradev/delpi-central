# 114 — S1 Autoconhecimento operacional — implementação e evidência

**Track:** `DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01` / STEP=S1
**Plano:** [112](./112-self-awareness-finite-delivery-plan.md) ·
**Matriz:** [113](./113-s0-contract-freeze-and-responsibility-matrix.md)
**Autorização PO:** `f7b6a601cb3770a2e592989d0a83371b95bbfaf0`
(S1–S5 execução contínua com gates)
**Status:** `IMPLEMENTED` — `INDEPENDENT_REVIEW_PENDING`

---

## 1. Escopo e requisitos

Implementa **RQ-SA01–RQ-SA03** com preservação de RQ-SA06/08/09:

- **RQ-SA01** — DÉLIA responde perguntas sobre si mesma e suas
  capacidades reais a partir da superfície viva, nunca de memória do
  modelo.
- **RQ-SA02** — identifica especialistas/superfícies elegíveis conforme
  os grupos observados neste turno.
- **RQ-SA03** — distingue capacidade publicada de permissão efetiva;
  listar uma superfície nunca autoriza invocação.

Gap tratado: **D4 = PROJECTION_PATH_GAP** (doc 113 §4) — a fonte
legítima (`ProviderSurface.groups` vivo) existia, mas nenhum caminho
tipado projetava o *conjunto de superfícies* ao usuário.

## 2. Decisão de implementação (reuse gate)

**EXISTING_EQUIVALENT=YES · REUSE_DECISION=EXTEND.** Nenhum engine,
planner, catálogo paralelo ou branch por especialista criado.

Extensões na fronteira canônica existente:

| Peça | Local | Decisão |
|---|---|---|
| Nova classe tipada `surface_inquiry` | `INTERACTION_ADMISSION_INSTRUCTION` (proposta semântica existente) | EXTEND — mesmo proposal, mesmo gate `requires_owner_surface` |
| Classificação tipada `_admit_conversational_turn` | `orchestration.py` | EXTEND — retorna a classe admitida; allowlist fail-closed |
| Projeção `_surface_inquiry_content` | `orchestration.py` | EXTEND — reusa `_live_interop_surface_lines` + `_redact_text` + bounds existentes |
| `_surface_inquiry_attempt` | `orchestration.py` | ADD — `GovernedCapabilityAttempt` padrão, `NOT_APPLICABLE` + `SURFACE_INQUIRY_ADMISSION` |
| Marcador `SURFACE_INQUIRY_ADMISSION` | `capability_attempt.py` | ADD — mesma família de `EARLY_CONVERSATIONAL_ADMISSION` |
| `LIMITATION_CAPABILITY_SURFACE_LISTING` | `interaction/contracts.py` | ADD — declara ao usuário que listagem ≠ autorização |
| Ramo terminal `_surface_inquiry_result` | `handle_interactive_turn.py` | ADD — mesmo padrão do `_conversational_budget_result` |

## 3. Contrato da resposta D4

1. O modelo de admissão classifica o turno `surface_inquiry` somente
   quando a pergunta mira a **própria superfície governada da DÉLIA**
   (quais especialistas/superfícies estão alcançáveis agora, o que cada
   superfície pode consultar). Conteúdo que um especialista **possui**
   (formatos, guias, tópicos, catálogos owner) permanece `operational`.
2. `requires_owner_surface=false` — nenhuma ferramenta owner roda;
   a resposta é a projeção determinística da listagem viva.
3. O orquestrador chama `self._groups(correlation, deadline)` — os
   mesmos `list_groups` ao vivo usados por qualquer turno governado —
   e projeta `display_name` + linhas DISCOVERY/READ/ANALYSIS bounded
   (mesma forma de `_live_interop_surface_lines`).
4. Falhas de listagem são declaradas honestamente ("uma ou mais
   superfícies não responderam"); superfície vazia informa ausência
   sem inventar nomes.
5. O rodapé declara: *superfície publicada respondeu agora; permissão
   é verificada a cada solicitação concreta — a lista não garante
   autorização.*
6. `EpistemicClass.OBSERVATION`, `GroundingStatus.NON_GROUNDED`,
   `limitations=(capability_surface_listing,)` — metadado de
   planejamento observado, nunca evidência de negócio DELPI.
7. PREPARE/ACT capability names nunca são anunciados como ferramentas
   de consulta (o ciclo de escrita permanece governado).

## 4. Compatibilidade de consumidores (verificada antes de estender)

- `SupportsGovernedCapabilityAttempt` protocol inalterado — o attempt
  usa campos já existentes (`admission_outcome`, `content`,
  `limitations`, `markdown_content`).
- `_admit_conversational_turn` tem **um único chamador** (`attempt()`);
  retorno `bool→str|None` verificado: único uso era `if ...:` truthy.
- Ramo handler inserido **antes** do fallback `NOT_APPLICABLE` genérico;
  marker vazio/sem conteúdo cai no fallback normal (fail-closed).
- Gate arquitetural `test_interaction_runtime_has_no_specialist_branching`
  preservado — vocabulário specialist-free no handler.

## 5. Evidência

**RED→GREEN:** `tests/test_c3_self_awareness_surface.py` — 11 testes.

| Teste | Cobertura |
|---|---|
| sa01 | D4 golden: DAVI+VISTA enumerados, `list_calls` ocorreu, zero invokes |
| sa02 | RQ-SA03: disclaimer publicação≠permissão obrigatório |
| sa03 | Falha parcial de `tools/list` declarada (não inventada) |
| sa04 | Superfície vazia → vazio honesto |
| sa05 | `requires_owner_surface=true` sempre vence — fail closed |
| sa06 | Regressão: `conversation` mantém caminho zero-cost |
| sa07 | Classe desconhecida não furta allowlist (fail-closed) |
| sa08 | Projeção espelha superfície viva verbatim (ÔMEGA sintético; ACT oculto) |
| sa09 | Descrição owner hostil renderiza bounded — dado, nunca instrução |
| sa10 | Handler: terminal determinístico, modelo geral jamais invocado |
| sa11 | Marker sem conteúdo → fallback normal (fail-closed) |

**Resultados factuais:**

- `tests/test_c3_self_awareness_surface.py`: 11/11 PASS.
- Suíte backend completa `tests/`: PASS integral (exit 0) no HEAD da
  etapa, incluindo `test_specialist_interop_architecture`,
  `test_g4_integrated_homologation` (fixture `/plugins` montado),
  `test_c3_contextual_discovery`, `test_conversational_budget_admission_split`.

**Generalização:** a projeção é provider-neutral — consome
`CapabilityGroup`/`ProviderCapability` genéricos; grupo sintético
(ÔMEGA) com READ+ACT prova que renomear/adicionar/remover grupos segue
a superfície viva sem catálogo paralelo nem ramo por especialista.

**Segurança:** descrições owner são dados não-confiáveis renderizados
bounded (≤180 chars/linha, `_redact_text`, cap global); nenhum texto
owner é tratado como instrução; descoberta não infere autorização;
AuthZ/PREPARE-ACT/audit inalterados; `MODEL_AUTHORED_FACTUAL_PROSE`
permanece `NONE` — o conteúdo é projeção determinística.

## 6. Preservação de contratos congelados

- `selection-only` mantido — nenhuma prosa factual model-authored.
- `READ != PREPARE != ACT` intacto; zero invocação neste caminho.
- 60/3/300 inalterado; admissão usa o mesmo budget tipado existente.
- `ProviderCapability.grants_*`/`.authorizes_act()` inalterados.
- Zero migrations, zero deploy, zero mudança AuthZ/Policy/B1.

## 7. Residuais

- `surface_inquiry` cobre perguntas sobre a superfície DÉLIA; perguntas
  híbridas (superfície + dado owner) seguem `operational`/`ambiguous`
  por design — classificação semântica, fail-closed a favor do owner.
- Identidade textual ("quem é você") permanece no instruction de
  identidade existente via prosa conversacional NON_GROUNDED — RQ-SA01
  cobre a parte *operacional* (o que posso consultar agora), que era o
  gap D4.
- `INDEPENDENT_REVIEW_PENDING` — sem parecer de coordenação nesta etapa.

---

```
DÉLIA EXECUTION REPORT — S1

TRACK_ID=DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01
STEP=S1

AUTHORITIES_REVALIDATED=16,50,17,49,51,52,21,20,25 + 24,03,60 + ADR 58
    + roadmap 59 + audits 56-57 + docs 108-113 (reanchor em HEAD)
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND (admission tipada + projeção live existentes)

GAP_RESOLVED=D4 PROJECTION_PATH_GAP
RQ_SA_COVERAGE=RQ-SA01..03 IMPLEMENTED; SA06/08/09 PRESERVED
CONTRACTS_PRESERVED=selection-only; MODEL_AUTHORED_FACTUAL_PROSE=NONE;
    READ!=PREPARE!=ACT; 60/3/300; allowlist admission fail-closed;
    zero provider branches; zero shadow catalog
FILES_CHANGED=orchestration.py, capability_attempt.py,
    interaction/contracts.py, handle_interactive_turn.py,
    tests/test_c3_self_awareness_surface.py (novo)

RED_GREEN=11 novos testes (RED antes da implementação) → GREEN
BACKEND_REGRESSION=suite completa tests/ PASS no HEAD da etapa
GENERALIZATION=provider-neutral (grupo sintético ÔMEGA prova)
SECURITY=no injection path; owner text bounded data; discovery!=authz

MATERIAL_GAPS=identidade puramente textual segue instruction existente
    (prosa NON_GROUNDED) — sem gap material
ARCHITECTURE_DECISIONS_REQUIRED=NONE
EXECUTION_DRIFT=NONE
INDEPENDENT_REVIEW_PENDING=YES
COORDINATION_REVIEW_REQUIRED=YES
```
