# SURI MCP — V6/G3 — Plano completo de execução: Entregas e Estoques

**Task:** `SURI-MCP-V6-G3-DELIVERIES-INVENTORY-001`  
**Data:** 2026-10-31  
**Decisão do Product Owner:** autorização explícita para executar G3, do inventário até implementação, testes, commits, push e deploy produtivo **condicionado aos gates** deste documento.  
**Estado deste documento:** `PLANNED / AUTHORIZED`; **não comprova implementação ou deploy**.  
**Base de revisão:** `main` no momento da consulta; rebaseline obrigatório antes da execução.  
**Dependência:** G2 aceito em revisão arquitetural após exportação anual (fonte: `SUPPLIES-G2-FULL-YEAR-EXPORT-PERFORMANCE-001-EVIDENCE.md`; fix `8a24b50181`, evidência `b8ce4a00cf`).

## 1. Objetivo, escopo e contabilidade da paridade

Completar o lote `P1-R3` da matriz de paridade Portal ↔ SURI sem desenvolver páginas do Portal, sem criar tools ou permissões e sem duplicar regra TOTVS.

| ID | Capacidade Portal (inventário P0) | Owner da fonte | Intenção MCP | Estado antes de G3 |
|---|---|---|---|---|
| R-11 | Entregas / atrasos: painel paginado | `api-delpi`, composição `supplies-api` | `read(entity="deliveries", action="late")` | `PROVEN` no Portal; `TO_IMPLEMENT` na SURI |
| R-12 | Controle de Estoques: stock-balances summary e items | `api-delpi`, composição `supplies-api` | `read(entity="inventory", action="summary"|"items")` | `PROVEN` no Portal; `TO_IMPLEMENT` na SURI |

**Importante:** são **2 linhas de capacidade** (R-11, R-12), embora haja 3 ações MCP candidatas. Baseline implementado G2 `19/45 = 42,2%`; alvo estritamente condicionado aos testes G3 `21/45 = 46,7%`. Não atualizar a matriz como `PROVEN` antes de implementação + testes; diferenciar `IMPLEMENTED_IN_CODE`, `TESTED_LOCALLY`, `DEPLOYED`, `AUTHENTICATED_RUNTIME_PROVEN`. O denominador deve ser revalidado no HEAD, nunca alterado apenas para elevar percentual.

**Fora de escopo:** `safety_stock` (R-13/R-14 = P1-R4/G4); OTD; consumo de OP; novos CRUDs; alertas automáticos; novas páginas; alterações do legado `plugins/dashboard-supplies`; mudanças de RBAC e OAuth; criação de sixth tool.

## 2. Autoridades e arquitetura inegociável

Reabrir, nesta ordem: `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`; regras `.cursor` globais `development-standards-index`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`, e específicas `plan-construction`, `plan-execution`, `test-and-commit` e outras materiais; ADRs/contratos; schemas/HEAD; testes; documentação; roadmap. Consultar `docs/12-roadmap-e-evolucao/supplies/README.md` e `IMPLEMENTATION-PLAN.md`, `SURI-MCP-FULL-PARITY-{MATRIX,IMPLEMENTATION-PLAN,EXECUTION-BRIEFS}.md`.

Fluxo: usuário ChatGPT OAuth user-delegated → SURI MCP `supplies-mcp` → use cases/gateways do contexto `supplies-api` → `api-delpi` / Core; MFE `plugins/supplies` permanece composição de UX e nunca fonte de regras. Flask BFF mantida; MCP container separado preservado. Não usar acesso direto à SQL TOTVS pelo MCP nem import de domain/application de outra API. `api-delpi` é owner da consulta, `supplies-api` owner da composição e AuthZ, Core owner de effective permissions. `@delpi/plugin-ui` e Help permanecem inalterados salvo evidência de impacto real.

### Regra de superfície fixa, sem exceção tácita

`get_context`, `read`, `analyze`, `knowledge`, `execute` = **exatamente cinco tools**. G3 adiciona ações ao registry fechado de `read`; **não registra `deliveries` ou `inventory` como tools separadas**, nem `delete`. Ver regra explícita na `SURI-MCP-FULL-PARITY-IMPLEMENTATION-PLAN.md`. Para evolução aditiva de Literals/schemas, aumentar `CATALOG_VERSION` de 5 para 6 **apenas se a revisão dos contratos confirmar esse número como próximo disponível**. `tools/list==5` e zero regressão do V5 são aceites obrigatórios.

Autorização por operação no backend, fail-closed: identidade JWT não é permission; resolver Core effective permissions por chamada; `capability AND unit_scope AND resource_scope/ownership AND business_rule`. `can_use_operations` é guard candidato do brief P1-R3, sujeito a confirmação no HEAD da BFF. `view-all` nunca amplia unidade. Propagar a identidade user-delegated/S2S autorizado exatamente como o gateway canônico; rejeitar service principal simulando usuário, audience errada, filtros inventados ou unidade não autorizada.

## 3. Fluxo de execução e gates

### G3.0 — Rebaseline / inventário comprovável (BLOCKING)

Cursor deve obter `HEAD`, `origin/main`, branch, `git status`, SHA fonte do deploy atual e alterações concorrentes, preferindo worktree isolada quando dirty. Revalidar G2 `CLOSED/PASS` por código, documentação e evidência de runtime; se drift material, registrar `EXECUTION_DRIFT`, não conciliá-lo silenciosamente.

Inspecionar e citar **arquivos e métodos exatos no HEAD**, sem presumir que nomes no brief são atuais:
- Consumidores reais das páginas WF-07 Entregas/Atrasos e WF-15 Controle de Estoques (rotas, filtros, parâmetros, forma do retorno, paginação, empty/partial/error, tenant/unidades);
- BFF routes, use cases, `LateDeliveriesCompositionService`, `InventoryStockBalancesService` e gateways equivalentes atuais;
- producers `api-delpi` (rotas `/deliveries/late` e `/inventory/stock-balances/*` como *candidatas*, conferir no HEAD), SQL e contratos de paginação, limites e datas;
- guards reais `can_use_operations`/`require_units`/`require_unit`; traduções de erro 401/403/404/422/429/5xx, timeouts, S2S e classificação `partialFailures`;
- `supplies-api/app/interfaces/mcp/{constants,schemas,server,tool_bridge}.py` e testes V5, incluindo `test_read_union_dispatch.py`;
- operações de inventário que **não** devem confundir saldos com estoque de segurança.

Inventário sai com **contrato congelado por ação**, tabela producer→BFF→MCP, query allowlist, tipo e default de cada filtro, envelopes JSON, limites e riscos. Um search miss não prova ausência. Se a página não existir/homologação tiver mudado: `EXECUTION_DRIFT` no subescopo.

### G3.1 — Contract freeze e requisitos (BLOCKING)

Definir e documentar, antes de tocar handlers:
- `read(deliveries,late)`: campos de filial, período, atraso, status, ordenação, paginação e budget **exclusivamente como o Portal/BFF de fato aceita**; não inventar filtros.
- `read(inventory,summary)`: agregação, filtros, unidades e estados de indisponibilidade do serviço owner.
- `read(inventory,items)`: paginação, busca, sort, filtros, unidade e limite exato; preservar page-budget cap do `InventoryStockBalancesService` (brief P1-R3).
- Resultado `data` mantém semântica, contagens, convenção de valores e proveniência do BFF. Não classificar `0` como indisponibilidade ou vice-versa.
- Política de lote grande: não criar exportação nova, truncar resultados nem remover budget; manter paginação e limites do owner.
- Side effects = zero; ações READ somente.
- Decidir se novos tipos de schema podem ser `Union` segura ou exigir discriminação adicional **sem quebrar o wire vigente**; endereçar o bug histórico de defaults de modelos irmãos e manter `model_dump(exclude_unset=True)`.

**Entrega:** adendo de contract freeze e matriz RQ/AC, aprovada contra código/owner atual. Caso contrato exija alteração em owner externo ou permission nova, parar a parte afetada como `EXECUTION_DRIFT`.

### G3.2 — Implementação BFF/MCP mínima

Implementar apenas a fatia necessária:
1. `constants.py`: registrar `deliveries:late`, `inventory:summary|items` em `READ_ACTIONS_BY_ENTITY`; adicionar vocabulários fechados por ação; `CATALOG_VERSION=6` condicionado ao G3.1.
2. `schemas.py`: filtros tipados Pydantic `extra="forbid"`, identidades se necessárias, limites e mensagens compatíveis.
3. `server.py`: ampliar Literals/unions e descrições de **`read`**, sem tool nova.
4. `tool_bridge.py`: dispatch por (entity, action) para handlers dedicados; reutilizar instâncias e serviços/gateways BFF canônicos, com AuthZ por chamada e propagação correta de identity/S2S; mapeamento de erro e partial fiel. Nunca importar domain/application do `api-delpi`.
5. `get_context(catalog)`: publicar versão e capacidades efetivamente habilitadas; remover metadata contraditória antiga “no write capability exists”, pois `execute(suppliers.create/update)` existe (fix apenas documental/semântico, não habilitar writes novas).
6. Manter G1 fornecedores/CEP/preview e G2 SC/PC/export e `execute` com idempotência durável V005 intactos.
7. Revisar limites de payload e latência à luz do incidente de exportação anual; se inventário for de grande volume, preservar budget por página, sem fan-out arbitrário ou aumento de timeout não fundamentado.

**Arquivos prováveis não são autorização de diff:** no HEAD escolher o menor conjunto apropriado.

### G3.3 — Testes obrigatórios e segurança

Cobrir **por ação** `late`, `summary`, `items`:
- positivo com dados reais mockados do owner e caso empty;
- filtros válidos e inválidos (unknown 422, datas invertidas, paginação/budget excedido, unidade ausente/indevida, branch sibling, sort incompatível);
- autorização positiva, sibling CC/units e negativa sem `supplies.access`, Core indisponível, user-delegated ausente, principal de serviço, token/audience inválida;
- erros upstream 401/403/404/429/timeout/502/503, partial failure conforme contrato, preservando honestidade de incompletude;
- query string e chamadas gateways exatamente as mesmas da BFF para mesmos filtros;
- prova de `no write` e ausência de consulta direta a banco alheio;
- teste `tools/list==5`, catálogo V6, regressão V5 completa, filtros desconhecidos fail-closed;
- **integração MCP real**: `initialize → tools/list → tools/call` passando pelo Pydantic Union e dispatch, com payload mínimo, optional omitido, defaults de modelo irmão e erros 422; mocks só nos owners/gateways, não pular o servidor MCP. Manter os seis testes históricos `test_read_union_dispatch.py`.
- testes de contrato da BFF e do producer, quando material; suíte `suri_mcp`, `supplies-api` e builds relevantes; reportar skip/env-gated, nunca mascarar.

Classificação `PASS|FAIL|INCONCLUSIVE|TEST_NOT_RUN` com comandos, contagens, SHAs e ambiente. Smoke federado MFE apenas se houver alteração user-facing efetiva; caso contrário registrar `NOT_APPLICABLE` fundamentado.

### G3.4 — Revisão / gate código (BLOCKING antes do push/deploy)

Produzir evidence `supplies-api/docs/SURI-MCP-V6-G3-CODE-ACCEPTANCE.md` com: base/final HEAD; fatos PROVEN; contratos; diffs; owner; RQ/AC; cenários positive/sibling/negative; suíte; AuthZ; residual search; `EXECUTION_DRIFT`; regressão; next step. Exigir:
`G3_CONTRACT=PASS`, `G3_AUTHZ=PASS`, `G3_TESTS=PASS`, `G3_REGRESSION=PASS`, `TOOLS=5`; caso contrário não avançar. Revisão humana/arquitetural ou gate formal aplicável **não** pode ser substituído pelo executor aprovando a si mesmo.

### G3.5 — Commits / push com isolamento

Conferir `git status`, `origin/main`, conflitos e diff; se árvore concorrente suja, worktree isolada; nunca reset destrutivo. Commits pequenos por responsabilidade (código/testes/contrato/docs), IDs em inglês e UX em PT-BR. Push controlado para branch/procedimento oficial; se `main` avançar, rebase/reconciliação segura e repetir testes afetados. Registrar SHAs completos e `SOURCE_SHA` imutável para deploy. Não incluir secrets, tokens, payloads sensíveis ou logs de usuários.

### G3.6 — Preparação de deploy (BLOCKING)

A autorização do PO cobre **deploy controlado do G3**, condicionado à aprovação G3.4, existência do source no remoto, ausência de drift e procedimento operacional oficial. Inventariar host/repo/compose/health, versão atual, imagem MCP, container, digest, config OAuth/Redis/S2S, service dependencies; não copiar segredos. Verificar que `supplies-mcp` é o serviço a atualizar se apenas MCP mudou; não recriar BFF/Core/api-delpi/PR-api/Keycloak/gateway sem causa técnica comprovada. Criar tag/digest de rollback efetiva e comando de reversão testável. Conferir janela/impacto e alertas.

### G3.7 — Deploy produtivo e gates operacionais

Seguir runbook canônico, preferindo Git→pull→build→recreate apenas `supplies-mcp`. Preservar Git dirty e commits locais de produção, conforme runbook; sem `reset --hard`; não presumir host/IP. Confirmar imagem construída de SOURCE_SHA correto, `CATALOG_VERSION` esperado in-image e cinco tools **antes** de publicar. Recriar somente serviço afetado. Healthz, restart count, logs sem secrets, identidade da imagem e saúde de BFF/Core/api-delpi/PR-api. Se falhar health, OAuth, AuthZ, regressão ou contrato: rollback V5 e emitir `FAIL/EXECUTION_DRIFT` com evidência.

### G3.8 — OAuth / smoke autenticado / descoberta ChatGPT

Separar: a) `tools/list` container; b) catálogo pelo transporte MCP público; c) chamada OAuth real user-delegated auth-code+PKCE; d) schemas de ferramenta no ChatGPT após atualização do plugin. Verificar metadata 200, challenge sem Bearer 401+`WWW-Authenticate`, audience errada 401, service principal negado, health 200, cinco tools e catálogo V6. Homologar `deliveries.late`, `inventory.summary`, `inventory.items` com unidades autorizadas e filtros que retornem dados (ou empty comprovado), validar contagens, paginação, budget e paridade com Portal/BFF. Testar negativos 401/403/422 sem expor dados de terceiros. Evitar exportações grandes e qualquer write ERP. Se o ChatGPT não refletir schema novo, registrar `STALE_EVIDENCE`, atualizar conexão SURI e reexecutar call real antes de declarar `CHATGPT_AUTHENTICATED_RUNTIME_PROVEN=PASS`. Se não houver usuário/ferramenta disponível, `INCONCLUSIVE` nunca PASS inferido.

### G3.9 — Aceite final / documentação

Criar `supplies-api/docs/SURI-MCP-V6-G3-DEPLOY-ACCEPTANCE.md`, atualizar matriz R-11/R-12 e planejamento/briefs, adendo de contrato/catálogo. Só promover `R-11/R-12` a PROVEN SURI quando testes e evidência correspondentes; distinguir código/teste de produção autenticada. Resultado alvo `21/45` somente após recontagem e gates completos. Registrar estado do deploy, SHA, images/containers, rollback, testes, incidentes e gaps; preservar histórico de G2. Não mexer em status de G4/Safety Stock.

## 4. Sequência formal, responsáveis e aceites

| Etapa | Owner principal | Gate de saída |
|---|---|---|
| G3.0 Inventário | Arquitetura + supplies-api + api-delpi | fontes/consumers/producers reais mapeados |
| G3.1 Freeze | BFF/owner api-delpi + Produto | contrato fechado, AuthZ e RQ/AC completos |
| G3.2 Código | supplies-api/SURI | menor diff, 5 tools, sem bypass |
| G3.3 Tests | supplies-api + owners afetados | positive+sibling+negative + JSON-RPC E2E |
| G3.4 Review | GPT Arquiteto/quality gate | aceite do código `PASS` |
| G3.5 Git | executor | commit/push/source SHA verificável |
| G3.6 Pre-deploy | Infra | rollback, config e escopo mínimo |
| G3.7 Deploy | Infra | imagem nova saudável, sem regressão |
| G3.8 Homologação | QA + SURI real | AuthZ, tool catalog e três ações comprovados |
| G3.9 Evidência | owner G3 | matrizes/documentos reconciliados, decision |

**Condições de parada:** contrato divergente; owner impróprio; novo endpoint/permission/tool pedido; alteração de SQL/ERP não autorizada; isolamento de unidade quebrado; `view-all` alargando filial; `partial` mascarado como sucesso integral; consumo excedendo budget; necessidade de mudar OAuth; ausência de rollback; G2 regressão; falta de usuário autenticado para runtime. Classificar `EXECUTION_DRIFT` e interromper subgrafo afetado; não justificar depois da implementação.

## 5. Relatório obrigatório do Cursor

```text
TASK:
BASE HEAD / ORIGIN MAIN / FINAL HEAD / GIT STATUS:
SOURCE SHA / IMAGE SHA / CONTAINER ID:
G3.0 INVENTORY:
G3.1 CONTRACT FREEZE:
G3.2 IMPLEMENTATION:
G3.3 TESTS:
G3.4 CODE REVIEW:
G3.5 COMMIT/PUSH:
G3.6 DEPLOY PREP / ROLLBACK:
G3.7 PROD DEPLOY:
G3.8 AUTHENTICATED SMOKE / CHATGPT SCHEMA:
G3.9 DOCUMENTATION:
R-11 DELIVERIES.LATE:
R-12 INVENTORY.SUMMARY / ITEMS:
FILTERS / PAGINATION / PAGE BUDGET:
AUTHZ / UNITS / RESOURCE SCOPE / ERROR MAPPING:
CATALOG_VERSION / TOOL_COUNT:
POSITIVE / SIBLING / NEGATIVE:
G1/G2 REGRESSION:
FILES INSPECTED / FILES CHANGED / CONTRACT IMPACT:
TESTS / BUILD / HEALTH / OAUTH:
FACTS PROVEN / TO_INVENTORY / EXECUTION_DRIFT:
RESIDUAL SEARCH / UNRESOLVED / NEXT STEP:
COMMITS / DOCUMENTATION URL:
```

Decisão GPT de aceite: `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. O executor não autodeclara `CLOSED/PASS` sem evidência runtime e revisão correspondente.

## 6. Handoff operacional e autorização

O PO autorizou o **lote G3 inteiro**, incluindo deploy produtivo condicionado aos gates anteriores. Não requisitar nova autorização genérica para as etapas previstas; **exigir decisão adicional** somente se houver mudança material de owner, contrato, segurança, deploy fora de escopo ou stop condition. O próximo lote G4 não está autorizado. Não confundir G3 desta paridade SURI com fases C1/C2/C3 de Purchase Requests ou com etapas E11 do Portal.

**Ordem mandatória:** READ → VERIFY → CLASSIFY → DECIDE → IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME → RESIDUAL SEARCH → DOCUMENT → REPORT.
