# Documento 119 — CLARA MCP Semântico · Plano mestre executável, migração, testes e deploy
**ID:** CLARA-MCP-SEMANTIC-001 · **Estado:** TARGET / EXECUTION_AUTHORIZED_BY_PO (código e deploy autorizados, condicionados aos gates técnicos)  
**Owner:** controllership-finance-api / Portal Controladoria & Finanças  
**Baseline observado:** origin/main `2a4307efe969afae6648fca7e36652efb698db02` em 29/10/2026; EXECUTOR DEVE REBASELINE.  
**Escopo:** reformular a superfície MCP da CLARA em seis ferramentas semânticas, preservar capacidades e integridade operacional e promover à produção via SSH `operador` após gates.  
**Não autoriza:** novas permissions, import de internals de outros contexts, mudanças financeiras canônicas, infra genérica, supressão de controles de alto risco, deploy de SHAs não revisados, migrações destrutivas.

## 0. Decisão do PO — fechada nesta task
O PO aprova a refatoração integral, documentação, testes, rework local, commit, deploy governado e relatório em **uma execução encadeada**. Não voltar ao PO para preferências de implementação já cobertas por este plano. Resolver escolhas técnicas locais pela authority do repo e menor diff.

Comportamento desejado:
| Intenção | Comportamento |
|---|---|
| Consultar / analisar / conhecimento | Executar imediatamente, dentro do acesso |
| Criar / atualizar | Executar diretamente se operação de baixo/médio risco, explícita, autorizada e contrato permitir |
| Várias operações | Planejar dependências e executar as permitidas na mesma solicitação, informando parcialidade |
| Excluir / cancelar com impacto destrutivo | Exigir confirmação humana explícita, vinculada e verificável |
| Operação bloqueada | Explicar motivo, não executar, não fazer bypass |
| Finalização oficial, publicação, rejeição terminal, mudanças de catálogo/template ou outra ação de alto impacto | Preservar PREPARE→consentimento independente→ACT, mesmo sob `execute` |

**Limite de autorização:** a autorização do PO não se substitui à confirmação do usuário final para ações específicas nem à effective permission do Core. Um `confirmed=true` vindo do LLM não é consentimento verificável. Se autoridade superior impuser confirmação para uma operação de risco baixo, preservar até mudança de contrato autorizada. Não classificar uma ACT como baixo risco apenas para contornar gate.

## 1. Authority e baseline (G0)
1. `git fetch`, registrar HEAD, origin/main, branch, `git status`, alterações alheias, SHA e produção atual.
2. Ler instruções oficiais `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`, Project Instructions, .cursor aplicável, ADRs, segurança, `docs/12-roadmap-e-evolucao/controllership-finance/README.md` e doc 118 (base canônica PROC-0072); documentos 94, 113 e 14 conforme aplicável.
3. Inspecionar `controllership_finance_app/interface/mcp/{server.py,tool_bridge.py,constants.py,branding.py,oauth_contract.py}`, camada application, BFF routes/use cases, `ClaraGovernedWrites`, `ClaraBatchOrchestrator`, proposals/consentimento, testes de wire, tools, AuthZ e consumers.
4. Inventariar contratos atuais dos MCPs TÉO, VISTA, DAVI e o plano EVA 54 apenas como referência; não importar código nem assumir que os planos TARGET são runtime.
5. Localizar deployment runbook oficial, `operador`, rollback e processo de atualização do plugin do ChatGPT. Não presumir paths, nomes de containers ou hosts.
6. Registre inventário machine-readable da superfície MCP REAL (`tools/list`) versus catálogo (`get_catalog`) e 48 governed operations (números podem ter mudado). Não deduzir compatibilidade só por contagem.
7. Mapear consumidor por tool: ChatGPT plugin, testes, GPT Actions, outras integrações registradas e eventuais clients externos; search miss != ausência. Capturar usage/telemetria disponível ou marcar INCONCLUSIVE.

## 2. Contrato TARGET: seis tools, funções estáveis
Taxonomia `shared/delpi_mcp` permanece DISCOVERY/READ/ANALYSIS/PREPARE/ACT; annotations honestas e esquemas de segurança preservados. A superfície PUBLIC FINAL do `tools/list` é exatamente:
| Tool | Classe | Interface semântica | Efeito |
|---|---|---|---|
| `get_context` | DISCOVERY | `{topic?, entity?, action?, scope?, selected_ref?}` | Contexto do ator, persona/AVATAR, catálogo versionado de capabilities, schemas sob demanda, provenance |
| `read` | READ | `{entity, action, ref?, period?, filters?, page?, page_size?, projection?}` | Consultas autorizadas, sem mutação |
| `analyze` | ANALYSIS | `{analysis_type, period?, refs?, filters?, question?, parameters?}` | Cálculos/achados de owner, FACT vs RECOMMENDATION, fontes, estado de paridade |
| `knowledge` | READ | `{action, query?, topic?, report_id?, business_step?, knowledge_id?, limit?}` | Busca, detalhe e fontes do corpus PROC-0072, citações e versão |
| `execute` | ACT | `{entity, action, params, phase?, proposal_handle?, idempotency_key?, expected_revision?, batch?}` | CREATE/UPDATE/workflow; direto só quando policy allow; alto risco via proposal/consent/ACT |
| `delete` | ACT | `{entity, action, target_ref?, params?, phase?, proposal_handle?, expected_revision?}` | CANCEL/DELETE explicitamente mapeados; sempre confirmação verificável |

O contrato acima é um schema lógico; congelar JSON Schema real Pydantic/MCP antes da primeira migração. Não permitir tool genérica com `url`, `method`, `sql`, `handler_name`, import dinâmico ou parâmetros livres sem schema por action. `params` é discriminado por `(entity, action)` com allowlist versionada, rejeição de unknown fields e limites de paginação/payload. `get_context` entrega somente schemas requisitados: jamais publicar 48 schemas pesados em toda chamada. Devolver `NOT_IMPLEMENTED` honesto quando não houver capability real.

**Nota semântica:** `delete` não inventa exclusão física; `cancel` continua transição de domínio. O nome da tool agrupadora não muda o efeito nem o grau de risco. `read` não deve retornar dados fora do scope por ter parâmetros amplos.

## 3. Action registry owner-local e arquitetura
```
ChatGPT/MCP OAuth → 6 semantic tools → owner-local typed capability catalog
   → explicit (entity, action) dispatcher + per-action schema + risk policy
   → existing application use cases / governed writes / BFF contracts
   → Core effective permissions + resource_scope/ownership + business_rule
   → outcomes/read-back/audit/provenance
```
- Ports & Adapters. Sem persistência ou regras de negócio no transport.
- Preferir dispatcher explícito simples, não framework/registry universal. Cada action recebe ID estável e versão de contrato, handler explicitamente ligado, schema, autorização, efeitos, risco, política de confirmação, limits, source/owner e testes.
- `ACCESS != MANAGE`; somente `controllership-finance.access` e `controllership-finance.manage` para Portal; permissões de outros contextos permanecem governadas pelo owner. Sem novos códigos por tool/rota/filial. Não alterar política DRE legada sem contrato próprio.
- A identidade do JWT não substitui effective permissions live; backend revalida a cada ACT e no commit. Escopo, OCC, idempotência, auditoria, consent_record e postcondition não podem ser contornados.
- Reutilizar `ClaraGovernedWrites`, `ClaraBatchOrchestrator`, `build_mcp_request`, errors e adapters existentes, sem duplicar lógica de fechamento. Não assumir transação global em batch.
- Preservar `agent_directives.character.avatar_distribution` e persona oficial no `get_context` e em projections compatíveis; não inventar avatares.

## 4. Inventário obrigatório de paridade e migration manifest (G1)
Gerar `CLARA-MCP-SEMANTIC-001-capability-matrix.md` no mesmo diretório. Para **CADA tool do tools/list real** e **CADA governed operation** registrar:
`old_tool | inputs/schema | consumer | capability_id | semantic_tool | entity/action | target_schema | backend handler | owner | permission | scope | risk | phase_policy | error_mapping | pagination | response_contract | evidence | test_id | migration_status`.
Inclua explicitamente famílias:
- contexto/catálogo/competências/detalhe/cockpit/estado do mês; checklist, validação e templates;
- documentos/evidências, participantes, versões, mensagens e entregas recebidas/DRE;
- pendências, tarefas e histórico; pacotes, atribuições, revisão e esclarecimentos;
- cutoff, conciliação P3, eventos e revalidação;
- settlements R01/R02, estoque P7/MATR460, movimentos R05/MATR320, WIP H02/MATR989, reconciliação SB9, kardex, ajustes, CPV, matriz R01–R15;
- conhecimento, fontes, corpus, itens e análise de bloqueios;
- PREPARE/ACT individual; `prepare_batch`/`confirm_batch`/`execute_batch`/`get_batch_status`; todos os `governed_operations` reais (não presumir número fixo).
Qualquer operation sem vínculo demonstrado ou sem teste é lacuna de migração, não pode ser removida silenciosamente. Preserve filters, branch_scope, pagination, error codes, status and audit. A paridade é por comportamento e resultado, nunca apenas total de tools.

## 5. Política de execução por risco (G2; produto aprovado, contratos por capability)
Classificar e testar cada action:
- `READ/ANALYZE`: imediata com autenticação/autorização e evidência.
- `LOW_DIRECT` ou `MEDIUM_DIRECT`: criação/atualização não destrutiva, reversível, efeito limitado, intenção inequívoca, parâmetros completos, actor scope e rule ok; executar sem confirmação conversacional redundante **somente se** owner existing contract permitir e houver idempotência/OCC/auditoria apropriados.
- `GOVERNED_HIGH`: abertura/fechamento oficial, decisão contábil, validação/rejeição de evidência, publicação de template/catálogo, entrega irreversível, mudança de visibilidade/versão ou risco material; PREPARE selado → consentimento independente e específico → ACT, read-back.
- `DESTRUCTIVE`: cancelamento/exclusão/revogação e equivalentes; sempre confirmação explícita e independente, alvo/impacto/versão/expiração vinculados.
- `BLOCKED`: permission ausente, resource_scope, regra, staleness, schema inválido ou dependency; não executar, retornar motivo tipado sem leak.
**Classificação inicial conservadora:** operações hoje executadas por `commit_proposal` ficam `GOVERNED_HIGH` até uma matriz por capability demonstrar de forma inequívoca baixa/média criticidade e autorização de mudança da política no owner. O PO autoriza refatoração e execução direta elegível, NÃO autoriza supressão genérica do consentimento atual. Se uma classe não pode ser comprovada como LOW/MEDIUM, preservar consentimento.
- `confirm_batch` não pode ser substituído por auto-confirm para operações governadas; lote com ações diretas e governadas deve separar fases e não ultrapassar consentimento original.
- Erros e estados: UNAUTHORIZED, FORBIDDEN, NOT_FOUND, VALIDATION_ERROR, CONFLICT, CONSENT_REQUIRED, PROPOSAL_EXPIRED, STALE, UNAVAILABLE, NOT_IMPLEMENTED, PARTIAL_OUTCOME, UNKNOWN; mapear aos erros existentes sem quebrar códigos canônicos.

## 6. Orquestração em uma solicitação
Permitir que um único pedido use múltiplos `read/analyze/execute` e, quando necessário, `delete`:
- Planejar DAG de dependências, preservar idempotency keys e revisão dos recursos, limitar cardinalidade/timeout/custo.
- Ações independentes não devem ser bloqueadas por falha não relacionada; dependentes bloqueadas se pré-requisito falhar.
- `GOVERNED_HIGH/DESTRUCTIVE` aguardam confirmação por canal oficial, mesmo em batch. Nunca gerar consent_record pelo LLM.
- Verificação pós-ação por read-back independente; reportar VERIFIED/FAILED/BLOCKED/UNKNOWN e PARTIAL, sem repetir side effect ao retomar.
- Reaproveitar orchestrator existente; não usar tool genérica como bypass dos mecanismos de proposals já estabelecidos.

## 7. Plano de migração e cutover (G3)
Uma **iteração operacional integrada** pode conter checkpoints internos; não fazer big-bang sem evidência.
1. Congelar inventário real, schemas de seis tools, matriz de 100% de operações e policy de risco; aprovar via testes/authorities já estabelecidas.
2. Implementar registry/dispatcher owner-local + seis tools, testes e adaptadores usando a lógica atual (strangler). Nenhuma tool nova por rota futura.
3. Executar suíte de paridade contra handlers atuais para todas as READ/ANALYSIS/KNOWLEDGE e workflows governados; wire snapshots de schema, metadata, annotations, OAuth, status/errors.
4. Executar regressão de consumidores e inventário de dependentes. O plugin ChatGPT só passa à superfície final 6 tools quando consumidores compatíveis e testes passarem.
5. Se consumers existentes ainda exigirem names antigos: manter aliases legados exclusivamente em adapter de compatibilidade com janela de depreciação documentada e **não publicar como six-tools-final** enquanto visíveis; remover apenas após prova de consumer cutover. Não mascarar dual surface como 6 tools.
6. Validar do zero uma conexão real ChatGPT: o host pode cachear schemas; reconectar/republicar plugin conforme procedimento real da plataforma, sem inventar capacidade de atualização automática.
7. Publicar docs, guides de novas actions e matriz `old→new`; adaptar help quando feature alterar UX; evitar mudanças no MFE se não necessárias.
8. Se detectar breaking consumer não resolvível no ciclo, parar cutover produtivo (não o trabalho de testes) e reportar `DECISION_REQUIRED`. Compatibilidade e segurança prevalecem sobre prazo.

## 8. Testes e Definition of Done
- `tools/list` tem **exatamente seis** nomes finais, annotations coerentes, OAuth intacto; catálogo on-demand, schema/validation strict, budget e ausência de enumeração irrestrita de schemas.
- Paridade 100% da matriz: requests, filtros, paginação, envelopes, erros, provenance, documents visibility, scopes, DRE, batch e histories.
- READ sem side effects; `analyze` não recalcula números de owner nem inventa paridade TOTVS; conhecimento mantém citações/locators.
- AuthZ matrix: access/manage, ausência de access, outros usuários, branch/resource scopes, token expirado, Core indisponível → fail closed. Sem autorização por UI.
- Mutation policy: direta LOW permitida; HIGH/DELETE sem consentimento negada; consent valid/expired/wrong actor/stale/replay; idempotência/OCC/audit/read-back; rollback e UNKNOWN reentry.
- E2E batch: múltiplos passos, parcialidade, dependências, risco misto e confirmação única consolidada onde permitida.
- Segurança: fuzz invalid entities/actions, sql/URL injection, arbitrary handler, oversized payload, path traversal; rate/timeout budget.
- MCP conformidade shared delpi_mcp, OpenAPI/BFF parity, backend boundaries, architecture_phase3, audit_fastapi_authz, platform_guardrails, gpt_actions, PG/integration suites, no unrelated regressions.
- Testes reais host ChatGPT após deploy: descobrir catálogo, listar 6 tools, consultar competência, estoque e conhecimento, analisar bloqueios, pedido composto READ, mostrar avatar oficial; testar operações de ACT **somente com dados seguros/autorização específica**, jamais criar/cancelar dados reais como smoke genérico.
- PASS somente com comandos, exit codes, evidence IDs, comparison and outcome; `TEST_NOT_RUN` onde host indisponível. Uma falha preexistente exige reprodução no baseline.

## 9. Deploy produtivo via SSH `operador` (G4)
**PO autorizou deploy deste escopo; autorização condicionada, não acesso irrestrito.**
1. Determinar host/SSH alias, scripts oficiais e diretórios pelo runbook (não hardcode IP, senha, key ou caminho).
2. Preparar rollback: SHA anterior, docker image digest, config, tool catalog anterior, consumer rollback; verificar espaço e health.
3. Verificar `git status` limpo em build/deploy, SHA alvo exato; não promover HEAD concorrente por acidente; alteração externa → pausar/rebaseline, reconciliar antes de seguir.
4. Build e testes de imagem de `controllership-finance-api` apenas (e consumer/plugin se exigido pela migração); não reiniciar cinco serviços por conveniência.
5. Pré-smoke no container/ambiente autorizado + canary se padrão vigente permitir; promoção via script canônico; verificar health, OAuth MCP 401 sem token, effective permission, seis tools reais, catalog, read/knowledge/analyze, avatar URL intacta, API do Portal intacta.
6. Confirmar consumer/plugin cutover: schema novo efetivamente disponível no ChatGPT após atualização/reconexão necessária. Não declarar 6 tools no host apenas por container.
7. Falha em tool count, AuthZ, risk/consent, consumers ou health → rollback da imagem/contrato/plugin afetado segundo runbook, verificar restabelecimento.
8. Registrar SHA, digests, horários UTC, operador, health, testes, logs sanitizados, evidência do resultado final. Não declarar deploy em produção apenas por `git pull`.
9. A refatoração não autoriza renomear o plugin, alterar `controllership-finance` ou expor acesso a financeiro sem AuthZ.

## 10. Checkpoints internos, sem voltar ao PO
`P0 INTAKE` → `P1 INVENTORY/MATRIX` → `P2 DESIGN/SCHEMA/RISK` → `P3 IMPLEMENT/ADAPTERS` → `P4 PARITY/SECURITY/REGRESSION` → `P5 CONSUMER CUTOVER` → `P6 RELEASE/DEPLOY` → `P7 LIVE VERIFY` → `P8 DOC/EVIDENCE/REPORT`.

Cada checkpoint: inputs, SHA, owners, evidence, PASS/FAIL, rework local até PASS. Não pular G2/G3 para acelerar. Escolhas técnicas sem impacto externo são delegadas a Devin. Se escolha material de produto/owner/permission, breaking change não compatível, desativação de safeguards ou infra não autorizada ocorrer, registrar `DECISION_REQUIRED` e não executar essa alteração; não pedir confirmação rotineira.

## 11. Entregáveis
1. Contrato/schema das seis tools e catálogo versionado.
2. Matriz exaustiva tool→action→handler→risco→testes→consumer.
3. Código owner-local dispatcher/handlers e testes, preservando BFF.
4. Inventário e migração de consumers, incluindo atualização de plugin ChatGPT se o ambiente permitir; indicar ação necessária do usuário se depender do host.
5. Política de risco por capability (com justificativa, autorização e outcomes).
6. Testes completos, evidência de segurança, auditorias.
7. Docs e help relacionados, histórico de decisões e migração.
8. Commit SHA e relatório de deploy com rollback.
9. Prova de tools/list seis tools no serviço e, separadamente, no ChatGPT conectado.

## 12. Modelo de execução e relatório
```text
CLARA-MCP-SEMANTIC-001 — FINAL EXECUTION REPORT
BASE HEAD / FINAL HEAD / BRANCH / GIT STATUS:
AUTHORITIES READ / .CURSOR / CONTRACTS:
CURRENT MCP TOOLS/LIST / CATALOG / GOVERNED OPERATIONS:
6 TOOL SCHEMAS AND CATALOG VERSION:
MIGRATION MATRIX COVERAGE (X/X) AND LOCATION:
CONSUMERS FOUND / CUTOVER STATUS:
RISK POLICY LOW_DIRECT / MEDIUM_DIRECT / HIGH / DESTRUCTIVE:
BACKEND AUTHZ (CORE LIVE) / RESOURCE SCOPE / BUSINESS RULE:
CONFIRMATION BOUNDARIES / BATCH / IDEMPOTENCY / POSTCONDITIONS:
FILES/DIFF / TEST COMMANDS+COUNTS / AUDITS / RESIDUAL SEARCH:
SECURITY NEGATIVE TESTS / CLIENT & WIRE CONFORMANCE:
COMMIT SHA / PRODUCTION PREVIOUS SHA & DIGEST / DEPLOYED SHA & DIGEST:
SSH OPERATOR / RUNBOOK / DEPLOY STEPS / HEALTH / ROLLBACK:
LIVE MCP TOOLS/LIST = 6? / CHATGPT PLUGIN TOOLS VISIBLE = 6?:
REAL READ/ANALYSIS/KNOWLEDGE / MUTATION-SAFE VALIDATION:
AVATAR_DISCOVERY AND OFFICIAL IMAGE FALLBACK:
FAILURES/REWORK/EXECUTION_DRIFT/DECISION_REQUIRED:
FINAL STATUS: ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE
NEXT STEP / USER ACTION FOR PLUGIN REFRESH:
```
Classificação: PROVEN | TO_INVENTORY | PLANNED | TARGET. Testes: PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE.

## 13. Regra final
**Uma iteração ponta a ponta, não uma implementação às cegas.** Nenhum sucesso por contagem de tools, HTTP 200, testes isolados ou docs. Se o código está pronto mas o host ainda mostra tools antigas, a task não está funcionalmente encerrada. Se a compatibilidade exigir janela de migração, declarar o estado real e não simular six-tool cutover. Segurança, contratos, ausência de regressão e resultado comprovado determinam o PASS. 

## 14. Adendo stage-03 (2026-10-31) — `analyze(report_comparison)` implementado

`CF-PROC0072-CLARA-REPORT-COMPARISON-IMPLEMENTATION-STAGE-03`: a
capacidade de comparação transversal (doc 126 §6-8) entrou no dispatcher
semântico como **action**, não como tool — a superfície `tools/list`
continua com exatamente seis tools (`get_context`, `read`, `analyze`,
`knowledge`, `execute`, `delete`).

| Aspecto | Entregue |
|---|---|
| Registro | `ANALYZE_ACTIONS["report_comparison"]` em `semantic_bridge.py` |
| Params tipados | `subjects` (required, 2–6), `comparison_kind`, `measure`, `grain`, `baseline_index`, `diff_page`, `diff_page_size` — allowlist estrita, unknown rejeitado |
| Handler | `tool_bridge.tool_analyze_report_comparison` → constrói `ReportComparisonRequest` e chama **a mesma rota BFF** `post_closing_analysis_report_comparison` via `_call_route` — paridade Portal×CLARA por construção, identidade delegada |
| Endpoint BFF | `POST /closing/analysis/report-comparison` |
| Schema discovery | `get_context(topic="schema", entity="closing", action="report_comparison")` |
| Semântica | matriz curada COMPARABLE / RELATED_REQUIRES_EXPLANATION / NOT_COMPARABLE / INSUFFICIENT_EVIDENCE; partial honesty; denied sem vazamento; sem zero implícito |
| Fora de escopo | nenhuma tool plana nova; nenhuma permissão nova; nenhuma tela/export de comparação |

## 15. Adendo stage-04 (2026-10-31) — corpus de conhecimento R01–R15 publicado localmente

`CF-PROC0072-CLARA-KNOWLEDGE-R01-R15-IMPLEMENTATION-STAGE-04`: a base
documental da CLARA passou a incluir as fichas técnicas governadas:

| Aspecto | Entregue |
|---|---|
| Novas fontes | 17 `SourceSpec` em `AUTHORIZED_SOURCES` (`fichas/` — índice, processo, R01–R15) |
| Pipeline | `corpus_ingestion` vigente — segmentação ATX, hash SHA-256 por fonte, supersede por locator estável; **nenhum segundo pipeline criado** |
| Corpus local | `f9857be6` (88 fontes / 2.170 itens) publicado em ambiente autorizado; versão anterior preservada |
| Recuperação | `knowledge`/`search` por `report_id` retorna fichas com `citation_locator` — verificado em execução local |
| Seis tools | preservadas — fichas chegam via `knowledge`/`get_context`, nenhuma tool nova |
| Produção | `PENDING_APPROVAL` — publish produtivo do corpus segue gate próprio |


## Adendo — Release stage-05 (30/10/2026)

Corpus governado publicado em producao: `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00`
(88 fontes/2.186 itens; anterior `fc6f4865` 71/2047 preservado; dump
`~/backups/clara-pre-stage05.sql`). Recuperacao citavel verificada via
repositorio real (fichas por `report_id` com `citation_locator`). Codigo:
release stage-05 (30/10/2026, host `srv-api`, checkout `297068f1b7` — inclui `9f66f8b8e0`) publicado por `up-prod-sequential.sh`: api-delpi `sha256:d46e307ad3e6`, BFF `sha256:7f0e7db69114`, MFE `sha256:8530bbc8f797`; corpus produtivo `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens, 17 fichas, 100% `PORTAL_ACCESS`). Transporte MCP e2e `TEST_NOT_RUN` — client `mcp-clara` segue
`BLOCKED_IAM` (credencial admin rotacionada; owner IAM via canal seguro;
401 fail-closed verificado para anon e token de usuario).

## Adendo Gate 021 — estado real do IAM/MCP (31/10/2026)

Inspeção read-only do realm `delpi` em produção confirmou o client **`mcp-controllership-finance`** totalmente provisionado: habilitado, público, standard flow, PKCE S256, redirect `https://chatgpt.com/connector_platform_oauth_redirect`, scopes default `mcp:tools` + `audience-delpi` (+`basic`,`email`,`profile`,`roles`,`web-origins`,`acr`). O registro histórico `mcp-clara = BLOCKED_IAM` referia-se à nomenclatura anterior e está **superado** — o client correto existe e está configurado. Direct access grants desabilitado por desenho: não há password grant legítimo; o caminho oficial é authorization code + PKCE via conector ChatGPT. **Pendente:** execução e2e real do fluxo (tools/list, read, analyze, knowledge, execute/delete discovery) — `TEST_NOT_RUN` no Gate 021 por indisponibilidade de sessão conectora autorizada; não requer alteração de IAM.
