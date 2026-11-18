# Strategic Indicators — DAVI MCP Full Portal Parity Plan

> Status atual (2026-11-18): **IMPLEMENTED / W016_DEV_FULL_PARITY_ACCEPTED / PRODUCTION_DEPLOYED_WITH_RESIDUALS / DELIVERY_CLOSED_BY_COORDINATION**. Evidência: W016 `4ebe5816e7`, fechamento `c13c36e22c`, matriz `03-w016-portal-parity-matrix.md`; deploy da V037 reportado e discovery autenticado das seis ferramentas verificado no ChatGPT. Este status substitui o cabeçalho histórico de planejamento para fins de execução; seções históricas permanecem como trilha de decisão.
> Decision: DAVI-ADR-SI-CRUD-001 (Coordination, 2026-11-16)
> Task: DAVI-SI-FULL-PORTAL-PARITY-PLAN-001
> Scope: planejar paridade funcional conversacional do portal de Indicadores Estratégicos no DAVI, sem implementar.
> Evidence: discovery DEVIN DAVI-STRATEGIC-INDICATORS-CRUD-DISCOVERY-01, code inventory; HEAD revalidar em toda task. GitHub code snapshot observado durante planejamento: 0b0bea01c98a78f998dafe6b417834b1c437bf06. Não equivale a deployed SHA.
> Master roadmap: ../davi/01-reestruturacao-strategic-indicators-mcp-semantico.md (plano mestre das waves do DAVI; este documento detalha somente a integração Strategic Indicators, não o substitui).


## Encerramento de entrega — Coordination, 2026-11-18

**Decisão:** encerrar por ora as entregas de paridade DAVI × Strategic Indicators como **implementadas**, com aceite funcional integral em DEV e deploy produtivo reportado e verificado por smoke não mutante. Novas waves dependem de nova demanda.

- **Escopo:** 50/50 ações elegíveis de portal cobertas no inventário W016; 1 rota genérica legada de importação intencionalmente bloqueada por design. Seis tools semânticas: `get_context`, `knowledge`, `read`, `analyze`, `execute`, `delete`.
- **Evidência DEV:** PostgreSQL + OAuth + MCP reais, três identidades de teste, operações de escrita e exclusão em fixtures, PREPARE/ACT, cascatas, import merge/replace, auditoria e concorrência. Reconciliação V034 e V037; suíte aplicável SI 378/378 e DAVI 132/132, total **510 PASS, 0 FAIL/ERROR**, gates arquiteturais sem findings; verificador r3 **ACCEPT_WITH_RESIDUAL**, zero ordens abertas.
- **Produção:** executor reportou deploy dos serviços `delpi-strategic-indicators-api` e `delpi-api-delpi`, migração V037 aplicada e smoke não mutante PASS. Ferramenta `delete` foi descoberta e invocada no ChatGPT com negativas seguras; **ACT destrutivo em produção não executado**, por decisão da Coordination. Não extrapolar resultado DEV para writes produtivos.
- **Resíduos não bloqueantes do aceite delimitado:** 17 skips reportados na suíte ampla, 40 falhas ambientais fora do escopo aplicável (necessitam acompanhamento próprio); testes negativos com segunda identidade provados em DEV, não em ChatGPT produtivo; aceites produtivos por capacidade/ACT não executados integralmente. Tratar resíduos como backlog de operação/governança, não como novas implementações já aprovadas.
- **Autoridade:** owner SI continua source of truth e AuthZ final; DAVI não concede permissões. Encerramento documental não altera regras de negócio nem autoriza mutações produtivas.

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
- DAVI MCP: seis tools registradas em `api-delpi/app/interface/mcp/server.py`: `get_context`, `knowledge`, `read`, `analyze`, `execute`, `delete` (W012–W015 implementadas).
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

**Wave SI-4 — Destructive delete:** ✅ **IMPLEMENTADA (W015)** — tool `delete` registrada; `si.goal.delete`, `si.indicator.delete`, `si.department.delete` (hard delete com OCC atômico + dependent guards + audit) e `si.config.import_replace` (via `execute`, recovery artifact selado); política destrutiva e testes aprovados no contrato §11 do inventário.

**Wave SI-5 — End-to-end acceptance & rollout:** matriz portal x DAVI com positive/negative user AuthZ, provider discovery, Agent private preview, performance, rate policy, deploy SHA, rollback, documentação, compartilhamento governado; aceites separados por capability. Não chamar completo até todas as ações portal inventariadas terem teste ou bloqueio explícito.

**W016 — DEV full parity validation:** ✅ **HOMOLOGADA EM DEV** — 50/50 ações elegíveis exercidas via MCP real (OAuth + 3 identidades reais: full/view-only/zero-SI), 6 tools validadas, 27 governed caps PREPARE→ACT→read-back, deletes com cascata, import merge+replace+restore, OCC/replay/AuthZ negativos. Correções aplicadas: V037 (audit event types admin), `import_replace` flat body + digest canônico + verify de module_settings. Detalhes: `04-w016-dev-parity-closure-report.md` e matriz §10. **Produção:** deploy executado (V037 + fixes) com smoke não-mutante PASS — 6 tools servidas, OAuth/RFC9728 íntegro, zero mutação de negócio. Discovery ChatGPT de `delete` aceito (sessão autenticada); ACTs destrutivos produtivos não executados por decisão.

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


## 11. Atualização de Coordination — 2026-11-16: W010 em produção e validação conversacional

**Decision:** `DAVI-SI-W010-CHATGPT-READ-ACCEPT-01` — aceite da **validação READ positiva no ChatGPT**, não do CRUD completo. Evidência runtime foi obtida pela conexão DAVI MCP autenticada neste chat; o SHA de deploy continua evidência reportada pelo executor, distinta da validação do ChatGPT.

**Persistência e deploy (execution report):**
- Merge reportado: `76449a73bb152a23cfbbd37fe203dadbf18e5574`; deployed checkout reportado: `4018a7d58c` (merge ancestor, segundo relatório). Rollback reportado: `a8304d4483`.
- Executor reportou dev-live: duas identidades com resultados distintos, 200 autorizado e 403 sem SI permissions; 401 JWT inválido; não confundir com teste negativo de segunda identidade **no ChatGPT**.
- Limites: não reproduzimos aqui check de deployed SHA, e `tools/list` raw não foi realizado pelo executor com sessão OAuth. A invocação MCP autenticada deste chat é evidência adicional do provider path.

**Prova ChatGPT neste chat, conexão DAVI end-user, catálogo v31:**
- `get_context(action=context)`: usuário autenticado, exatamente 4 tools (`get_context`, `knowledge`, `read`, `analyze`); `execute/delete` = `PLANNED_NOT_IMPLEMENTED`.
- `get_context(action=catalog)`: `catalog_version=31`, `eligible_action_count=102`, contendo os cinco SI action_ids.
- `get_context(action=schema)`: `get_si_executive_summary`, `list_si_indicator_goals` e `list_si_indicator_goal_history` retornaram schemas limitados.
- `read(get_si_executive_summary,{})`: `status=ok`; competência `2026-11`, IGD `6.82`, departments com dados efetivos.
- `read(get_si_departments,{department_id:"commercial"})`: `status=ok`, depto Comercial score `8.71`.
- `read(get_si_indicators,{department_id:"commercial"})`: `status=ok`, seis indicadores, incluindo ROL, seus valores e metas.
- `read(list_si_indicator_goals,{goal_year:2026,department_id:"commercial",active_only:true})`: `status=ok`; curvas mensais por filial 01/02, versionadas.
- `read(list_si_indicator_goal_history,{indicator_id:"commercial-rol",goal_year:2026})`: `status=ok`; registros de metas 01 e 02.
- Nenhum write executado na validação; dados retornados não são autorização de negócio para futuras operações.

**Gates:**

| Gate | Classificação | Evidência/limite |
|---|---|---|
| W010 merge/deploy | PASS reportado | SHA do executor; deployed SHA não independente neste chat |
| Autenticação e catálogo ChatGPT | PASS | get_context, catalog v31, 102 elegíveis |
| SI READ positiva via ChatGPT | PASS | cinco capabilities, status=ok |
| SI READ cross-user negative em dev | PASS reportado | duas identidades no relatório de execução |
| Segunda identidade negativa no ChatGPT/prod | PENDING | não executada nesta sessão |
| PREPARE, ACT, DELETE | PLANNED / TEST_NOT_RUN | nenhuma tool de escrita implementada |

**Decision:** prosseguir ao **gate SI-2 de design/contract-first**, mantendo `read` e arquitetura existentes, **sem habilitar writes ainda**. Paridade completa com o portal segue TARGET.

## 12. Próximo briefing bounded — W011 / contratos e segurança para PREPARE→ACT

`TASK_ID: DAVI-SI-W011-GOAL-WRITES-CONTRACT-AND-SAFETY-01`

`MODE: READ_ONLY_INVENTORY / CONTRACT_SPEC / NO_CODE / NO_DEPLOY / NO_WRITE`

1. Revalidar origin/main/HEAD/status, `.cursor`, README DAVI, plano mestre, SI API/owner contracts e todos os consumidores do MFE. Identificar owner, source, use case e AuthZ para create/update/activate/deactivate de metas/curvas por ano e filial; confirmar o que o portal realmente permite.
2. Comparar contratos MCP de TÉO e VISTA (e outros irmãos) para `execute`/proposal selada, confirmação, idempotência, concorrência, auditoria e authoritative postcondition; adotar princípios, não copiar internals cross-context.
3. Matriz por operação: intenção, entrada mínima (incl. `monthly_targets`), saída allowlisted, target ID/version, efeitos colaterais, permission `strategic-indicators.settings.manage`, classificação `PREPARE|ACT`, erros, limites, consumer e provenance.
4. Definir mecanismo seguro de principal end-user: JWT-only no hop SI, jamais `X-Delpi-Service-Token`; SI revalida AuthZ em PREPARE e ACT; avaliar stale RBAC e write risks. Não criar nova permissão DAVI.
5. Especificar proposal selada server-side vinculada a ator, scope, payload hash, versão, validade e confirmação explícita; idempotência/replay; OCC ou alternativa owner-canonical; auditar actor/diff/correlation; pós-condição lida novamente na API SI. Marcar gaps reais: SI goal update sem OCC precondition, ausências de idempotency key e auditoria individual reportadas.
6. Não incluir `delete` destrutivo nesta primeira execução; inventariar hard-delete e cascata para gate separado. Não converter `read` em write; preservar `get_context/knowledge/read/analyze`; `execute` só será registrado em implementação futura após approval de contrato.
7. Preparar golden conversational scenarios: criar meta 2027 por filial, atualizar apenas um ponto mensal, ativar/desativar com versões, repetir commit, mudança concorrente, token revogado, usuário sem settings.manage, usuário sem SI app access. **Sem executar writes**.
8. Devolver `Capability Decision` + `DAVI EXECUTION BRIEF` mínimo para W012 (implementação) com Abstraction Gate, RQ/AC, arquivos prováveis, testes e STOP conditions.

**Acceptance W011:** cobertura completa dos contratos das operações escolhidas; paridade de permissões provada em código; matriz de risks/OCC/idempotency/audit fechada ou marcada TO_INVENTORY; sem novas ferramentas/serviços/código e sem execução de writes. Se conflitos de owner/AuthZ/identity, STOP e `ARCHITECTURE_DECISION_REQUIRED`. O restante do CRUD do portal continua no roadmap SI-3/SI-4.
