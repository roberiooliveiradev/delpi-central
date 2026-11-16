# Strategic Indicators — DAVI MCP Full Portal Parity Plan

> Status: PRODUCT_DIRECTION_ACCEPTED / IMPLEMENTATION_PENDING
> Decision: DAVI-ADR-SI-CRUD-001 (Coordination, 2026-11-16)
> Task: DAVI-SI-FULL-PORTAL-PARITY-PLAN-001
> Scope: planejar paridade funcional conversacional do portal de Indicadores Estratégicos no DAVI, sem implementar.
> Evidence: discovery DEVIN DAVI-STRATEGIC-INDICATORS-CRUD-DISCOVERY-01, code inventory; HEAD revalidar em toda task. GitHub code snapshot observado durante planejamento: 0b0bea01c98a78f998dafe6b417834b1c437bf06. Não equivale a deployed SHA.
> Master roadmap: ../davi/01-reestruturacao-strategic-indicators-mcp-semantico.md (plano mestre das waves do DAVI; este documento detalha somente a integração Strategic Indicators, não o substitui).

## 1. Resultado de produto e critérios

Um usuário autenticado deve conseguir conversar com DAVI para executar **todas as funcionalidades disponibilizadas no portal Strategic Indicators para as quais já tenha permissão efetiva**, incluindo leituras, criação, alteração, ativação/desativação, exclusão, operações administrativas, workflows, importação/exportação, jobs e consultas de resultados, conforme contratos e policy do owner. **Paridade funcional é o TARGET, não um claim de runtime atual**. Não converter a exigência em proxy genérico de todas as rotas: cada intenção operacional deve ter capability semântica delimitada e projeção governada.

Acesso ao DAVI nunca implica acesso ao SI. Não criar RBAC DAVI, novas permissões nem exigir permissões diferentes das existentes para a mesma operação. A Core API é autoridade de plataforma e SI API aplica a business AuthZ final. Escopos adicionais de workflow, se necessários por risco de ação conversacional, são controles de confirmação/policy e não um substituto nem expansão de permission codes.

## 2. Decisões congeladas

- Preservar arquitetura `Workspace Agent DAVI -> App/Plugin -> remote MCP api-delpi -> bounded integration -> authoritative SI API -> backend AuthZ -> SI PostgreSQL`; sem outro MCP, banco, backend DAVI, Keycloak client ou rehosting.
- Preservar `END_USER_ACCOUNT`, Authorization Code + PKCE S256, recurso MCP atual e identidade individual. Encaminhar somente JWT end-user ao SI para user-parity; jamais `X-Delpi-Service-Token`/superadmin no caminho conversacional de usuário.
- Padrão de MCPs irmãos (TÉO, VISTA e CAIO/CLARA/EVA/SURI) como **referência de semântica e workflow**, não código copiado automaticamente nem autorização. Surface alvo: `get_context`, `knowledge`, `read`, `analyze`, `execute`, `delete`, registradas somente quando implementadas e testadas. Não criar tool por endpoint.
- `read/analyze/knowledge/get_context` nunca persistem; `execute` para ACT governado, `delete` exclusivo para exclusão destrutiva. PREPARE != ACT; proposal selada e bound à identidade, confirmação explícita verificável, AuthZ revalidada no commit, idempotência/controle de concorrência/audit/postcondition conforme risco.
- Integração entre bounded contexts somente via contratos estáveis HTTP/adapter governado; nunca import de internals de SI, SQL direto nem arbitrarily callable HTTP.
- Não alterar permissões, papéis, owners ou source of truth de Strategic Indicators. Não tratar Dashboard BFF permissions como substitutos de `strategic-indicators.*`.
- Este plano não autoriza deploy, mudança de runtime nem liberação de write.

## 3. Evidência e limitações do inventário

Discovery Devin (source inspection, TEST_NOT_RUN):
- `strategic-indicators-api/si_app` FastAPI, MFE `plugins/strategic-indicators/`, schema `strategic_indicators`, rotas `/strategic-indicators`; inventário reporta cerca de 51 rotas de negócio e 7 integration routes: validar enumeração exata no HEAD.
- SI permissions reportadas: `strategic-indicators.view`, `strategic-indicators.trends.view`, `strategic-indicators.settings.manage` (manifest tem demais permissões; sua aplicação por rota exige inventário).
- DAVI MCP: quatro tools registradas em `api-delpi/app/interface/mcp/server.py`: `get_context`, `knowledge`, `read`, `analyze`. `execute/delete` planejadas, não implementadas.
- Atual DAVI catalog/index = api-delpi OpenAPI, allowlist v30 e executor ASGI READ-only; SI API não integra diretamente o executor. Dashboard SI BFF existente usa dashboard permissions e service principal, portanto NÃO satisfaz user parity do SI.
- `X-Delpi-Service-Token` do client SI atual pode produzir superadmin; proibido para fluxos DAVI user-parity.
- Goals `monthly_curve` possui targets mensais autoritativos; não reduzir a meta anual a um valor derivado ou média sintética. Há commit recente `0b0bea01c98a78f998dafe6b417834b1c437bf06` tratando rollup de curvas mensais: revalidar implementação e contratos antes de testes.
- Delete de meta reportado como HARD no código, divergindo da documentação que diz soft. Atualizações de meta sem OCC precondition; idempotency keys e auditoria por mutação de metas não comprovadas.
- Testes de integração cross-user, provider discovery e deployed SHA: PENDING/STALE_EVIDENCE. Sem inferir production readiness a partir de código.

## 4. Matriz de paridade portal -> capabilities (TARGET)

Cada linha exige inventário do fluxo real no MFE, owner use case, route/schema, permission, side effects, business postcondition e status de implementação. **Não significa adicionar uma tool por linha.**

| Área do portal | Intenções para DAVI | Classe | Backend/permission a validar |
|---|---|---|---|
| Visão executiva | consultar resumo, pontuação e filtros de competência/filial | READ / ANALYZE | `view`, snapshots |
| Departamentos / árvore | listar, detalhar, navegar, tendências, snapshot | READ | `view` / `trends.view` |
| Indicadores | consultar catálogo, valores realizado/meta, metadados e séries | READ / ANALYZE | `view`; fonte/provider vs derivado |
| Alertas / apresentação | consultar alertas e visualizações | READ | permissão efetiva na rota |
| Metas | listar, histórico, criar, editar, ativar, desativar, excluir | READ / PREPARE / ACT / DELETE | `settings.manage`, scope/year/version |
| Curvas mensais | consultar e alterar targets mensais por competência, filial e periodicidade | READ / PREPARE / ACT | `indicator_goals`, `indicator_goal_monthly_targets` |
| Administração de departamentos | cadastrar, editar, ativar, desativar, excluir | READ / PREPARE / ACT / DELETE | `settings.manage` |
| Administração de indicadores | cadastrar, editar, ativar, desativar, excluir, pesos/aggregation | READ / PREPARE / ACT / DELETE | `settings.manage` |
| Configurações | consultar/editar settings, auditoria | READ / PREPARE / ACT | `settings.manage` |
| Solicitações de alteração | criar, comentar, submeter, consultar histórico/status | READ / PREPARE / ACT | `settings.manage` e workflow real |
| Importar/exportar configuração | exportar, preview, aplicar/importar | READ / PREPARE / ACT | `settings.manage`; diff/atomicidade |
| Operações em lote | criar metas, duplicar ano, preencher faltantes | PREPARE / ACT | `settings.manage`; limites/custo |
| Cache/snapshots/jobs | consultar status, disparar refresh/invalidate/load job | READ / ACT | `view` ou `settings.manage`; side effects |

Realizados vêm de fontes autoritativas (TOTVS, Sheets, RH etc.) e não são registros de edição direta no SI: a paridade é executar o mesmo que o portal suporta, não criar uma escrita artificial de realizado. Permissões e funcionalidades do frontend são hipótese de mapeamento até validação rota-a-rota.

## 5. Contrato de capability e execução

`get_context` descobre intenções elegíveis e schemas sem autorizar. `read` retorna projeções tipadas, limitadas, com unidade/competência, completude e proveniência. `analyze` compõe resultados sem persistir nem recalcular regras canônicas por conta própria. `knowledge` descreve metodologia versionada sem ser fonte operacional.

`execute` expõe intenções ACT aprovadas, e não verbos HTTP. Fluxo padrão para ação material:
1. Receber intenção + payload tipado mínimo; validar business owner, escopo, usuário e policy.
2. PREPARE server-side: calcular diff/impacto, checar versão/estado, montar proposta selada vinculada a ator, alvo, digest, prazo e operation ID; não persistir mudança de negócio.
3. Exibir resumo humano exato, efeitos e escopo; confirmação explícita.
4. ACT: verificar mesma proposta, identidade e prazo, revalidar AuthZ efetiva e estado/version, aplicar via API SI com end-user JWT e idempotency/OCC onde pertinente.
5. Reconsultar owner authoritative postcondition, registrar audit/correlation e devolver resultado tipado. 2xx sozinho não prova sucesso.

`delete`: proposal separada e confirmação explícita para HARD DELETE; incluir dependências/cascata, irreversibilidade, preview de registros impactados, conflitos e auditoria. Nunca fazer soft delete quando owner executa hard delete. Se owner não oferece controles necessários, capability fica bloqueada até fechamento da lacuna.

Serviço de proposta somente se necessário a boundary/consumer real, seguindo Abstraction Gate; preferir padrão irmão comprovado, sem duplicar autorização nem persistir secrets. Não copiar mecanicamente implementação de TÉO/VISTA.

## 6. Gates de segurança e contrato

- Identity: usuário Keycloak end-user, JWT validado pelo SI (issuer, signature, audience), principal de usuário verificado; cross-service forwarding sem service token superadmin.
- AuthZ: Core app permission conforme mecanismo vigente + enforcement final no SI em cada READ, PREPARE e ACT; deny para usuário DAVI sem SI access; negative matrix por permissão e ator.
- Proteção de dados: output allowlist/field redaction, paginação/budgets, tratamento de erros sem detalhes internos, nenhum token/log sensível.
- Writes: confirmar semântica HTTP e negócio por operação, idempotency key/replay protection, OCC/If-Match ou mecanismo equivalente, transações, auditoria, revalidação de RBAC e pós-condição. Controlar cache RBAC stale (reportado 60s/900s) em decisões sensíveis.
- Policies: mass writes, config import, cascade delete, refresh job e ações irreversíveis requerem aprovação específica de risco.
- Anti-patterns: no generic SQL/HTTP, endpoint=tool, service-principal impersonation, prompt-only ACL, dashboard permission substitution, silent writes, writable `read`.
- Conflicts: owner/source/AuthZ/identity changes ou nontrivial abstraction voltam à Architecture / Coordination.

## 7. Sequência executável, sem reduzir escopo de produto

**Wave SI-0 — Rebaseline/coverage freeze (READ-ONLY):** inventariar todas as telas, botões e ações do MFE, rotas SI, payloads/erros/permissions, identificar gaps do report Devin, confirmar readiness de tokens e semantics; checklist total de portal parity rastreável; no implementation.

**Wave SI-1 — READ user parity:** cross-API bounded adapter, SI JWT user-only, published owner endpoints e allowlists, `read` + `get_context`, testes negativos de acesso SI; sem usar Dashboard BFF como bypass.

**Wave SI-2 — PREPARE/execute foundation:** padrão irmãos avaliado (TÉO/VISTA; também CAIO/EVA), registrar `execute` somente após capability ACT real; introduzir proposal/diff/confirm/idempotency/OCC/audit/postcondition com menor diff; começar metas (create/update/activate/deactivate) e curva mensal.

**Wave SI-3 — Admin parity:** departamentos, indicadores, configurações, change requests, bulk, import preview/apply, jobs/cache; cada intenção por use case canônico, mesmo `execute` sem tools extras.

**Wave SI-4 — Destructive delete:** registrar `delete` quando política e testes de hard delete/cascade, audit, confirmation, replay e recovery estiverem aprovados; goals/departments/indicators separadamente.

**Wave SI-5 — End-to-end acceptance & rollout:** matriz portal x DAVI com positive/negative user AuthZ, provider discovery, Agent private preview, performance, rate policy, deploy SHA, rollback, documentação, compartilhamento governado; aceites separados por capability. Não chamar completo até todas as ações portal inventariadas terem teste ou bloqueio explícito.

Waves são gates de implementação, **não redução do TARGET de CRUD e demais funcionalidades do portal**. Pode dividir cada wave em menores diffs.

## 8. Critérios de aceite de paridade

AC-01 catálogo completo MFE action -> SI route -> owner use case -> business permission -> DAVI semantic intent -> status/evidence.
AC-02 operação que o usuário não pode executar no SI também não pode via DAVI, inclusive knowledge protegida, preview, análise e writes.
AC-03 zero uso de service token superadmin em user-parity SI.
AC-04 `read` é read-only e `execute/delete` com confirmação governada; nenhuma tool por rota.
AC-05 todas as operações de criação, alteração, exclusão, ativação/desativação, bulk/import, workflow e jobs incluídas na matriz, com requisitos de segurança e pós-condição explícitos.
AC-06 CURVE: metas mensais preservadas por competência/filial/periodicidade, sem derivação incorreta da curva.
AC-07 audit, idempotency, OCC, revalidation RBAC, 401/403/503, replay, conflict e destructive policy testados por operação.
AC-08 sem regressão das consultas existentes DAVI, MCP OAuth, catálogo e demais consumers SI.
AC-09 deployment SHA e provider discovery reais, testes live positivos/negativos em ao menos duas identidades.
AC-10 qualquer ação do portal não implementada é explicitamente GAP (não declarar FULL PARITY).

## 9. Evidence/report e governança

Para cada wave: `git fetch`, HEAD/origin/main/status, authorities, RQ/AC, contratos e consumers, min diff, testes, residual search, documentação, SHA commit/push, deployed SHA quando houver, MCP tools/list, provider discovery, live positive/negative AuthZ e postcondition ACT. Classificar fatos `PROVEN | TO_INVENTORY | PLANNED | TARGET`, execução `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`, invalid premise `EXECUTION_DRIFT`. Aprovador: DAVI — Architecture / Coordination.

## 10. Próximo bounded brief (não iniciar implementação sem Coordination)

`DAVI-SI-PORTAL-PARITY-MATRIX-001`: READ-ONLY. Revalidar main e working tree, percorrer todos os fluxos MFE e controllers SI, registrar matriz exaustiva de paridade e dependências/safety das operações ACT, confirmar políticas de identidade, identificar primeiro menor diff cross-API. Não implementar, não deploy, não realizar writes. Retornar relatório com gaps, precedências e aceites. Após aprovação, iniciar SI-1 e SI-2 em waves delimitadas.

