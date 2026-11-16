# 122 — EVA EXECUTION REPORT: read(routing.steps) — roteiro de fabricação

**TASK_ID:** `EVA-PRODUCT-ROUTING-SEMANTIC-CAPABILITY-E2E-01`
**DATA:** 2026-11-16
**STATUS:** `DEPLOYED_PENDING_AUTHENTICATED_E2E`

```text
TASK_ID              EVA-PRODUCT-ROUTING-SEMANTIC-CAPABILITY-E2E-01
BASE_HEAD            a7218deeca19d7201ac02fe88f6572b054f39c14
FINAL_HEAD           5c9774feaf53595d3291dec2ab2eff808e5d99af
ORIGIN_MAIN          5c9774feaf53595d3291dec2ab2eff808e5d99af
STATUS               DEPLOYED (engineering-api healthy em PROD);
                     E2E autenticado pendente (credencial do owner)
```

## AUTHORITIES_READ

- `AGENTS.md` (entrega, deploy canônico srv-api, delpi-verifier, branch governance)
- `.cursor/rules/` — development-standards-index, centralized-rules-first,
  clean-code-architecture-guardrails, test-and-commit, evidence-driven-execution,
  mfe-own-api-no-direct-api-delpi, migrations-immutable-checksum,
  infra-sequential-container-startup, local-first-deploy
- `docs/12-roadmap-e-evolucao/engineering/54` (plano mestre seis tools —
  `read(routing,steps)` previsto como ponto de extensão canônico, §5)
- `docs/12-roadmap-e-evolucao/engineering/69` §10 (roteiro SG2 =
  owner-blocked sem contrato — agora resolvido via api-delpi)
- `docs/12-roadmap-e-evolucao/engineering/121` (runbook E2E autenticado,
  caminho password grant → token-exchange `delia-api` → `mcp-engineering`)

## FACTS_PROVEN

- Contrato api-delpi: `GET /products/{code}/guide`
  (operationId `get_product_guide`), params `branch`, `page`, `page_size`
  (≤500), `max_depth` (1–15); envelope `paged_list`; itens =
  `GuideOperation.to_dict()` (branch, route_code, product_code,
  operation_code, operation_description, resource_code, work_center,
  setup_hours, standard_time_hour_mil/hours_piece/minutes_piece,
  operation_type, mandatory_operation/sequence/report,
  component_code/description/sequence, bom_level).
- Fonte: `ProductGuideRepository` — SG2010 (roteiro) × SG1010 recursivo
  (BOM vigente) × SGF010 (componentes por operação) × SB1010 (descrições);
  `D_E_L_E_T_=''`; ordenação `bom_level, G2_PRODUTO, G2_OPERAC, GF_TRT`.
- AuthZ upstream: `@require_permission(API_DELPI_ACCESS)` — Bearer humano
  validado por JWKS Keycloak (RS256).
- BFF canônico: `ApiDelpiDelegatedAuxiliary` (delegação Bearer humano,
  sem service token) — padrão idêntico a `fetch_product_structure`.
- Superfície MCP pública: exatamente 6 tools (`test_semantic_surface_is_exactly_six`).

## TO_INVENTORY

- SH6/SH8 (`H6_TIPO`, `H6_RECURSO`): não fazem parte do contrato
  `/guide` (SG2010). Não consumidos — semântica inventariada apenas como
  contexto ERP, nunca como contrato.
- `not_found` upstream em `/guide`: rota responde 200 `items=[]` para
  produto inexistente e para produto sem roteiro — distinção "produto
  inválido" vs "sem roteiro" não existe no contrato atual do owner
  (404 só ocorreria por rota inexistente). Tratamento EVA: `items=[]` +
  `total=0` = ausência explícita e honesta.

## API_DELPI_ROUTING_CONTRACT

`GET /products/{code}/guide?branch&page&page_size&max_depth` → envelope
`api_delpi_success` shape `paged_list`; sem `page/page_size` retorna
modo full (todos os itens). Ordenação oficial por bom_level → produto →
operação → sequência de componente. Erros: 401/403 AuthZ, 422 validação
de query; sem 404 semântico.

## BFF_INTEGRATION_CONTRACT

- MCP: `read(entity="routing", action="steps", ref=<product_code>,
  filters={branch, max_depth}, pagination={page, page_size})` — tool
  `read` existente, `ref_arg=product_code`, `paginated=True`.
- REST (handoff frontend): `GET /v1/products/{product_code}/routing`
  (operationId `get_product_routing`), query `branch`, `max_depth`
  (1–15), `page` (≥1), `page_size` (1–500); envelope `ok|fail`;
  estados: available→200, forbidden→403, not_found→404,
  unavailable→502; AuthZ `engineering.access` + principal humano.

## EVA_SEMANTIC_CAPABILITY

`routing.steps` — promovida de `PLANNED_SEMANTIC_ACTIONS` para
`SEMANTIC_ACTIONS` (status `proven`), exatamente o ponto de extensão
previsto no plano mestre (doc 54 §5: `read(routing,steps)`).
Resposta preserva payload oficial do owner sem reconversão de tempos.

## MCP_TOOLS_BEFORE / AFTER

`get_context, read, analyze, knowledge, execute, delete` → idênticos.
`NEW_MCP_TOOLS_CREATED = 0`.

## FILES_INSPECTED (principais)

`api-delpi/app/interface/http/routes/product_routes.py`,
`openapi_agent_metadata.py`, `list_product_guide_use_case.py`,
`product_guide_repository.py`, `guide_operation.py`,
`engineering_app/interface/mcp/{server,semantic_bridge,tool_bridge}.py`,
`application/eva/semantic_registry.py`,
`infrastructure/gateways/{delegated_auxiliary,downstream_client}.py`,
`interface/http/routes/product_routes.py`, `docs/12…/54,69,121`,
`sandbox/eva_pdf_mcp_e2e.py`, `tests/test_eva_mcp_semantic.py`,
`tests/test_product_drawing_pdf.py`, `tests/conftest.py`.

## FILES_CHANGED

```
M engineering_app/application/eva/semantic_registry.py
M engineering_app/infrastructure/gateways/delegated_auxiliary.py
M engineering_app/interface/http/routes/product_routes.py
M engineering_app/interface/mcp/semantic_bridge.py
M engineering_app/interface/mcp/tool_bridge.py
M tests/test_eva_mcp_semantic.py
M tests/test_health.py
A tests/test_product_routing.py
```

## RQ_COVERAGE

| RQ | Status |
|---|---|
| RQ-01 contrato inventariado | PASS (evidência código+SQL acima) |
| RQ-02 BFF existente reutilizado | PASS (`ApiDelpiDelegatedAuxiliary`) |
| RQ-03 tool semântica existente ampliada | PASS (`read`, zero tools novas) |
| RQ-04 consulta autorizada, read-only | PASS (humano + `engineering.access` + AuthZ owner downstream) |
| RQ-05 operações/sequência/recursos/tempos | PASS (payload preservado, sem reconversão) |
| RQ-06 compat product/BOM | PASS (regressão: 287 testes superfície MCP/products/auth) |
| RQ-07 provenance/estados/sem alucinação | PASS (estados tipados; `unavailable` honesto) |
| RQ-08 fluxo integrado real | PARTIAL — cadeia completa testada por contrato/adapter; live auth pendente (ver UNRESOLVED) |
| RQ-09 documentado | PASS (este doc + handoff) |

## AC_RESULTS

| AC | Status |
|---|---|
| AC-01 roteiro com dados oficiais | PENDING_LIVE (contrato+unidade provados; aguarda E2E autenticado) |
| AC-02 ordem oficial | PASS (ordenação do owner preservada: bom_level→produto→operação→componente) |
| AC-03 CT/recursos/tipos/tempos | PASS (campos SG2 transportados intactos; teste confirma valores) |
| AC-04 ausência explícita | PASS (`available`+`items=[]`+`total=0`, teste dedicado) |
| AC-05 inválido/sem permissão | PASS (403 forbidden; service principal negado; 404 defensivo) |
| AC-06 falha upstream ≠ sucesso falso | PASS (`unavailable`/`timeout`/`contract_error` tipados — mesma semântica das ações existentes) |
| AC-07 capabilities anteriores | PASS (regressão suíte MCP/products/auth: 287 verdes) |
| AC-08 nenhuma tool nova | PASS (6 tools, teste de superfície) |
| AC-09 via BFF oficial | PASS (único caminho: `DownstreamClient`→api-delpi) |
| AC-10 linguagem natural | PENDING_LIVE (depende do host MCP — discovery cobre `routing.steps`) |
| AC-11 verificação independente | ACCEPT_WITH_RESIDUAL (ver abaixo) |
| AC-12 prod validado pós-deploy | PARTIAL — 401 boundary+OpenAPI+saúde OK; teste real MCP autenticado delegado ao owner (ChatGPT EVA) |

## TESTES

- **UNIT_TESTS:** 9 novos em `test_eva_mcp_semantic.py` (delegação de
  args, ref obrigatório, filtro desconhecido, forbidden 403,
  not_found 404, vazio honesto, unavailable honesto, principal service
  negado, adapter → path do owner com Bearer e `service_token=None`).
- **CONTRACT_TESTS:** 7 em `test_product_routing.py` (payload owner,
  401, 403, 403 fonte, 404, 502, OpenAPI). Adapter `fetch_product_guide`
  → `GET /products/{code}/guide` com params mapeados.
- **INTEGRATION_TESTS:** cadeia MCP→bridge→adapter→(stub client)→
  envelope verificada nos testes semânticos. Live real: api-delpi local
  indisponível (checksum migration drift pré-existente — fora do escopo).
- **REGRESSION_TESTS:** suíte engineering-api — 1342 pass, 21 skip,
  3 falhas pré-existentes comprovadas em baseline por stash
  (`test_d16_attendance_flags::test_isolation_between_requests`,
  `test_pi_with_children_flattened_as_parent_block`,
  `test_normalize_box_json_safe`).
- **SECURITY_TESTS:** service principal → 403; sem permissão → 403;
  forbidden upstream → 403 tipado; `service_token` nunca injetado;
  sem secrets em logs/payloads.
- **SEMANTIC_EVALS:** discovery (`get_context`) lista `routing.steps`
  proven; filtros desconhecidos rejeitados; paginação fora de ação
  paginada rejeitada. Interpretação NL depende do host (ChatGPT) —
  validação final pelo owner.
- **MCP_COMPAT:** `tools/list` = 6 tools antes/depois; assinaturas
  inalteradas.
- **GATES:** `audit_architecture_phase3 --check --base HEAD` → 0
  regressões; `audit_platform_guardrails --check --base HEAD` → 0.

## INDEPENDENT_VERIFIER

- Motor oficial `delpi-verifier`: **indisponível** — `devin` CLI sem
  auth neste ambiente; `cursor-agent` sem quota (2 tentativas cada,
  INCONCLUSIVE por infra, não por conteúdo).
- Substituto autorizado pela task ("agente de verificação disponível no
  ambiente Devin"): subagente independente com contexto limpo
  (read-only), adversarial.

**VERIFIER_VERDICT:** `ACCEPT_WITH_RESIDUAL`

Residuais do verificador:
- #8 [minor] 4xx de validação upstream → `unavailable` (padrão
  pré-existente de `_map_error`, uniforme em todas as ações delegadas —
  follow-up transversal, não routing-específico).
- #9 [minor] `unavailable` dentro de envelope `success:true` (mesma
  semântica de `product.structure`/LMP — decisão plataforma).
- #10 [minor] `page` sem `page_size` → modo full upstream (contrato do
  owner fielmente delegado).
- #14 [info] prova live adiada para pós-deploy → este doc.

## COMMIT_SHA / PUSH_VERIFIED

`5c9774feaf` — `git push origin main` confirmado; `origin/main` ==
`HEAD` == `5c9774feaf`.

## DEPLOY

```text
DEPLOY_ENVIRONMENT   PROD srv-api (operador@192.168.1.237)
DEPLOY_PROCEDURE     git pull --ff-only +
                     infra/scripts/up-prod-sequential.sh --build engineering-api
DEPLOY_SHA           5c9774feaf
DEPLOY_STATUS        SUCCESS — delpi-engineering-api Up (healthy);
                     código verificado dentro do container
RUNTIME_POSTCONDITION /v1/products/{code}/routing → 401 sem auth;
                     OpenAPI declara a rota; /mcp → 401 challenge;
                     api-delpi healthy; sem regressão em containers irmãos
ROLLBACK_READINESS   git revert do SHA + mesmo script --build
                     engineering-api (imagem anterior no daemon)
```

## RESIDUAL_SEARCH / EXECUTION_DRIFT / UNRESOLVED

- `EXECUTION_DRIFT`: nenhum.
- `ARCHITECTURE_DECISION_REQUIRED`: nenhum.
- `UNRESOLVED`: validação autenticada real em PROD
  (read(routing.steps) com token humano `engineering.access`) —
  delegada ao owner via sessão EVA/ChatGPT; o ambiente não possui
  credencial de avaliação aprovada (Doc 121 §5: usuário eval dedicado
  ainda não provisionado com senha em cofre).
- api-delpi LOCAL (dev stack) fora do ar por checksum divergente em
  `V024__prc_record_flags.sql` — trabalho concorrente, pré-existente,
  fora do escopo desta task.

## FRONTEND_HANDOFF

Para o Portal Engenharia (detalhe do produto):

- **Rota BFF autorizada:** `GET /v1/products/{product_code}/routing`
  na **engineering-api** — o MFE NUNCA chama api-delpi direto
  (`mfe-own-api-no-direct-api-delpi`).
- **Query:** `branch` (opcional: `01|02`), `max_depth` (1–15,
  default = todos os níveis da BOM), `page`/`page_size` (omitir =
  modo completo).
- **Resposta 200:** `data.items[]` com `operation_code`,
  `operation_description`, `work_center`, `resource_code`,
  `operation_type`, `setup_hours`, `standard_time_hour_mil`,
  `standard_time_hours_piece`, `standard_time_minutes_piece`,
  `mandatory_operation/sequence/report`, `component_*`, `bom_level`,
  `route_code`, `branch`, `product_code`.
- **Ordenação oficial já vem pronta** — renderizar na ordem recebida,
  não reordenar no cliente.
- **Tempos:** exibir as três formas fornecidas (`hour_mil`,
  `hours_piece`, `minutes_piece`) sem conversão local; `setup_hours`
  em horas.
- **Estados:** `items=[]` → estado vazio "produto sem roteiro
  cadastrado"; 403 → forbidden; 404 → não encontrado; 502 → fonte
  indisponível com retry manual. Nunca renderizar tabela vazia como
  se fosse roteiro.
- **UX:** aba/seção "Roteiro" no detalhe do produto; seguir o padrão
  visual do Portal Engenharia (`plugins/engineering`), kit
  `@delpi/plugin-ui`, estados loading/empty/error/forbidden.
- **Row spanning:** uma operação com N componentes repete os campos de
  operação em N linhas (bom_level/operation_code) — agrupar por
  `operation_code` na apresentação.

## NEXT_BOUNDED_STEP

1. Owner executa `read(routing.steps)` autenticado em PROD
   (EVA/ChatGPT) e confirma payload real → fechar AC-01/AC-10/AC-12.
2. Frontend Portal Engenharia (task separada) consome
   `/v1/products/{code}/routing` com o contrato acima.
3. Follow-up transversal (fora desta task): classificação de 4xx de
   validação em `_map_error` e semântica de `unavailable` no envelope
   MCP — decisão plataforma, não routing-específica.
