# 42 — Playbook GPT Brief → Cursor → Execution Report → GPT Review (V1)

> **REBASELINE 24/10/2026:** O procedimento de brief/relatório abaixo permanece aplicável, mas cada execução da Central deve selecionar o **slice e checkpoint atuais** do [Documento 93 — Roadmap executivo E2E com checkpoints reais](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md); consultar também docs 90–92 e TÉO/PROC-0072. Não usar a ordem de implementação 16/10 para autorizar código novo. `IMPLEMENTATION_AUTHORIZED=NO` até GO explícito.
**Estado:** TARGET / PLANNED / DOCUMENTATION_ONLY. Guia para os [slices IMP](./40-matriz-dependencias-e-slices-v1.md), subordinado a [39 — Roadmap](./39-roadmap-mestre-implementacao-v1.md) e aos [gates de qualidade](./41-estrategia-validacao-e-gates-implementacao-v1.md).

## 1. Regra de entrada e authorities

**Não implementar runtime** sem `DOCUMENTATION_CLOSURE_COMPLETE=PASS`, quatro freezes transversais com evidência e aprovação posterior explícita do PO (`IMPLEMENTATION_AUTHORIZED=YES`). Este playbook não é essa aprovação. IMP-00 pode produzir inventário/revisão documental, sem scaffold.

Toda execução começa por HEAD + `git status` real, Project Instructions, `.cursor` aplicáveis, README/18/21/23/30 e doc específico, seguida de leitura do source dos producers, consumers, contratos, testes e owner. GitHub connector sem working tree não prova `git status`; classificar `INCONCLUSIVE` quando material. AS-IS e proveniência via TÉO/Transformômetro; TARGET/contratos/código via GitHub.

Authority em conflito: instruções oficiais do GPT Arquiteto → regras `.cursor` → ADR/contract → HEAD → testes → docs vigentes → roadmap. Não presumir que search miss significa ausência. Não alterar owner, framework, permission, persistência, integração ou breaking change por gosto técnico.

## 2. Subetapas de execução E*.S*

| Etapa | Natureza e evidência |
|---|---|
| E0.S1 — baseline | Verificar HEAD/status; regras/documentos/branches; owner atual e mudanças preexistentes |
| E0.S2 — inventory | Inspecionar producer→contract→consumer, API/Portal vigente, Core T05/scope, state e tests |
| E0.S3 — decision/contract | Vincular RQ/AC, opções materiais somente se novas, contrato técnico e teste positive/sibling/negative; stop conditions |
| E1.S1 — minimal diff | Somente após autorização, implementar mudança mínima no owner correto; não scaffold ou migration por antecipação |
| E1.S2 — tests/help | Domain/contract/authz, UI/Help mesma PR, smoke material e casos concorrentes |
| E1.S3 — verify outcome | Validar postcondition real, regression, segurança, residual search e evidence no SHA |
| E1.S4 — review/commit | GPT review, REWORK se necessário; commit/push autorizado, CI no SHA final, next slice |

Antes de cada subetapa perguntar `READY_TO_EXECUTE?` com evidência. Premissa inválida = `EXECUTION_DRIFT`; congelar subgrafo afetado. Nenhum teste pode ser pulado ou enfraquecido para liberar CI.

## 3. Template GPT BRIEF para Cursor

Preencher os campos no HEAD observado. Placeholders são solicitações de inventário, **nunca** fatos provados.

~~~text
TITLE: [IMP-xx / E*.S* / capability]
TASK: [comportamento e limite exatos]
GOAL: [valor e postcondition testáveis]
STATUS: PLANNED / RUNTIME_GATE_NOT_YET_AUTHORIZED

BASE_HEAD: [SHA]
GIT_STATUS: [clean / dirty c/ arquivos / INCONCLUSIVE]
AUTHORITIES: [official GPT, .cursor, ADR, contract, HEAD, testes, docs]
OWNERS: [produto/contexto canônico; producers/consumers]
CURRENT_STATE: [PROVEN com path/SHA; TO_INVENTORY; hipóteses concorrentes]
DECISIONS_LOCKED: [C2/P5-A..J/DEC-01..04 quando aplicáveis]

RQ_AC: [IDs do ledger 23 e outcome de cada um]
SCOPE_ALLOWED: [menor conjunto de arquivos/contratos e owner correto]
SCOPE_FORBIDDEN: [outros contextos, RBAC novo, browser-api-delpi, shortcuts]
CONTRACTS: [request, response, states, errors, idempotency/OCC, versioning]
SECURITY: [JWT identity, Core effective, capability AND resource scope AND rule]
UX_HELP: [plugin-ui, PT-BR, themes, mobile, keyboard, states, Help mesma PR]

DEPENDENCIES: [E/T, inventário e predecessores IMP]
TEST_MATRIX: [positive + sibling + negative; contrato, UX, CI e smoke]
EVIDENCE_REQUIRED: [path, SHA, command, outcome, postcondition]
STOP_CONDITIONS: [unknown owner, drift, missing Core, blocked gate]
COMMIT_POLICY: [somente se autorizado e READY_TO_COMMIT]
OUTPUT: [Execution Report no template 4; nunca inferir PASS]
~~~

### Primeiro brief candidato — A01 Página do usuário (NÃO ATIVO)

**IMP-01** usa [31 — Página do usuário](./31-pagina-do-usuario.md), RQ-USER-01..09, D1=B/D2=A. Perfil self/other autorizado conforme Core; outro usuário não expõe RBAC; Meu Perfil central é a única UI de edição de identidade; foto e perfil são owner Core, sem persistência local. Reusar `createDashboardPortalUserProfilePage` se o export continuar vigente no HEAD; inventariar Core S2S, plugin-ui, BFF e padrão das APIs atuais **antes de scaffold**. Fail-closed quando Core indisponível. Deep route sem item de topbar. Testes self/other, ACCESS/MANAGE, 403/404/503, F5, Help/UX.

## 4. Template CURSOR EXECUTION REPORT

~~~text
EXECUTION_ID: [IMP / E*.S*]
BASE_HEAD: [SHA]
FINAL_HEAD: [SHA]
GIT_STATUS_BEFORE: [evidência]
GIT_STATUS_AFTER: [evidência]
RESULT: [IMPLEMENTED / NO_CHANGE / BLOCKED / EXECUTION_DRIFT]
CLASSIFICATION: [PROVEN / TO_INVENTORY / PLANNED / TARGET, por item]

FACTS_PROVEN:
  - [fato, code path/line, owner, SHA]
TO_INVENTORY:
  - [lacuna, owner, risco, próxima inspeção]
DECISION_REQUIRED:
  - [opções materiais, impacto/recomendação, SEM implementar]
EXECUTION_DRIFT:
  - [premissa invalidada, evidence, chain stopped]

FILES_INSPECTED: [paths]
FILES_CHANGED: [paths/razões]
CONTRACT_IMPACT: [owner, producer/consumer, DTO/OpenAPI, state, version]
SECURITY_CHECKS: [capability, Core, scope, fail-closed e negativos]
RQ_AC_COVERAGE: [ID, positive/sibling/negative com evidência]
TESTS: [comando/ambiente/SHA/resultado ou TEST_NOT_RUN]
CI_GATES: [job URL/SHA/status]
UX_HELP: [screens/states/keyboard/theme/deep-link e Help same PR]
POSTCONDITION_OUTCOME: [valor observável; HTTP 200 não basta]
RESIDUAL_SEARCH: [termos, arquivos, contraexemplos e achados]
UNRESOLVED: [blocking/nonblocking, owner, risk]
COMMIT_SHA: [ou NOT_COMMITTED + razão]
NEXT_STEP: [próximo IMP somente após gate]
~~~

Não declarar `PASS` para smoke não rodado, testes verdes que não cobrem objetivo, UI que apenas esconde operação proibida, nem lógica de owner criada em outro contexto.

## 5. GPT REVIEW obrigatório

O GPT confronta report com USER GOAL, authorities, RQ/AC, HEAD final e todas as dependências:

1. Owner e boundaries corretos? Domain independente, MFE→BFF, no browser→api-delpi, no DB/import vizinho.
2. Permissions só access/manage? Core effective permission e resource scope/ownership/business rule validados fail-closed; TESTES de negação.
3. Feature P5 respeita versão imutável, quorum por área, reatribuição, rejeição formal e C2? P6 publica sem afetar snapshot existente?
4. Todas as RQ/AC têm positive, sibling e negative; testes medem outcome, não só rota/status?
5. UX PT-BR, responsividade, claro/escuro, foco/teclado, Help same PR e link só de rota ativa?
6. CI relevante, integração e smoke materiais realmente executados no SHA atual?
7. Há residual de permission extra, estado stale, bypass, concorrência, duplicação, migration retroativa ou drift de contrato?
8. O diff foi mínimo, preservou terceiros e respeitou a autorização de commit/merge?

Conclusão **somente** `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. Residual de segurança/owner/outcome impede aceite. `ACCEPT_WITH_RESIDUAL` exige owner, risco e ação pendente, nunca falso fechamento de stop material.

## 6. Commit, PR e pós-merge

- Antes de editar: HEAD/status e preservação de trabalho alheio; sem reset, force push, merge/rebase ou overwrite silencioso.
- Branch/PR por owner e capability/slice; commit/push somente quando solicitado e após READY_TO_COMMIT. Testes/Help no mesmo PR.
- Em CHANGE que afeta contract/DB: revisar OpenAPI, migrations imutáveis, consumers, fallback, rollback e testagem.
- Se Gate/CI falha: parar; não modificar expectativa do teste para esconder causa. Falha fora do diff recebe owner separado e evidência, nunca estado global PASS automático.
- Depois do merge: conferir main SHA, CI fresco, source/dto/docs/help, postcondition, smoke e residual search antes de liberar próximo slice.
- Deploy não é decorrência automática de merge: gate próprio em [43](./43-rollout-operacao-e-handoff-v1.md).

**Pacote mínimo de handoff:** brief preenchido, owner/source map, diff, RQ/AC tests, Help, execution report, GPT review, CI e SHAs, residual + próximo step.

A existência do playbook **não** muda `IMPLEMENTATION_AUTHORIZED=NO` ou `TEST_NOT_RUN`.