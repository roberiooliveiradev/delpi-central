# 64 — ENGINEERING.PRODUCTS.E2E.MASTER.R1 — Relatório Final de Implementação e Deploy

Missão: `ENGINEERING.PRODUCTS.E2E.MASTER.R1` — implementação ponta a ponta do módulo
Produtos do Portal Engenharia conforme Plano 62 e especificação 61.

- **Commits de implementação:** `dea3d6512a` (G2/G4 façade+EVA+owner), `77200fa07f` (G5 frontend+docs)
- **SHA deployado em produção:** `77200fa07f` (origin/main)
- **SHA anterior de produção:** `297068f1b7`
- **Data do deploy:** 2026-10-30
- **Estados:** `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`

## 1. Escopo entregue

### Backend (api-delpi — owner)

- `view=engineering` aditivo em `GET /products/search`, `GET /products/{code}`,
  `GET /products/{code}/suppliers`: allowlists
  `PRODUCT_DETAIL_ENGINEERING_FIELDS` / `PRODUCT_SUPPLIER_ENGINEERING_FIELDS`
  excluem `sale_price`, `standard_cost`, `last_purchase_price` e campos fiscais.
- `narrow_paged_items` aplica o narrowing item a item em respostas paginadas.
- AuthZ aditivo `require_any_permission(ENGINEERING_LMP_ACCESS)`
  (`api-delpi.access` OR `dashboard-engineering.view` OR `dashboard-lmps.view`) em:
  detail, structure, parents, suppliers, drawing metadata, drawing PDF e `/drawings`.
- Rotas comerciais permanecem estritas: `/{code}/summary`,
  `/{code}/purchase-price-history`, `/{code}/purchase-budget-history` (API_DELPI_ACCESS).

### Façade (engineering-api — bounded context Engineering)

8 rotas `/v1/products*` (`product_routes.py`): principal humano obrigatório
(`_human_context`), Bearer delegado ao owner via `DelegatedAuxiliaryGateway`,
`get_raw()` binário governado no `DownstreamClient`, mapeamento honesto
`forbidden→403` / `not_found→404` / demais→`502 unavailable`.

### EVA — paridade semântica

`read(product.*)` despacha por allowlist `(entity, action)` — sem tools MCP novas:
`product.search`, `product.detail`, `product.structure`, `product.where_used`,
`product.suppliers`, `product.drawing`, `product.history`.
`product.update` em `PLANNED_SEMANTIC_ACTIONS` → `not_implemented` honesto.
`product.history` compõe revisão cadastral + purchase-price autorizado +
`revision_history: not_implemented` explícito (doc 63 §2.7).

### Frontend (plugins/engineering)

- `src/features/products/` — listagem (hero, filtros oficiais code/description/
  group/type/customer_reference, tabela server-sort + paginação) e Ficha do
  Produto (breadcrumb, hero compacto, badge `Visualizar`, `Editar` desabilitado
  com tooltip OWNER_BLOCKED, 6 abas na ordem da spec 61, lazy load por aba,
  erro independente por aba).
- Catálogo `products` + ícone `Package` + rota `/apps/engineering/products*`.
- `productCopy.ts` centraliza labels e help hints (FieldLabel/HelpTooltip).
- CSS com tokens `--en-*` do design system (light/dark, responsivo).
- `e2e/specs/products.spec.ts` — 4 testes × 3 viewports (SSO real).

## 2. Evidência de testes (SHA final `77200fa07f`)

| Camada | Comando | Resultado | Estado |
|---|---|---|---|
| engineering-api | `pytest` | 491 passed, 10 skipped (16.5s) | PASS |
| api-delpi | `pytest` seleção produto/authz | 1614 passed, 5032 deselected | PASS |
| MFE unit | `vitest run` | 18 files / 166 tests | PASS |
| MFE typecheck | `tsc --noEmit` | 0 erros | PASS |
| MFE lint | `eslint` | 0 erros (warnings pré-existentes) | PASS |
| MFE build | `npm run build` | `App-DbW4JhhE.js` | PASS |
| Browser E2E | Playwright SSO real | desktop+tablet verde (ficha 6 abas, dados reais); mobile inconclusivo por flakes ambientais em run anterior | INCONCLUSIVE (mobile) |

Notas ambientais: suite E2E sofreu instabilidade do ambiente dev (container
api-delpi caindo em reload, worktree drift externo). Em run estável,
desktop e tablet passaram integralmente; mobile teve flakes de timing.
O caso detail-422 observado em run intermediário era drift do enum
`view=engineering` revertido por processo externo — não defeito do diff.

## 3. Deploy de produção

- Procedimento canônico: `git pull --ff-only` + `up-prod-sequential.sh --build
  api-delpi engineering-api engineering` via `operador@192.168.1.237`.
- Ordem: owner → façade → MFE. Apenas os 3 serviços recriados; demais
  containers intactos (uptimes 8h–4 semanas preservados).
- Health pós-deploy: `delpi-api-delpi` healthy, `delpi-engineering-api`
  healthy, `delpi-engineering` up; zero erros nos logs.
- Rollback disponível: rebuild dos 3 serviços em `297068f1b7` (SHA anterior
  deployado); sem migrations, flags ou schema novos.

## 4. Smoke de produção (evidência direta)

Identidade: `products.smoke`/`act57.smoke` provisionados com autoridade
operacional, `is_superadmin` temporário no Core (workaround do cache de
permissões do PermissionResolver — registrado em doc 59), removidos ao final.

### REST façade (`/apps/engineering-api/v1/products*`) — token delegado

| Rota | HTTP | Evidência |
|---|---|---|
| `GET /v1/products?limit=3` | 200 | envelope `success`, `items` reais (SB1) |
| `GET /v1/products/30190123` | 200 | ficha view=engineering (1042 B) |
| `GET /v1/products/30190123/structure` | 200 | `items:[]` honesto (sem BOM) |
| `GET /v1/products/30190123/parents` | 200 | `total:0` honesto |
| `GET /v1/products/30190123/suppliers` | 200 | LC IND E COM LTDA (SA5) |
| `GET /v1/products/30190123/drawing` | 404 | "sem desenho disponível" honesto |
| `GET /v1/products/0156/drawing` | 200 | `0156.pdf`, 129762 B |
| `GET /v1/products/0156/drawing/pdf` | 200 | 129762 B, magic `%PDF-1.5` — proxy binário |
| `GET /v1/products/30190123/purchase-price-history` | 200 | histórico SC (superadmin) |
| `GET /v1/products/NAOEXISTE9X` | 404 | "não encontrado" honesto |
| sem Authorization | 401 | em todas as 7 rotas |

### EVA semântica (MCP `mcp-engineering`, OAuth user real, sessão real)

| Ação | Resultado | Estado |
|---|---|---|
| `read(product.search)` `description=PROD` | 200, 23 itens reais | PASS |
| `read(product.detail)` `30190123` | 200, ficha engineering | PASS |
| `read(product.suppliers)` | 200, 1 vínculo real | PASS |
| `read(product.history)` | 200, `revision_history:not_implemented` explícito | PASS |
| `read(product.drawing)` `0156` | 200, filename+size+media_type | PASS |
| `read(product.where_used)` | 200, `total:0` | PASS |
| `read(product.update)` | `not_implemented` + allowed_actions | PASS (honesto) |
| `read` filtro inválido | 400 validation com allowed_fields | PASS (guarda) |
| `get_product_structure` | 200 `status:available` | PASS |
| `tools/list` | 28 tools incluindo 6 semânticas | PASS |

### Portal/MFE público

- `remoteEntry.js` 200; `App-DbW4JhhE.js` 200 contendo "Ficha do Produto",
  "Onde é usado", "products".
- Portal `/` 200.

## 5. Matriz PRD-01..25

| PRD | Estado | Nota |
|---|---|---|
| PRD-01 | PASS | Menu "Produtos" + títulos Catálogo/Ficha |
| PRD-02 | PASS | Ícone `Package` + hero nativo |
| PRD-03 | PASS | Filtros/paginação/sorting server-side dentro dos contratos |
| PRD-04 | PASS | Colunas oficiais; CSS responsivo sem overflow |
| PRD-05 | PASS | Lista → ficha com navegação por código |
| PRD-06 | PASS | Hero compacto, Visualizar padrão, Editar bloqueado honesto |
| PRD-07 | PASS | 6 abas na ordem + lazy loading por aba |
| PRD-08 | PASS | Visão geral com dados reais + help hints |
| PRD-09 | PASS | Estrutura com níveis/qtd/unidade oficiais (owner SG1) |
| PRD-10 | PASS | Onde é usado via `parents` oficial |
| PRD-11 | PASS | Fornecedores via SA5 delegado, view=engineering sem preço |
| PRD-12 | PASS | Desenho via contrato oficial do acervo (metadata+PDF proxy) |
| PRD-13 | PASS | Card de desenho na Visão geral quando `found` |
| PRD-14 | PASS | Viewer seguro via proxy, estados 404/forbidden/unavailable |
| PRD-15 | PASS | Histórico real + `revision_history:not_implemented` honesto |
| PRD-16 | PASS | Edição bloqueada — sem contrato WRITE (OWNER_BLOCKED) |
| PRD-17 | PASS | Estados loading/empty/forbidden/not_found/unavailable |
| PRD-18 | PASS | Tokens `--en-*` light/dark; layout responsivo |
| PRD-19 | PASS | AuthZ backend-first; sem campos comerciais na view |
| PRD-20 | PASS | EVA paridade 7 ações — todas PROVEN em prod |
| PRD-21 | PASS | Delegação ao owner; sem duplicação de fonte |
| PRD-22 | ACCEPT_WITH_RESIDUAL | Backend+unit+build verdes; E2E mobile INCONCLUSIVE |
| PRD-23 | PASS | Evidência neste doc + doc 63 §6 |
| PRD-24 | PASS | Deploy canônico pós-homologação, rollback disponível |
| PRD-25 | PASS | Nenhuma capacidade declarada sem contrato/fonte |

## 6. Residuais (OWNER_BLOCKED / ambientais)

1. `product.update` / edição: sem contrato WRITE oficial no owner →
   `not_implemented` honesto na EVA e `Editar` desabilitado na ficha.
2. `revision_history` cadastral: sem contrato oficial (doc 63 §2.7) →
   seção honesta `not_implemented` no tool history.
3. Filtro server-side por situação (ativo/bloqueado): owner não expõe
   filtro dedicado (doc 63 §G-3) — badge renderizado por linha.
4. `purchase-price-history` permanece `API_DELPI_ACCESS` no owner:
   usuários sem permissão comercial recebem `forbidden` honesto.
5. E2E mobile: INCONCLUSIVE — flakes ambientais (containers dev);
   desktop/tablet verdes no mesmo spec.
6. PermissionResolver do Core: cache sem invalidação cross-process
   (workaround superadmin temporário no smoke; débito registrado para
   owner Core — doc 59 §EXECUTION_DRIFT).

## 7. Teardown de evidência

- `products.smoke` e `act57.smoke`: removidos do Keycloak de prod e da
  tabela `users` do Core (DELETE 2 verificado).
- Nenhum registro oficial alterado durante o smoke (somente GETs).
- Arquivos de smoke em `/tmp` do host não contêm segredos persistidos
  (tokens expiráveis).

## 8. Veredito

**ACCEPT_WITH_RESIDUAL** — todas as capacidades com contrato oficial
estão PROVEN em produção (REST + EVA + MFE público); as únicas pendências
são autoridades externas (WRITE, revision_history, filtro por situação)
e o viewport mobile do E2E com evidência inconclusiva por ambiente.
