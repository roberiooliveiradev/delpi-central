# 41 — Estratégia de Validação, Matriz de Testes e Gates V1

**Estado:** TARGET / PLANNED / TEST_NOT_RUN. Este arquivo é uma especificação de testes futuros, **não** relata execução. `DOCUMENTATION_CLOSURE_COMPLETE=NO` e `IMPLEMENTATION_AUTHORIZED=NO` permanecem.

Fontes: [.cursor — platform-quality-testing](../../../.cursor/rules/platform-quality-testing.mdc), [test-and-commit](../../../.cursor/rules/test-and-commit.mdc), [feature-help-sync](../../../.cursor/rules/feature-help-sync.mdc), [15 — requisitos](./15-requisitos-criterios-de-aceite-e-testes.md), [23 — ledger](./23-ledger-rq-ac-testes.md), [35 — A15](./35-contratos-regras-scripts-test-matrix-gate-v2.md), [38 — evidências](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md).

## 1. Gates de validação obrigatórios

| Gate | Momento | Entrada e saída exigidas |
|---|---|---|
| G0 / A16 | Antes de qualquer runtime | A12/A14/A15 e A16 revalidados, quatro freezes sustentados e autorização explícita posterior do PO; caso contrário STOP |
| G1 / READY_TO_EXECUTE | Antes de cada IMP | HEAD + git status, authorities/.cursor aplicável, RQ/AC, owner, consumer/producer, scope e stop conditions verificados |
| G2 / VALIDATE | Durante o slice | Prova de comportamento positive, sibling, negative, contratos, segurança, estados e experiência; postcondition e evidência no SHA |
| G3 / READY_TO_COMMIT | Antes de PR/commit autorizado | Diff mínimo, Help no mesmo slice, testes/CI relevantes, sem enfraquecimento de gate, residual search |
| G4 / VERIFY_FINAL | No SHA pós-diff | Reexecutar provas afetadas pela mudança; smoke relevante não rodado = INCONCLUSIVE |
| G5 / RELEASE | No ambiente alvo, se autorizado | Feature availability, configuração, observabilidade, rollback, smoke, operação e autorização separada |

Fatos: `PROVEN | TO_INVENTORY | PLANNED | TARGET`. Evidência: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`. Se descoberta contradiz premissa necessária, `EXECUTION_DRIFT` e STOP-THE-LINE. Conclusões GPT: `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

PASS nunca é inferido de rota, HTTP 200, documentação, merge, build ou teste isolado. É necessário provar o outcome e a AuthZ da ação.

## 2. Camadas de teste por owner

| Camada | Matriz mínima |
|---|---|
| Domain/application próprios | Sem dependência de framework/DB/HTTP; estados/transições, quórum, versionamento, concorrência/idempotência, invariantes e contraexemplos com ports fake |
| Integration/contract | DTO/OpenAPI/evento, compatibilidade, producer/consumer, Core permission/roster/notifications, api-delpi/TOTVS e strategic indicators, erros e freshness |
| HTTP/BFF/AuthZ | JWT validado + Core effective permissions AND resource scope/ownership AND business rule; 401/403/404/409/503, fail-closed, nenhum segredo |
| MFE/component | Reuso do plugin-ui, mesma árvore claro/escuro, CSS root, keyboard/foco, desktop/mobile, states, deep link/F5, rota/nav protegidas |
| E2E/smoke | Usuário autorizado e não autorizado, integrações reais quando materiais, postcondition e leitura posterior, erros degradados honestos |
| Delivery | CI aplicável, script de build, migrations/reversão se stateful, health/observability/release/rollback se houver deploy |

Por comportamento: ao menos **positive + sibling + negative**; sem sibling lógico, justificar explicitamente. Simulações não substituem owner real ou live smoke material.

## 3. Matriz por slice (seleção; RQs completos no ledger 23)

| Slice | Positive | Sibling / isolamento | Negative / limite |
|---|---|---|---|
| IMP-01 Página do usuário | self/other autorizado, Core identity/foto e D1/D2 | mudança de outro perfil não altera o viewer | MANAGE sem ACCESS, RBAC alheio oculto, Core/foto indisponível |
| IMP-02 Início | hero, catálogo de rotas ativas, eventos, recentes/favoritos | falha em eventos não derruba catálogo | futuro não aparece, favorito stale sem persistência provada, link fora de scope |
| IMP-03 Visão geral | KPI owner/source/formula/freshness, filtros/deep link | falha de um source preserva outros | zero inventado, O05 fórmula incorreta, unidade fora de scope |
| IMP-04 Minhas tarefas | TaskProjection self-only, filtros e link ao owner | owner resolve obrigação e projeção converge; outros producers independentes | TaskEntity local, SLA global, user selector, deep link unauthorized |
| IMP-05 Sala | room contextual, mensagens e mention segura | contextos independentes, realtime degradável | comentário não muda business state, attachment não é P2 evidence, criação de task proibida |
| IMP-06 Administração | MANAGE+escopo, revisão, publish, inativação com audit | snapshot antigo permanece intacto | ACCESS-only, stale revision, hard delete, write de usuário/role local |
| IMP-07 Ajuda | manual do kit, rotas/features já ativas e FAQ | viewer MANAGE tem seção autorizada distinta de ACCESS | conteúdo de feature futura, hash/link inseguro, Help desatualizada |
| IMP-08 P1 | cockpit agrega eixos, fontes e blockers reais | documento pronto não fecha estoque nem pacote | source 503 não vira zero/sucesso; recurso irmão protegido |
| IMP-09 P2 | requirement, attachment, validation, replacement com histórico | sibling item mantém estado independente | upload != ACCEPTED, validator sem elegibilidade, catálogo retroativo |
| IMP-10 P3 | cutoff, dados ERP autorizados e paridade exata R$ 0,00 | outro período/filial não herda `STOCK_CLOSED` | diferença R$ 0,01 bloqueia; falha de T03; nunca escrita ERP própria |
| IMP-11 P4 | pendência/classificação usa owner e audit | outro centro custo/item não é afetado | heuristic local vira regra canônica, scope indevido |
| IMP-12 P5 | Finalizar congela PackageVersion; submit in-portal; aceite 1/área atual; completion C2 | reviewers da mesma área, outro destinatário, nova versão e reatribuição preservam isolamento | ACCESS sem função/scope, MANAGE-only, Core down, retorno 200 sem negócio, rejeição de área sem confirmação não terminal, retificação V1 inexistente |
| IMP-13 P6 | publish versionado por tipo de pacote, MANAGE+scope, audit | publicação futura não altera snapshot P2/P5 | ACCESS-only, stale OCC, exclusão retroativa, catalog free-form |
| IMP-INT | processo de competência reproduzido com owners e estados reais | duas competências, dois recipients, duas versões e usuários distintos | falhas Core/api-delpi/notificação/realtime não criam falso fechamento |

**Experiência em todas as páginas:** LOADING, EMPTY, PARTIAL, UNAVAILABLE, ERROR, FORBIDDEN/403, NOT_FOUND/404 quando aplicáveis; F5 e filtros na URL; desktop/mobile, claro/escuro, teclado/foco e copy PT-BR; Help contextual atualizada **na mesma PR**. Se não aplicável, registrar rationale.

## 4. Suite transversal de segurança

1. Testar JWT com issuer/audience/assinatura/exp reais e falha de configuração; JWT não é fonte de effective permissions.
2. Core ACCESS e MANAGE independentes; só códigos `controllership-finance.access` / `controllership-finance.manage`. Unidade/filial é escopo de dado, não permission.
3. Recurso sibling: outra competência, destinatário, pacote, área, usuário; negar leak de dados pela BFF e deep link, independentemente do menu.
4. P5 reviewer: ACCESS efetivo **AND** grupo/função elegível **AND** área congelada **AND** scope/ownership **AND** business rule; erro de Core ou mapeamento desconhecido falha fechado.
5. P5 terminal DEC-01/02: coordenador formal com ACCESS+vínculo+scope confirma com reason; rejeição de área sozinha não é terminal; negativa motivada deixa pendente.
6. P5-E/F/G/J: nova versão reinicia quorum; substituto não se apropria da autoria; nenhum endpoint/UI de reversão; rejeição terminal torna tarefas não acionáveis preservando audit.
7. P6 DEC-04: MANAGE efetivo **AND** escopo administrativo, publish com reason e OCC; published/snapshot anteriores imutáveis.
8. Fronteiras: MFE usa apenas BFF, não api-delpi direto; BFF não importa domínio do vizinho nem acessa seu banco; sem secrets em frontend/logs.

## 5. Submatriz P5 de alto risco

| Contrato | Requisito no ledger 23 | Casos obrigatórios |
|---|---|---|
| Finalização e versões | P5-02/03/04/09, P5-AREA-02 | Finalizar != Enviar; immutable; nova versão exige aceites novos; destinatário sibling independente |
| Quorum por área e elegibilidade | P5-06/12, P5-AREA-01/04 | Um aceite por área, dois reviewers mesma área, área ausente bloqueia, falha Core, concurrent accept |
| Autoria e não reversão | P5-AREA-03, P5-TERM-03 | Reatribuição preserva aceite e ator; substituto só ações futuras; rectification V1 inexistente |
| Rejeição terminal | P5-TERM-01/02, DEC-01/02 | Reviewer REJECTED ≠ competence terminal; coordenador confirma; recusa mantém pending; projeções desativadas no terminal |
| Notificações/tarefas | P5-07/08 | Notification/email failure não faz rollback de business state; projection self-only; owner deep link |
| Conclusão C2 | P5-12 | Todos recipients submetidos, todas áreas da versão atual aceitaram, nenhuma clarification aberta, competência não rejeitada: uma negativa isolada por conjunção |

Os scripts `validate-p5-*` citados em docs anteriores são **PLANNED**, não presumir arquivo ou teste real antes de inventariar HEAD.

## 6. Registro de evidência por slice

| Campo | Evidência mínima |
|---|---|
| BASE_HEAD / FINAL_HEAD / STATUS | SHA, branch, git status antes/depois; working tree indeterminada = INCONCLUSIVE |
| OWNER / SOURCE / CONTRACT | links do producer/consumer, código, DTO/OpenAPI, scopes, RQ/AC com versão |
| TESTS | positivos/sibling/negativos, comandos, logs, resultados, timestamp, SHA, smoke ou sua ausência |
| UX / HELP | rota/estado, screenshot ou inspeção quando material, foco/tema/mobile, Help no mesmo diff |
| CI | jobs específicos e transversais aplicáveis; não dizer CI global verde por amostra |
| SECURITY | permission + resource scope + business rule e contraexemplos executados |
| RESIDUAL SEARCH | permissões extras, duplicação de owner, API direta, estados antigos, links futuros, docs divergentes |
| OUTCOME / CONCLUSION | postcondition real, `ACCEPT / ACCEPT_WITH_RESIDUAL / REWORK / EXECUTION_DRIFT / INCONCLUSIVE` e próximo step |

**Gates de teste não podem ser enfraquecidos** por update de expected, skip, default permissivo ou override. Mudanças depois dos testes requerem retestar dimensões afetadas. Falha externa ao diff: registrar owner e causa, nunca classificar globalmente como PASS.

## 7. Definition of Done e release

Uma entrega só recebe `ACCEPT` quando RQ/AC e outcome realmente provados, security/UX/Help em conformidade, contratos sem breaking não aprovado, evidência no SHA e smoke executado quando material. `ACCEPT_WITH_RESIDUAL` é apenas para resíduos não bloqueantes documentados com owner. Release exige o gate separado em [43](./43-rollout-operacao-e-handoff-v1.md).

**No momento:** todos os testes de Portal planejados aqui = `TEST_NOT_RUN` e todos os slices runtime = `NOT_STARTED`; a existência desta matriz não altera `IMPLEMENTATION_AUTHORIZED=NO`.