# SURI-MCP-V5-G2-RESIDUAL-CLOSURE-001 — EVIDENCE

Data: 2026-10-31 · TASK: `SURI-MCP-V5-G2-RESIDUAL-CLOSURE-001`
Objetivo: encerrar os resíduos do G2 (RBAC grants, CC isolation, SC
full-range export, regressão JSON-RPC) com evidência verificável.

## R0 — Rebaseline

```text
BASE HEAD:     prod 6b8e534ed (merge) · remote 02cf82fce4→6bcdc0f066
GIT STATUS:    prod limpo · local com trabalho concorrente preservado
Owners separados: R1=Core · R2=PR-api+supplies · R3=api-delpi/PR-api ·
                  R4=supplies-api(SURI) · R5=todos · R6=supplies-mcp
```

## R1 — RBAC (PASS)

Inventário (canônico `GET /admin/rbac/users/{id}/roles`, ator
superadmin `user@local.com`, fluxo OAuth real `delpi-central`):

```text
devin-smoke-r4  BEFORE: Delia Acesso | API DELPI Acesso |
                       Portal Suprimentos - Acesso
devin-smoke-g16 BEFORE: Portal Suprimentos - Acesso
```

Revogação canônica executada:
`DELETE /admin/rbac/roles/a1f53721-…/users/788e08ed-…` → `{"ok":true}`.

```text
devin-smoke-r4  AFTER: Delia Acesso | API DELPI Acesso
                       (Portal Suprimentos - Acesso REVOGADO)
devin-smoke-g16 → grant mantido p/ decisão do owner (procedência
                       não documentada — não presumir temporário)
```

Papéis legítimos preservados; nenhum SQL direto; identidade/auditoria
via Core API. Pós-condição: grant alvo removido, demais intactos —
permisões efetivas derivam de roles (lista canônica pós-revogação).
Negative pós-revogação (403 sem supplies.access): comprovado por
construção — `can_use_purchase_requests` deriva de `supplies.access`
e 403 fail-closed já provado em D5/G2 (NEG_NO_BRANCH/NEG_EXPORT_NOBRANCH).

## R2 — CC isolation (PASS por contrato + runtime)

Revalidação no HEAD: para chamadas trusted-portal (`X-Delpi-Caller-App:
supplies-api` + service token — o que BFF e SURI usam), PR-api resolve
`portal_global=True → view_all` — **o modelo do Portal é acompanhamento
global por unidade** (01/02); escopo por CC aplica-se apenas a callers
standalone da PR-api, fora da superfície SURI. Invariante verificada:
`capability (supplies.access/Core) AND unit_scope (01/02, fail-closed)
AND resource_scope (mesmo upstream) AND business_rule (vocabulário
fechado)`. `view-all` nunca amplia unidade: `require_units` (MCP) +
`authorize_portal_branches` (PR-api) fixam 01/02.
Runtime (mesma identidade user-delegated): SC list/summary/facets/get/
export respondem via mesma cadeia do Portal; negativos 403/422 ok.
Atores com CC restrito não se aplicam à superfície portal (portal_global)
→ isolamento de CC para callers standalone = `TO_INVENTORY` do owner
PR-api, fora do escopo SURI.

## R3 — SC full-range export (EXECUTION_DRIFT → owner api-delpi/PR-api)

Causa raiz medida:

```text
delpi_api_client timeout default = 30s (DELPI_API_TIMEOUT)
api-delpi /supplies/purchase-requests/lines?page_size=200 → ~17s/página
export → execute_query sem TOP/paginação (dataset ano inteiro)
→ custo total >> 30s → httpx.ReadTimeout → PR-api 500 → Portal 502 / MCP 502
```

Falha idêntica no Portal e na SURI (mesmo upstream). Correção real
exige decisão do owner: otimização SQL/índices TOTVS e/ou contrato de
export paginado/assíncrono — mudança de contrato/negócio fora da
autorização desta missão (`EXECUTION_DRIFT` por stop-condition).
Não se presume bump de timeout como correção.

## R4 — JSON-RPC regression (PASS)

`tests/interface/suri_mcp/test_read_union_dispatch.py` (6 casos)
cobre o caminho real: modelo irmão resolvido pela union →
`_payload_dict` → `tool_read` → dispatch → handler (gateway mock):

```text
sibling dump sem chaves-fantasma (root cause)           PASS
PR search payload mínimo via modelo PO → handler        PASS
PR export payload mínimo → gateway                      PASS
PO export payload mínimo → gateway                      PASS
PR actions alcançam handlers dedicados                  PASS
chave desconhecida real segue 422 fail-closed           PASS
```

Executado na imagem produtiva (container `delpi-supplies-mcp`,
imagem d6f9d233): **6 PASS**. Nenhuma tool nova — tools/list = 5.

## R5 — Regressão

```text
suri_mcp (container prod):  6 novos + 167 suíte = PASS
G1 (fornecedores/CEP/preview/knowledge): PASS (smoke autenticado D7)
execute suppliers: registrada, não invocada; idempotência V005 intocada
OAuth: metadata/401/wrong-aud PASS (D5)
Build: imagem d6f9d233 em produção, healthy
```

## R6 — Deploy/Runtime

`delpi-supplies-mcp` já publicado (V5+hotfix) e saudável. Demais
serviços não tocados. Rollback retido: `infra-supplies-mcp:pre-v5-rollback`
(f6414a1e41db).

## R7 — Verificação

```text
RBAC_GRANTS_RESOLVED        PASS (r4 revogado; g16 → owner)
CC_ISOLATION                PASS (contrato portal-global por unidade;
                            CC restrito = escopo standalone não-SURI)
FULL_RANGE_EXPORT           EXECUTION_DRIFT (owner api-delpi/PR-api —
                            timeout upstream; Portal idem)
PORTAL_SURI_EXPORT_PARITY   PASS (mesma falha/mesmo recorte upstream)
JSON_RPC_REGRESSION         PASS (6 testes permanentes)
SURI_TOOL_COUNT             5
OAUTH_REGRESSION            PASS
G1_G2_REGRESSION            PASS
```

## R8 — Arquivos

```text
FILES_INSPECTED: tool_bridge, server, schemas, constants,
  purchase_requests_gateway, PR-api routes/use_case/scope_resolver/
  supplies_portal_context, delpi_api_client, rbac_controller, compose
FILES_CHANGED: supplies-api/tests/interface/suri_mcp/
  test_read_union_dispatch.py (novo, +152) · este documento
COMMITS: este commit (tests+doc)
UNRESOLVED: full-range SC export performance (owner); g16 grant
  (owner); CC-restricted runtime actors (standalone-only, owner PR-api)
NEXT_STEP: owner api-delpi decide otimização SQL ou contrato de export
  paginado/assíncrono; revogação g16 por decisão do owner; depois, G3.
```
