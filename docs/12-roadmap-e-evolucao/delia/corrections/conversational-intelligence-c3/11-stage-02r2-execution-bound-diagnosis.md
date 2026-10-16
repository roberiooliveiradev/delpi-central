# 11 — Diagnóstico Etapa 02R2: execution bound textual vs interpretação do modelo

**Task:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-02R2-DIAG`
**Data:** 2026-10-16
**MODE:** `DIAGNOSIS_AND_ARCHITECTURE_DECISION_ONLY` — nenhuma linha de código produtivo alterada.
**REVIEWED SHA:** `9fd3a7bc959686a6c4828f46b7d292c81a96938c` (veredicto §6.176: B1 `PASS_STRUCTURAL`, B2 `REWORK`)
**BASE_HEAD:** `0018906278191c8366602c6d68d8449e6c7bd644` (main local; origin/main `479c128e86`; reviewed SHA na ancestry)
**Veredicto da tarefa:** `ARCHITECTURE_DECISION_REQUIRED` — ver §7.

## 1. Gate de entrada e reancoragem

- `git rev-parse HEAD`, `git status`, `origin/main` verificados; working tree contém trabalho concorrente do usuário (plugins/requests-api/bpmn + 3 commits locais unpushed) — preservado, nada restaged.
- Autoridades reancoradas 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 → 24 → specs 60/69/70 → personality → ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.171–6.176.
- Estado vigente confirmado no HEAD efetivo: `STAGE_02R1_REVIEW=REWORK`; `B1=PASS_STRUCTURAL`; `B2=REWORK`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`. Sem `EXECUTION_DRIFT`.
- Documentos lidos integralmente: 02, 03, 05, 07, 08, 09, **10** (revisão §6.176) + README.

## 2. Inventário do fluxo real (mapa de autoridade)

| Ponto | RESPONSIBILITY | OWNER | CONTRACT | TRUST | VALIDATION | FAILURE | EXECUTION EFFECT |
|---|---|---|---|---|---|---|---|
| `input_text` ("não aplique") | enuncia intenção e restrição | usuário | string livre | **autoridade de intenção**, mas só legível via modelo | nenhuma (texto) | — | só afeta execução via interpretação |
| `InteractiveTurnRequest.max_execution_stage` | teto reduction-only do request | cliente → `handle_interactive_turn` | `None \| "prepare"` | untrusted, reduction-only | `_validate_execution_ceiling` (linha 672): qualquer outro valor → `InteractionError` | fail-closed | `prepare_only=True` bloqueia as 3 fronteiras ACT |
| `confirmation` payload | decisão estruturada sobre write pendente | cliente | digest+session+fingerprint+decision | untrusted; vincula a `PendingWrite` backend | `_attempt_confirmation`: digest/actor/session/fingerprint/decisão | fail-closed em cada dimensão | CONFIRM → `_execute_prepared_act` |
| `GOAL_INSTRUCTION` → `_understand_goal` | interpretação semântica do turno | DÉLIA (modelo) | proposta JSON bounded | **HYPOTHESIS — nunca autoridade** | `allowed_keys` (rejeita proposta inteira) + `_GOAL_CLASSES` + `_OUTPUT_MODES` + `_EXECUTION_BOUNDS` | proposta inválida → `_TurnGoal` neutro (`declared=False`) | alimenta gate de finalidade + bound |
| `_TurnGoal.execution_bound` | bound textual validado | DÉLIA | `unrestricted \| prepare_only` | derivada de HYPOTHESIS | whitelist; **ausente/inválido → `"unrestricted"`** | **fail-OPEN** | `== "prepare_only"` reduz o teto |
| `prepare_only` efetivo | teto do turno | `_attempt` | `request_ceiling OR bound=='prepare_only'` | composição reduction-only | — | — | alimenta `_attempt_prepare`, `_attempt_direct_act`, `_attempt_confirmation` |
| `confirmation_requirement` (PREPARE) | política de confirmação | owner (untrusted data, structural) | `explicit_user_confirmation` | owner-declared | `_effective_confirmation_policy` | `owner_policy_invalid` quando ausente | `False` → continuação direta elegível (§6.140) |
| `evaluate_write_continuation` + `_execute_prepared_act` | decision gate + ACT | DÉLIA → owner | decision estruturada | gates determinísticos | live revalidation + AuthZ owner | `write_gate_blocked` | única via de ACT |

**Fatos centrais:**

1. `attempt(confirmation=...)` retorna em `_attempt_confirmation` (linha 2535) **antes** de `_select_target` e `_understand_goal` — o path de confirmação **não recebe `input_text`**; só o teto estruturado do request se aplica.
2. `expected_fields` em `_propose` é **metadata do adapter**, não validação — a única validação estrutural é `Mapping` + `allowed_keys` (rejeição total). Campo esperado ausente **não** rejeita a proposta.
3. `execution_bound` ausente ou inválido → coagido a `"unrestricted"` com `declared=True` (válido via `goal_class`). O runtime **não distingue** "modelo declarou ausência de restrição" de "modelo não considerou restrição".
4. O bound textual não existe em nenhum outro canal legível por máquina: `prior_turns`, `workspace_context`, `confirmation` e `max_execution_stage` não transportam restrição semântica do texto.

## 3. Respostas às perguntas obrigatórias

- **O que comprova positivamente que não há limite?** Hoje: nada — `unrestricted` é default de coerção, não evidência. PROVEN por leitura.
- **`unrestricted` significa ausência de restrição ou apenas que o modelo não identificou?** Apenas o segundo; ambos os casos colapsam no mesmo valor. PROVEN.
- **Bound omitido?** → `unrestricted`, `declared=True`, write path elegível (DIAG-02 FAIL).
- **Bound inválido?** → `unrestricted`, idem (DIAG-03 FAIL).
- **Request traz representação estrutural do limite?** Só `max_execution_stage` — depende de o cliente preencher; o texto não o alimenta. PROVEN.
- **Quem pode legitimamente reduzir o limite?** Hoje: request ceiling + bound validado do modelo. Nenhum consumer adicional existe. PROVEN.
- **Como a restrição textual chega ao gate?** Somente via interpretação do modelo (`GOAL_INSTRUCTION`). PROVEN.
- **Caminhos para ACT sem essa verificação?** Dois: continuação direta PREPARE→ACT (`CONFIRMATION_POLICY_DIRECT and not prepare_only`) e confirmação estruturada (`_attempt_confirmation`). Ambos respeitam o teto estruturado; apenas o primeiro consome o bound textual. PROVEN.
- **Confirmação estruturada pode conflitar com texto atual?** O path de confirmação não interpreta texto — precedência CONFIRM↔texto contraditório é **lacuna de especificação** (DIAG-08, ver §4).
- **Invariantes já resolvidos?** ceiling reduction-only, confirmação estrutural owner-sealed, idempotência/digest/fingerprint, live revalidation, AuthZ owner, HYPOTHESIS epistemic — não recriar. PROVEN.

## 4. Testes adversariais (harness scripted, FakeProposalModel — SHA avaliado `9fd3a7bc95`, rerun no HEAD local)

Arquivo: `delia-api/tests/test_stage02r2_execution_bound_diagnosis.py` (16 casos; defeitos conhecidos como `xfail(strict=True)` — documentação do RED sem quebrar a suíte).

| Caso | Scripted | Esperado (segurança) | Observado | Resultado |
|---|---|---|---|---|
| DIAG-01 contradição explícita | text 'não aplique' + `unrestricted` + ceiling None + owner direct + ACT | zero ACT | `commit_record` **invocado** | **FAIL** (xfail) |
| DIAG-02 bound ausente | idem, campo omitido | zero ACT | `commit_record` invocado | **FAIL** (xfail) |
| DIAG-03 bound inválido | `execution_bound='never_apply'` | zero ACT | `commit_record` invocado | **FAIL** (xfail) |
| DIAG-04 teto estruturado | `max_execution_stage='prepare'` + `unrestricted` | zero ACT | bloqueado (`CONFIRMATION_REQUIRED`) | **PASS** |
| DIAG-05 controle positivo | 'Crie um cadastro.' + `unrestricted` + direct | continuação direta preservada | `stage_record`→`commit_record`, SUCCESS | **PASS** |
| DIAG-06 bound só reduz | 'Crie um cadastro.' + `prepare_only` | ACT bloqueado | `CONFIRMATION_REQUIRED`, sem commit | **PASS** |
| DIAG-07 variantes ×6 | 6 formulações prepare-only + `unrestricted` | zero ACT | `commit_record` invocado em **todas** | **FAIL** (xfail ×6) |
| DIAG-08 confirmação + texto contraditório | CONFIRM válido + text 'Não aplique.' | investigação | texto **não interpretado**; CONFIRM governa; ACT executado | observado — **lacuna de especificação**, não exploit provado |
| DIAG-08b teto no path de confirmação | `max_execution_stage='prepare'` + CONFIRM | zero ACT | `WRITE_REJECTED execution_ceiling` | **PASS** |
| DIAG-09 superfície renomeada | provider/group/caps renomeados + `unrestricted` | zero ACT | `post_entry` invocado | **FAIL** (xfail) |
| DIAG-09b owner sem ACT | PREPARE-only + `unrestricted` + direct | zero ACT | `WRITE_REJECTED` fail-closed (nenhum ACT possível) | **PASS** |

**Suíte completa:** `delia-api` — **1091 passed + 10 xfailed** (exit 0). Nenhum expected de outro teste alterado; nenhuma fixture modificada para evitar o cenário crítico.

## 5. Root cause (PROVEN)

O bound textual é um campo da **proposta do modelo** — o único componente que lê semanticamente o texto. `_understand_goal` normaliza ausência/invalidade para `'unrestricted'` (**fail-open para mais autoridade**), e nenhum estágio posterior coteja o bound com a mensagem. Sob owner `confirmation=False` + ceiling `None`, a continuação direta (§6.140) é elegível apesar do 'não aplique'. **A assimetria é estrutural:** `prepare_only` é honrado porque reduz; `unrestricted` é confiado porque permite. Para uma restrição **negativa** no texto, a única fonte de verdade é o texto — e só o modelo o lê.

## 6. Reuse-before-design

| Mecanismo | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Execution ceiling (`prepare_only`/3 fronteiras ACT) | YES | REUSE — já consome qualquer redução |
| Goal interpretation (`_understand_goal`/`_TurnGoal`/`declared`) | YES | EXTEND — mesmo padrão do fix B1 |
| `_propose` allowed_keys/validação | YES | REUSE — fail-closed já existe |
| Request contract `max_execution_stage` | YES | REUSE — reduction-only já validado |
| Confirmação estruturada / decision gate | YES | REUSE — não tocar (§6.140) |
| Segundo estágio de verificação semântica | NO | — não projetado; exigiria decisão |
| Parser/regex textual | NO (proibido) | — |

## 7. Alternativas comparadas (sem implementação)

### A — Contrato estruturado reduction-only (extensão do request)
Elevar o bound a campo estruturado do request (como `max_execution_stage`). **Owner legítimo:** contrato de turno existente. **Problema fatal:** quem preenche? O cliente/MFE não entende semântica do texto — viraria parser no frontend (proibido, e frontend não é autoridade). O campo só funciona quando o chamador já sabe da restrição — caso típico em que não sabe. **Não cobre DIAG-01/02/07.** Veredito: insuficiente isolada; já existe e está correto para o que cobre.

### B — Verificação de consistência semântica antes de ACT
Estágio independente re-lendo o texto ("o usuário restringiu a execução?"). **Cobre DIAG-01** — único mecanismo que pega a contradição positiva. **Custos:** nova chamada de modelo (latência/tokens), mesma classe de falha (mitiga, não elimina), nova instrução/version lineage — exige evidência de necessidade e autorização; é materialmente um novo gate. **Sem isso, DIAG-01 é irredutível:** nenhum consumer não-modelo lê o texto. Veredito: única cobertura do caso crítico, mas `ARCHITECTURE_DECISION_REQUIRED`.

### C — Tratamento conservador de incerteza (fail-closed no bound)
Espelhar o fix B1: bound **ausente ou inválido** em objetivo declarado de ação → não é prova de `unrestricted` → `CLARIFICATION_REQUIRED` ("Quer que eu apenas prepare, ou também aplique?"). `unrestricted` **explicitamente emitido** continua honrado (simetria com `goal_class`). **Cobre DIAG-02/03 e endurece DIAG-07**; **não cobre DIAG-01** (afirmação positiva errada permanece — mesmo resíduo já aceito para `goal_class` misclassification). **Compatível com §6.140** (não é confirmação universal: só dispara quando a interpretação falhou). **Mudança:** `_understand_goal` distingue campo-ausente/inválido de valor-presente + instrução (v9→v10) — EXTEND sobre contrato existente, ~dezenas de linhas. **Falso bloqueio:** modelo que omite o campo em pedido irrestrito → 1 clarificação extra (custo de disponibilidade, direção fail-safe). Veredito: menor correção legítima para a parte contratável — `CONTRACT_EXTENSION_REQUIRED`.

### Recomendação fundamentada
**C como base** (fecha o vetor fail-open: ausente/inválido nunca vira `unrestricted` silencioso) **+ decisão explícita da coordenação sobre o residual DIAG-01**: (i) aceitar resíduo model-trust — mesma classe já aceita para `goal_class` misclassification, ou (ii) autorizar B (estágio de verificação bounded) com custo documentado. A precedência CONFIRM↔texto (DIAG-08) deve ser especificada na mesma decisão — hoje CONFIRM governa e o texto é ignorado; se a coordenação quiser veto textual, é contrato novo.

**Classificação final:** `ARCHITECTURE_DECISION_REQUIRED` — o caso crítico nomeado pelo reviewer (afirmação positiva errada) não fecha por extensão de contrato; exige aceite de resíduo ou mecanismo materialmente novo. A alternativa C é recomendada independentemente do veredicto sobre o residual.

## 8. Limitações

- Todos os resultados são com `FakeProposalModel` scripted — frequência de misclassification em modelo real = `TEST_NOT_RUN`.
- DIAG-08 registrado como lacuna de especificação; não houve prova de exploit (CONFIRM estruturado é ato explícito do usuário).
- Nenhum código produtivo alterado; xfail marca defeito conhecido, não aceite.

## 9. Estado

`B2_DIAGNOSIS=RECORDED`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; nenhuma implementação autorizada. Relatórios 04–10 preservados.

NEXT = STOP → RETURN_TO_ARCHITECTURE_COORDINATION
