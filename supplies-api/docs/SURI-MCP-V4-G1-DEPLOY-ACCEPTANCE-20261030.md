# SURI-MCP-V4-G1-DEPLOY-001 — ACEITE DE DEPLOY PRODUTIVO

Data: 2026-10-30 · Autorização: Product Owner (deploy produtivo explícito)

```text
TASK:            SURI-MCP-V4-G1-DEPLOY-001
BASE HEAD:       c82d928802 (commit V4 G1)
SOURCE SHA:      c82d92880219a7e97b76457e6174bc1caf4a27ac
FINAL HEAD:      ac1bb7d765 (prod repo já em origin/main — inclui V4 + CAIO/docs concorrentes)
ORIGIN MAIN:     ac1bb7d765dcb0b824ab0abbeb0834c0b1cb3e7c
BRANCH:          worktree detached (delpi-central-g1-wt); prod em main
GIT STATUS:      limpo local e em produção
```

## Gates

```text
D0 REBASELINE:        PASS — c82d928802 ancestor de origin/main; commits
                      concorrentes (CAIO, docs CF) disjuntos de supplies-api
                      (0 linhas de diff); CATALOG_VERSION=4; 5 tools via
                      create_mcp_server(); READ_ACTIONS_BY_ENTITY com
                      suppliers+postal_codes; ANALYSIS_KINDS com
                      supplier_creation_preview; execute V3 preservado; zero
                      mudança OAuth/Keycloak/RBAC no diff.
D1 SECURITY/CONTRACT: PASS — handlers read usam exclusivamente
                      _S2S_GATEWAY.get (zero verbos de escrita no caminho de
                      leitura); _operations_user/_admin_user re-derivam
                      permissão por chamada (Core como fonte); integration_status
                      gated por can_administer (supplies.manage); Bearer do
                      usuário propagado; DelpiS2SApiGateway do owner correto;
                      CNPJ via is_valid_cnpj canônico; CEP via
                      normalize_postal_code (8 dígitos); catalogs na allowlist
                      fechada; operation_id validado como UUID; schemas
                      _ClosedModel; paginação/rate-limit canônicos; preview
                      read-only (write_enabled=false, nenhum POST/PUT);
                      proveniência no payload; provider indisponível → erro
                      honesto; V005 idempotência intacta; nenhuma migration
                      nova; nenhum bypass Protheus.
D2 TESTS:             PASS — supplies-api inteira: 796 passed / 24 skipped
                      (baseline G1 796/24 — idêntico); SURI 131/131;
                      test_suppliers_read 34/34; ZERO FAIL; V3 execute
                      preservado; READ sem side-effect de escrita.
D3 BUILD/PREP:        PASS — infra/docker-compose.yml: supplies-mcp builda de
                      supplies-api/Dockerfile, container delpi-supplies-mcp;
                      PRE-DEPLOY SHA=ac1bb7d765; PREVIOUS MCP IMAGE=c622ed1b33de
                      (retida p/ rollback); PREVIOUS CONTAINER=70f5b6174b88;
                      BFF IMAGE=8c87aefe1e66 (não rebuildada — sem necessidade);
                      imagem nova inspecionada em ambiente controlado via
                      create_mcp_server(): CATALOG=4, 5 tools, entities e
                      analyses corretos; docker compose config OK; conjunto
                      mínimo = supplies-mcp apenas.
D4 PRODUCTION DEPLOY: PASS — host operador@192.168.1.237 (srv-api),
                      repo /home/operador/projetos/delpi-central já em
                      ac1bb7d765 (pull concorrente); build supplies-mcp →
                      f6414a1e41db; up -d --no-deps supplies-mcp →
                      container 10d70d4f6557, healthy, restarts=0, logs sem
                      erros; /healthz 200; nenhum outro container tocado;
                      nenhum reset --hard; nenhuma alteração em secrets/
                      OAuth scopes/Keycloak client.
D5 OAUTH/PUBLIC:      PASS — resource metadata HTTP 200 (resource + AS
                      keycloak + scopes corretos); initialize sem Bearer →
                      401 com WWW-Authenticate Bearer realm="suri-mcp" +
                      resource_metadata + scopes + invalid_token; token de
                      audience/realm errada (master/admin-cli) → 401; BFF
                      /health 200 preservada; TLS OK; gateway encaminha ao
                      ASGI MCP, não ao Flask.
D6 MCP SMOKE:         PARCIAL — surface provada no container em execução:
                      tools/list = 5 tools, read.entity=[purchase_orders,
                      suppliers, postal_codes], analyze.analysis=
                      [purchase_orders_summary, supplier_creation_preview];
                      negativos ao vivo: CEP inválido → 422, catalog fora da
                      allowlist → 422 com 14 kinds; conectividade S2S provada
                      (requisição alcançou api-delpi); token de usuário fake
                      rejeitado upstream → fail-closed correto.
                      CHAMADAS AUTENTICADAS POR USUÁRIO (CEP/CNPJ/ficha/
                      catalogs/preview positivos): INCONCLUSIVE — mcp-supplies
                      não permite direct grants; fluxo OAuth user-delegated
                      exige ação interativa do usuário. Service tokens não
                      foram usados para simular usuário.
D7 CHATGPT:           SERVER_CATALOG_V4=PASS; SERVER_TOOL_SCHEMAS_V4=PASS;
                      CHATGPT_CATALOG_V4=PENDING; CHATGPT_AUTHENTICATED_SMOKE=
                      PENDING — atualização aditiva (mesmas 5 tools, schemas
                      ampliados); usuário deve recarregar ferramentas no
                      conector caso o ChatGPT cacheie schemas V3.
D8 DOCUMENTATION:     PASS — este aceite; matriz reconciliada
                      (READ 34 linhas, WRITE 11, denominador 45 consistente);
                      indicadores preservados (14/45 = 31.1%, sem promoção
                      artificial a RUNTIME_PROVEN além do comprovado).
```

## Deployment

```text
PREVIOUS MCP IMAGE:   infra-supplies-mcp c622ed1b33de (V3 — retida p/ rollback)
NEW MCP IMAGE:        infra-supplies-mcp f6414a1e41db (V4)
PREVIOUS CONTAINER:   delpi-supplies-mcp 70f5b6174b88
NEW CONTAINER:        delpi-supplies-mcp 10d70d4f6557 (healthy, restarts=0)
PREVIOUS BFF IMAGE:   infra-supplies-api 8c87aefe1e66
NEW BFF IMAGE:        — (não rebuildada; mudança compartilhada é
                      refactor-neutro e BFF não precisava de rebuild)
CONTAINERS CHANGED:   delpi-supplies-mcp apenas
MIGRATIONS:           nenhuma nova (V005 permanece; zero migration adicional)
```

## Capacidades em produção

```text
CATALOG_VERSION:            4
TOOL COUNT:                 5 (get_context, read, analyze, knowledge, execute)
READ ENTITIES:              purchase_orders, suppliers, postal_codes
READ ACTIONS (suppliers):   search, get, catalogs, search_by_tax_id, existing,
                            operations, integration_status (manage-only)
READ ACTIONS (postal):      lookup
ANALYZE:                    purchase_orders_summary, supplier_creation_preview
EXECUTE (preservado):       suppliers create|update — sem delete
CEP LOOKUP:                 contrato+negativo+S2S PASS; usuário-auth INCONCLUSIVE
CNPJ LOOKUP:                contrato PASS (testes); usuário-auth INCONCLUSIVE
SUPPLIER SEARCH/360/...:    contrato PASS; usuário-auth INCONCLUSIVE
CREATION PREVIEW:           contrato PASS (write_enabled=false, read-only);
                            usuário-auth INCONCLUSIVE
OAUTH:                      PASS (metadata+challenge+wrong-aud)
AUTHZ POSITIVE:             PASS (suíte: access→reads, manage→integration_status)
AUTHZ NEGATIVE:             PASS (anônimo 401, sem access 403, sem manage 403,
                            wrong-aud 401 — negative ao vivo inclusos)
S2S:                        PASS (gateway correto, conectividade provada,
                            rejeição upstream propagada fail-closed)
READ_ONLY GUARANTEE:        PASS (zero write verbs; preview write_enabled=false)
ROLLBACK:                   READY (imagem c622ed1b33de retida + recreate;
                            zero migrations novas; git revertável)
```

## Resíduos / próximos passos

```text
FACTS PROVEN:     catálogo v4 publicado em produção, 5 tools, superfície
                  suppliers/postal/preview no container em execução, OAuth
                  preservado, negatives ao vivo, S2S conectado, regressão
                  V3 intacta, BFF preservada, rollback pronto
TO_INVENTORY:     smoke autenticado por usuário real (INCONCLUSIVE — requer
                  OAuth user-delegated no ChatGPT); recarregar tools do
                  conector ChatGPT; homologar leitura real de fornecedores/
                  CEP/CNPJ com usuário autorizado
EXECUTION_DRIFT:  nenhum
UNRESOLVED:       CHATGPT_CATALOG_V4, CHATGPT_AUTHENTICATED_SMOKE (ação do
                  usuário)
POSTCONDITION:    catálogo v4 em produção ≠ chamada autenticada de usuário
                  provada — distinção registrada
NEXT STEP:        usuário recarrega ferramentas no conector SURI → smoke
                  autenticado G1 → aceite arquitetural → autorizar próximo
                  lote (G2)
```

**STATUS FINAL: `ACCEPT_WITH_RESIDUAL`** — deploy produtivo V4 G1 concluído com sucesso e evidência; resíduo = smoke autenticado por usuário (depende de OAuth interativo) e refresh de ferramentas no ChatGPT.
