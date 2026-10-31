# SURI-MCP-V4-G2-DEPLOY-001 — Aceite de Deploy Produtivo

Data: 2026-10-31
TASK: `SURI-MCP-V4-G2-DEPLOY-001`
Objetivo: publicar a SURI V5 em produção, homologar capacidades G2 de
Solicitações (SC) e Pedidos de Compra (PC), preservar a V4 G1 e registrar
evidências reais.

## 1. Baseline (D0)

```text
BASE HEAD (local):      2ff4193b8ca1d8d18dc40898feaddff2a3c326f6 (divergente/velho — não era fonte)
SOURCE SHA G2:          665b7ee441c6ba51a2a96cbfc97cd762f5faec3a (ancestral de origin/main)
ORIGIN MAIN (pré):      7086824a1d — supplies-api/infra/purchase-requests-api idênticos ao G2
FINAL HEAD (prod):      c92de81741a3d968346ff47ca6ba3a8d4738a776 (merge)
PRODUCTION HEAD (pré):  100f31c1f2498c34f9f889090f90f20f6d03e46a (commit local public-hub preservado)
GIT STATUS local:       140 arquivos sujos de trabalho concorrente (não tocados;
                        staged removia REDIS_URL do supplies-mcp — não commitado, não chegou a prod)
GIT STATUS prod:        limpo; main ahead 1 (commit local preservado via merge)
CURRENT MCP IMAGE:      infra-supplies-mcp:latest = sha256:f6414a1e41db (retida como rollback tag)
CURRENT MCP CONTAINER:  7cbf41558f8a → substituído
CURRENT CATALOG:        v4 (5 tools; read: postal_codes, purchase_orders, suppliers)
Commits pós-G2:         nenhum tocou supplies-api/infra/purchase-requests-api até o deploy.
```

## 2. D1 — Segurança e contratos (PASS)

- **AuthZ por ação (tool_bridge.py):** `can_use_purchase_requests` e
  `can_export_purchase_requests` → `supplies.access` resolvido da Core `/me`
  por chamada (`resolve_effective_user`); `require_units`/`require_unit`
  fail-closed (unidades 01/02; lista vazia → 403; branch fora do produto →
  erro upstream). Principais de serviço rejeitados (`principal_type!=user`
  → 403). Nenhuma permissão nova, nenhum bypass.
- **Cadeia de escopo (D1.2):** MCP → `PurchaseRequestsGateway` (Bearer do
  usuário + `X-Delpi-Caller-App: supplies-api` + service token interno) →
  purchase-requests-api contexto portal ("global accompaniment") →
  `authorize_portal_branches` (escopo de produto 01/02) + resolução de CC
  por usuário (escopo explícito fora → `PermissionError`/403; vazio →
  fechado). Visibilidade **estruturalmente idêntica ao Portal** — mesmo
  gateway/headers/upstream; MCP não amplia nada. Facetas e export usam o
  mesmo recorte. `view-all` não amplia unidade (camada MCP limita 01/02).
- **Export (D1.3):** `data.items` + `data.export={format:"json",row_count,
  portal_file_formats}` — DECISION-G1 implementada exatamente; sem
  binário/base64/link; branch não-vazio fail-closed; timeout configurado
  (`PURCHASE_REQUESTS_API_TIMEOUT=90`, `DELPI_API_TIMEOUT=60` em prod).
  **Residual:** sem cap absoluto de linhas — mesmo contrato do export do
  Portal (DECISION-G1 congelada, review ACCEPT_WITH_RESIDUAL). Comprovado
  em runtime que dataset completo estoura timeout upstream (ver D6.4).

## 3. D2 — Regressão e build (PASS)

Executado em worktree limpo de `origin/main` (fonte real de deploy):

```text
pytest tests/interface/suri_mcp  → 167 PASS, 0 FAIL
pytest tests (supplies-api)      → 832 PASS / 24 SKIPPED (env-gated: Redis/PG), 0 FAIL
```

Nota: baseline documental G2 citava 888 PASS — divergência de contagem na
doc (código supplies idêntico entre SHA G2 e origin/main); zero falhas.
`create_mcp_server()` inspecionado: `CATALOG_VERSION=5`, `TOOL_COUNT=5`,
read entities = purchase_orders/purchase_requests/suppliers/postal_codes,
execute = suppliers.create/update, analysis = purchase_orders_summary +
supplier_creation_preview. Build de imagem real feito em produção (D4).

## 4. D3 — Prep e rollback (PASS)

- Host confirmado: `operador@192.168.1.237` (`srv-api`), repo
  `/home/operador/projetos/delpi-central`, tree limpa, main ahead 1
  (commit local `public-hub` — preservado por merge `--no-rebase`).
- `docker compose config` válido; `REDIS_URL`/`DELPI_REDIS_URL` configurado;
  DNS `delpi-purchase-requests-api` resolve do container MCP; todos os
  containers Up.
- Escopo mínimo confirmado: rebuild apenas `supplies-mcp` (G2 só toca
  `app/interfaces/mcp/*`; BFF Flask não importa esse módulo → imagem BFF
  preservada).
- Rollback preparado: imagem anterior taggeada
  `infra-supplies-mcp:pre-v5-rollback` (f6414a1e41db). Rollback =
  `docker tag infra-supplies-mcp:pre-v5-rollback infra-supplies-mcp:latest`
  + `docker compose up -d --no-deps supplies-mcp` → restaura V4 (OAuth,
  catálogo v4, fornecedores/CEP homologados).

## 5. D4 — Deploy (PASS)

```text
git pull --no-rebase  → merge limpo (HEAD c92de81741a3)
docker compose build supplies-mcp → imagem 29ff12a5f7b2 (catalog v5 in-image)
docker compose up -d --no-deps supplies-mcp → container 1d6aecc7d75e healthy
+ hotfix: commit e1c3c529ce (pushed para main) → rebuild imagem d6f9d233f3c6
  → container final healthy, RestartCount=0, logs limpos
PREVIOUS_IMAGE:  infra-supplies-mcp:latest = f6414a1e41db (rollback tag)
NEW_IMAGE:       infra-supplies-mcp:latest = d6f9d233f3c6
PREVIOUS_BFF:    infra-supplies-api = 8c87aefe1e66 (container 7541c4052de8 — preservado)
CONTAINERS_CHANGED: delpi-supplies-mcp apenas
Serviços não tocados: keycloak, core-api, api-delpi, purchase-requests-api,
  supplies-api (BFF), gateway, demais MCPs — todos seguem saudáveis.
```

## 6. D5 — OAuth/MCP smoke (PASS)

```text
GET /apps/supplies-api/.well-known/oauth-protected-resource → 200
  (resource=MCP URL; authorization_servers=realm delpi; scopes corretos)
POST /mcp sem Bearer → 401 + WWW-Authenticate correto
  (realm="suri-mcp", resource_metadata, scope="openid profile email mcp:tools")
Bearer inválido → 401
Token KC real aud=[delpi-central,...] (service-account delpi-core-admin)
  → 401 (isolamento de audience)
/healthz interno → 200; container healthy; sem restart loop
SERVER_TOOLS_LIST (MCP tools/list autenticado) → 5 tools
SERVER_CATALOG (in-container) → v5, read entities completos
USER_AUTHENTICATED_CALL → executado (D6/D7 abaixo)
CHATGPT_DISCOVERY → não executado nesta sessão (requer conector;
  catalog v5 provado via transport MCP real — descoberta pelo conector
  consome o mesmo catalog)
```

## 7. D6 — Homologação autenticada G2 (identidade user@local.com, superadmin,
OAuth auth-code+PKCE real via client `mcp-supplies`)

```text
SC_SEARCH       200  total=859 items=5 paginado        PASS
SC_SUMMARY      200  stage_counts reais (7 estágios)   PASS
SC_REQUESTERS   200  19 requesters                    PASS
SC_COST_CENTERS 200  53 cost centers                  PASS
SC_GET          200  detalhe real (SC 01/179309)       PASS
SC_EXPORT       200  narrow request_number=179309:
                     export={format:json,row_count:1,
                     portal_file_formats:[csv,xlsx]}   PASS (scoped)
PO_SEARCH       200  total=343 items=5                PASS
PO_GET          200  pedido real                      PASS
PO_EXPORT       200  export={format:json,row_count:343,
                     portal_file_formats:[xlsx]}       PASS
UNIT_SCOPE      PASS (branch obrigatória; sem branch → 403; unidade
                     inválida "99" → 422 upstream "Filial inválida.")
CC_SCOPE        INCONCLUSIVE (identidade superadmin/global accompaniment;
                     sem ator com escopo restrito no ambiente)
RESOURCE_SCOPE  PASS por construção (mesmo upstream do Portal — veja D1.2)
NEGATIVOS:      filtro desconhecido → rejeição union (422)
                página inválida (page=0) → 422
                entidade desconhecida → 422 Literal
                ação desconhecida → 422 Literal
                export sem branch → 403 Forbidden
                identidade inválida/aud errada → 401 (D5)
```

### D6.4 — Export Portal × SURI (INCONCLUSIVE para conteúdo / PROVEN para contrato)

- SURI `read(purchase_requests, export)` narrow → dataset JSON correto.
- Export full-range (branch=01, ano inteiro): MCP → PR-api → api-delpi
- SURI `read(purchase_requests, export)` narrow → dataset JSON correto.
- Export full-range (branch=01, ano inteiro): MCP → PR-api → api-delpi
  `/lines/export` estoura `httpx.ReadTimeout` → PR-api 500 → MCP 502
  honesto. **Portal BFF `GET /purchase-requests/export` falha
  identicamente** (502) — bug pré-existente do owner
  (purchase-requests-api/api-delpi), fora do escopo G2.
- PO export: dataset coerente com o recorte (343 linhas), mesmo escopo.
- Classificação: `EXECUTION_DRIFT` residual do owner PR-api/api-delpi —
  performance/timeout do `/lines/export` em ranges amplos; encaminhar ao
  owner de dados/contratos. MCP não amplia nem mascara o erro.

## 8. D7 — Regressão V4 G1 (PASS)

```text
read(suppliers,search)              200  total=6 items=3   PASS
read(suppliers,get)                 200  ficha real         PASS
read(suppliers,search_by_tax_id)    200  match exato        PASS
read(suppliers,catalogs)            200  34 itens           PASS
analyze(supplier_creation_preview)  200  preview read-only  PASS
knowledge(search)                   200  8 itens            PASS
postal_codes(lookup)                não re-executado nesta rodada
                                    (PROVEN no G1 recovery; código intocado)
execute(suppliers.create|update)    registrada (tools/list); não invocada —
                                    zero escritas nesta missão
Redis: REDIS_URL=CONFIGURED no container novo
OAuth Protheus / S2S: sem regressão observada
```

## 9. D8 — Residual RBAC G1 (EXECUTION_DRIFT → owner Core)

Verificado (read-only, `delpi-postgres-core`):

```text
devin-smoke-r4 → "Portal Suprimentos - Acesso"  PRESENTE (grant G1 não revogado)
devin-smoke-r4 → "Delia Acesso", "API DELPI Acesso" (outros grants)
devin-smoke-g16 → "Portal Suprimentos - Acesso" (outra identidade smoke
                 com o mesmo papel — flag adicional p/ owner)
```

Não existe ator com `rbac.manage`/`roles.manage` via papel; revogação
canônica exige superadmin (engenharia@/dennis@/ti@/inovacao@/fabiano@)
via `DELETE /admin/rbac/roles/<role_id>/users/<user_id>` ou UI Gestão de
Acessos, depois verificar `/me`. **Sem SQL direto executado.** Não
bloqueia o G2 (residual independente, sem risco ativo material novo).

## 10. Correção de gate aplicada (diff produtivo)

`supplies-api/app/interfaces/mcp/tool_bridge.py` — `_payload_dict` agora
usa `model_dump(exclude_none=True, exclude_unset=True)`. Sem isso, a union
de `filters` do `read` injetava defaults de modelos irmãos
(`late_only`/`page`/`page_size` de `PurchaseOrder*Filters`) como chaves
fantasma e TODAS as ações `purchase_requests` + `purchase_orders.export`
falhavam em runtime (422 "Unknown filters"). Commit `e1c3c529ce` em main.

Gap de teste identificado: a suíte chama handlers com dicts — o caminho
schema→union→dispatch não era coberto. Recomendado teste de integração do
nível tool (entrada JSON-RPC → dispatch) como follow-up.

## 11. Estado final

```text
SURI_V5_DEPLOYED          = PASS
SURI_CATALOG_VERSION      = 5 (transport + in-container)
SURI_TOOL_COUNT           = 5
PURCHASE_REQUESTS_*       = PASS (search/summary/requesters/cost_centers/get/export-scoped)
PURCHASE_ORDERS_*         = PASS (search/get/export)
UNIT_SCOPE                = PASS
CC_SCOPE                  = INCONCLUSIVE (sem ator com escopo restrito)
RESOURCE_SCOPE            = PASS (paridade estrutural com Portal)
EXPORT_SECURITY           = PASS com residual (timeout upstream em range amplo — owner)
SURI_G1_REGRESSION        = PASS
OAUTH                     = PASS
MCP_HEALTH                = PASS
BFF_HEALTH                = PASS
DOCUMENTATION             = este documento + matriz atualizada
ROLLBACK_READY            = YES (imagem V4 retida taggeada)
```

## 12. Residual e próximo passo

- `EXECUTION_DRIFT` (owner PR-api/api-delpi): `GET /lines/export` timeout
  em ranges amplos — afeta Portal igualmente; investigar SQL/paginação do
  dataset de export.
- `EXECUTION_DRIFT` (owner Core/Segurança): revogar grant
  `devin-smoke-r4 → Portal Suprimentos - Acesso` (e revisar
  `devin-smoke-g16`) pelo mecanismo canônico; verificar `/me` após.
- `TO_INVENTORY`: teste automatizado do caminho JSON-RPC→union→dispatch
  (evitaria o bug do gate); `postal_codes` re-smoke; isolamento de CC com
  ator com escopo restrito (requer identidade autorizada).
- `CHATGPT_DISCOVERY`: confirmação da descoberta no conector pelo reviewer.
- Próximo gate proposto: G3 somente após fechamento dos residuais.
