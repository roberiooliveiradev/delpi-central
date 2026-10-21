# 78 — CRI E3 · Personality & grounded conversational presentation — execution report

**TASK_ID:** `DELIA-CRI-E3-PERSONALITY-AND-GROUNDED-PRESENTATION-01`
**Data:** 2026-10-21 · **Base:** `origin/main` `b8aceafe11…`
**Tipo:** implementação funcional bounded — primeira resposta
conversacional da frente CRI.

Estados de entrada revalidados nas fontes canônicas do HEAD
(docs 73–77, ledger §6.354): `CRI_E0/E1/E2=ACCEPT_WITH_RESIDUAL`,
`CENTRAL_FEATURE_CONTROL=IMPLEMENTED`, `DEFAULT_STATE=OFF`,
`PERSONALITY_BASELINE=APPROVED_PRODUCT_DIRECTION`,
`SELECTION_ONLY=FROZEN`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`.

## 1. Escopo entregue

A DÉLIA deixou de devolver apenas renders técnicos no modo ON: a
aresta governada outcome → response agora **compõe a resposta** a
partir do veredito E2 + evidências sanitizadas do owner — resposta
principal primeiro, evidências legíveis, avisos de limitação honestos
e uma oferta de continuidade quando existe detalhe real a explorar.

Nenhuma camada decorativa, nenhum planner novo, nenhuma chamada extra
ao modelo, nenhuma segunda flag. Toda a funcionalidade é isolável
pelo controle central da E1.

## 2. Contratos e reutilização (Reuse Gate)

| Conceito | Decisão | Onde |
|---|---|---|
| `SpecialistOutcome`/`GovernedCapabilityAttempt`/wire | REUSE — conteúdo continua `attempt.content`, limitações no contrato existente | `orchestration.py` |
| Verdict E2 (`assess_outcome`/`EvidenceFacts`/`AnswerRequirements`) | REUSE — um único veredito alimenta marcação E2 e composição E3 | `_attempt` binding edge |
| `compose_presentation` (contrato v1) | REUSE — conteúdo CRI flui pelo bloco `text` existente | `presentation.py` (inalterado) |
| Frontend (`ConversationMarkdown`, adapter `presentation.ts`) | REUSE — zero alterações; v1 renderiza markdown plano | `plugins/delia` (inalterado) |
| Loader declarativo CRI (E2-R3) | EXTEND — mesmo módulo, mesmo contrato fail-closed, segundo recurso para consumidor distinto | `cri_instruction_resource.py` |
| Helpers de prova E2 | EXTEND — `_temporal_proofs` agora retém o campo que prova a direção; wrappers públicos `ordering_proof_fields`, `distinct_delivered_count`, `parse_temporal_value` | `outcome_assessment.py` |
| Vocabulário de rótulos existente (`_FIELD_CLAUSE_LABELS`, `_IDENTIFIER_KEYS`) | REUSE — rótulos PT-BR e identificador verbatim | `orchestration.py` |
| Sanitização/redação (`_sanitize_renderable`, `_redact_text`) | REUSE — valores apresentados são folhas sanitizadas do owner | `orchestration.py` |
| Personalidade `personality/01–04` (PERS-001..018) | REUSE — decisões aprovadas aplicadas como *forma*, nunca como autoridade | mapeadas em §7 |

`EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=REUSE+EXTEND` — nenhuma
segunda camada de render, nenhum registry paralelo.

## 3. E3-G1 — modo efetivo ON/OFF (residual E2 resolvido)

`root_composer` agora distingue **requested** (configuração confiável)
de **effective** (pós-validação de recursos):

```text
requested = settings.response_intelligence_enabled
resources = clause AND vocabulary (mesmo try — qualquer falha invalida)
effective = requested AND resources válidos
```

O modo efetivo único é propagado para o orquestrador **e** para o
handler — `stage=response_mode` nunca registra `cri` quando o
fallback desativou o fluxo. Log de composição:

```text
delia_response_intelligence requested=cri effective=baseline
config_source=environment runtime_sha=…
```

Matriz exigida coberta e testada (`test_g1_*`):

| Config | Recurso | Efetivo | Prova |
|---|---|---|---|
| OFF | qualquer | BASELINE | `test_g1_requested_off_is_baseline_regardless_of_resources` |
| ON | válido | CRI | `test_g1_requested_on_valid_resources_effective_cri` |
| ON | vocabulário inválido | BASELINE | `test_g1_requested_on_invalid_vocabulary_effective_baseline` |
| ON | vocabulário ausente | BASELINE | `test_g1_requested_on_missing_vocabulary_effective_baseline` |
| ON | cláusula inválida | BASELINE | `test_g1_requested_on_invalid_clause_effective_baseline` |
| inválida | qualquer | BASELINE | `Settings._env_flag` fail-closed (E1) |

## 4. E3-G2 — contagem apresentada (residual E2 resolvido)

Quatro contagens distintas, nunca confladas:

- **available** — `facts.total_count` declarado pelo owner (citado só
  como aviso atribuído: «A fonte informa N registros no total.»);
- **returned** — registros no envelope/structured;
- **delivered** — `distinct_delivered_count` (dedup por igualdade
  estrutural — duplicatas nunca inflam exemplos);
- **presented** — linhas efetivamente emitidas no conteúdo.

Regras provadas:

- `min_items=N` satisfeito → apresenta-se exatamente N (ou o teto de
  apresentação); o lead carrega a contagem **apresentada**;
- `presented < returned` → aviso `truncation_notice` + limitação
  `result_truncated`;
- `presented < requested` → re-marca `insufficient_evidence` — a
  projeção nunca declara sucesso omitindo registros;
- `coverage_complete=False` sem truncamento → `available_notice`
  (com total) ou `more_available` (sem total);
- duplicatas colapsam na emissão — um payload nunca vira duas linhas;
- observabilidade: `stage=cri_response decision=composed|fallback
  presented=N delivered=M correlation_id=…`.

## 5. Implementação

**`conversational_response.py` (novo módulo-folha)** — composição
determinística por *forma de veredito*, não por provider/assunto:

- `answered` + `ordering` → lead nomeia o registro extremo
  (identificador — título, verbatim) + cláusula temporal formatada
  (`DD/MM/YYYY às HHhMM`) do campo que **provou** a ordenação;
- `answered` + `min_items` → lead de quantidade + linhas de evidência;
- `answered` genérico → lead de contagem/único + linhas legíveis
  (`Rótulo: valor`, booleanos `sim`/`não`, datas pt-BR, teto 5
  registros × 4 campos);
- `insufficient`/`envelope_only`/`empty_result` → mensagem honesta por
  razão proximária (`coverage_unproven`, `ordering_unproven`,
  `fewer_than_requested`, `quantity_unproven`, `partial_outcome`);
- continuidade (`detail_offer`) somente quando registros apresentados
  têm campos não exibidos — sugestão real e servível via reply;
- `None` → fallback para o render sintetizado existente (a composição
  é melhoria, nunca dependência de correção).

**`orchestration.py`** — `_cri_presented_record` projeta cada registro
em `PresentedRecord` (sanitizado, rótulos humanizados, identificador
primeiro, escalares apenas); `_compose_cri_response` alimenta a folha
com veredito, requisitos, `delivered_count`, `total_count`,
`coverage_complete` e `ordering_date`; o veredito passa a ser
computado uma vez em `_attempt` e compartilhado entre
`_apply_outcome_assessment` e a composição. Prior-turn excerpts
mantêm o render existente.

**`cri_presentation.delpi.json` (novo recurso governado)** —
`resource_id=delia.cri.presentation_vocabulary`, `version=1`,
`kind=presentation_vocabulary`, `owner=DELPI`, seções `leads`,
`temporal_clauses`, `insufficiency`, `continuity`, `labels` —
placeholders restritos à allowlist
(`identifier/date/count/presented/returned/available/requested/
delivered/total`).

**`cri_instruction_resource.py`** — `_load_resource_object` +
`_validate_identity` compartilhados; `load_cri_presentation_vocabulary`
valida identidade/kind/versão, chaves extras, seções exigidas,
entradas exigidas, tipos str→str, limites (≤32 entradas, ≤512B),
placeholders desconhecidos — fail-closed, `content_hash` SHA-256
sobre as seções canônicas.

**`root_composer.py`** — caminho fixo `_CRI_PRESENTATION_PATH`
(nunca request/env); ambos os recursos no mesmo try; `effective`
propagado; log `requested=…/effective=…`.

## 6. Personalidade aplicada (PERS-*)

Decisões aprovadas mapeadas para forma observável — personalidade
nunca vira autoridade:

- **resposta primeiro, detalhes depois** → lead sempre precede
  linhas de evidência;
- **clara e objetiva** → uma frase de lead, campos limitados, sem
  blocos decorativos;
- **reconhece limitações** → mensagens de insuficiência por razão
  proximária, nunca silêncio ou sucesso falso;
- **proporcional e não intrusiva** → uma única oferta de continuidade,
  apenas quando há detalhe real;
- **transparência de origem** → totais do owner citados como
  atribuídos («A fonte informa…»), nunca como fatos da DÉLIA;
- **evidence discipline** → todo valor é folha verbatim sanitizada;
  o modelo não escreve prosa factual (selection-only congelado).

## 7. Casos de avaliação e generalização

- **TEO** («último processo alterado») — ordenação+cobertura provadas
  → «O registro mais recentemente alterado foi PROC-0080 —
  Monitoramento de Estoque. A última alteração registrada ocorreu em
  16/10/2026 às 10h57.»; sem prova → `ordering_unproven` honesto.
- **DAVI** («três exemplos de terminal bandeira») — 3 entregues →
  lead «3 exemplos»; total=10/entregues=2 → `fewer_than_requested`,
  «10» nunca aparece como resultado.
- **DELPI** («três exemplos, grupo 1008») — mesma forma min_items;
  duplicatas colapsam; projeção curta re-marca insuficiência.
- **VISTA** («playlists») — campos humanizados, booleanos `sim`/`não`,
  estrutura legível sem interpretação não autorizada.
- Generalização coberta em teste: listas grandes (truncamento +
  aviso), registro único, cobertura incompleta, resultado vazio,
  envelope-only, dados maliciosos (injetados como *valor*, nunca
  como instrução), recurso ausente/inválido/desconhecido.

## 8. Evidência

- `tests/test_cri_e3_conversational_presentation.py` — **42 testes**:
  loader (12), composer por forma (15), integração ON/OFF (8), G1
  composição (5), helpers públicos (2).
- Focado E1+E2+E3: **130 passed**.
- Suíte completa `delia-api`: **1823 collected, 1820 passed,
  3 skipped, 0 failures** (JUnit XML; um flake temporal isolado de
  `test_activity_streaming` passa standalone e na reexecução —
  timing `time.sleep`, fora do diff).
- `ADDITIONAL_MODEL_CALLS=0` — contagem de requests OFF vs ON igual.
- OFF = byte-idêntico (mesmo conteúdo, mesmas limitações, sem
  estágio); rollback = env + restart (E1).
- Residual search limpo: nenhum texto CRI em Python fora dos
  recursos, nenhum atalho `total_count>=`, nenhum segundo
  planner/flag/registry, contrato de apresentação v1 intacto,
  frontend inalterado.

`PUBLIC_CONTRACT_CHANGE=NO` (presentation v1 inalterado);
`FRONTEND_FILES_CHANGED=0`; `SELECTION_ONLY=PRESERVED`;
`AUTHORITY_BOUNDARIES_PRESERVED=YES`; `MATERIAL_ACT=0`;
`PRODUCTION_DEPLOY=NO`; `REAL_MODEL_EVALUATION=NOT_RUN` (E4);
`I04_ACCEPTED=NO`; `C3_EXECUTED=NO`.

## 9. Resíduos

- A composição E3 cobre o caminho de leitura principal
  (`_attempt` pós-síntese); corroboração e outros caminhos de outcome
  mantêm o render existente — intencional, mesmo boundary E2.
- Vocabulário v1 cobre as formas de veredito; perguntas cujo
  veredito é `answered` sem requisitos declarados recebem a forma
  genérica (lista/único) — adequada, sem claims extras.
- Registros exclusivamente aninhados (sem escalares) não geram linha —
  o detalhe segue disponível pelos caminhos existentes; o composer
  degrada para o render sintetizado.
- `REAL_MODEL_EVAL=TEST_NOT_RUN` — qualidade real OFF/ON com modelos
  e especialistas reais é escopo E4.

`E3_IMPLEMENTED=YES`; `E3_ACCEPTED=PENDING_INDEPENDENT_REVIEW`;
`NEXT=COORDINATION_REVIEW_THEN_E4`.
