# 65 — ENGINEERING.PRODUCTS.UX.ROUTING.FIX.R1 — Runtime Regression, Reactive Filters & Production Evidence

**Status:** DEPLOYED_PROD — ACCEPT_WITH_RESIDUAL
**Executado:** 2026-10-30
**Executor:** Devin (EVA Coordination)

---

## 1. Escopo da missão

Correção dos defeitos funcionais do módulo Produtos do Portal Engenharia evidenciados em produção:

- Página preta na Ficha do Produto (`Uncaught TypeError: Cannot read properties of undefined (reading 'length')`).
- Abas sem endereçamento por URL, sem deep link e sem histórico confiável.
- Filtros Grupo/Tipo sem multiselect oficial.
- Busca dependente de ação manual.
- Ausência de botão Limpar do design system.
- Descrições de produto apresentadas como `#`/`###` e campos vazios inconsistentes.

## 2. Causa-raiz (GATE A)

| Item | Evidência |
|---|---|
| Envelope delegado | `GET /v1/products/{code}/structure` retorna `{status:"available", data:{items:[...]}}` — rota pré-existente de LMP.G5 — enquanto `parents`/`suppliers` retornam o payload plano. |
| Crash | A aba Estrutura lia `payload.items` de um envelope → `undefined.length` → React unmount → página preta (sem error boundary na feature). |
| Estado stale | `useTabData` não resetava `loaded.current` ao trocar `productCode` → reúso de dados entre produtos. |

**Produtos de reprodução:** `30190123` (estrutura vazia envelopada), `90264302` (com desenho).

**Correção (boundary, não patch pontual):**

- `productApi.ts`: `unwrapDelegated()` + `requireItems()` — `available` desempacota; `forbidden`→403; `not_found`→404; demais estados→unavailable; coleção malformada→`contract_error`.
- `ProductDetailPage`: reset de estado por `productCode`.
- `App.tsx`: `PluginErrorBoundary` envolvendo Products — qualquer crash futuro degrada para estado de erro, nunca página preta.

## 3. Roteamento (GATE B)

Contrato de URL (sem roteador paralelo — `history`/`URLSearchParams` nativos via `useLocationSearch`):

```text
/apps/engineering/products                      catálogo (code|description|ref|groups|types|sort|dir|page)
/apps/engineering/products/:productCode         ficha, aba=overview
/apps/engineering/products/:productCode?tab=T   T ∈ overview|structure|where-used|suppliers|drawings|history
```

- Clique na aba → `pushState`; normalização de aba inválida → `replaceState` (sem poluir histórico).
- `whereUsed` (camelCase legado) normaliza para `where-used`; valor inválido → `overview`.
- Refresh/deep link/back/forward funcionam (`popstate` ouvido por `useLocationSearch`).

## 4. Multiselect + filtros reativos (GATE C/D)

**Novo contrato oficial (extensão aditiva, owner api-delpi):**

| Rota | Mudança |
|---|---|
| `GET /products/search?group_code=` | único → CSV `IN (?, ?, ...)` parametrizado (valor único continua válido) |
| `GET /products/filter-options` | **novo** — `groups[]` + `product_types[]` da fonte oficial (110 grupos / 19 tipos em prod) |
| `GET /v1/products?group_code=` | façade repassa CSV ao owner |
| `GET /v1/products/filter-options` | **novo** na façade (registrado antes de `/{product_code}`; allowlists de rotas atualizados) |

**Frontend:**

- `EngineeringMultiSelectField` (`createDashboardMultiSelectField` do `@delpi/plugin-ui`) para Grupo e Tipo — busca interna, seleção múltipla, acessível, mobile.
- Reativo: código/descrição/referência com debounce; grupo/tipo aplicam na seleção; filtros → `page=1`; `AbortController` cancela requests obsoletos; draft pendente não é perdido ao interagir com outro filtro antes do debounce.
- **Limpar** (botão oficial): reseta filtros + seleções + URL + paginação e reexecuta.
- Sem filtro local de página — filtragem é server-side real no owner.

## 5. Descrições e apresentação (GATE E)

**Investigação:** produção retorna `description:"#"` (ex.: `30190123`) e `description:""` (ex.: `90260862`) **direto da fonte TOTVS** — o `#` é o valor oficial persistido, não bug de transformação.

**Tratamento honesto:** `#`/`###`/vazio renderizam como placeholder não-informativo (classe `products-desc--missing`, tooltip indicando ausência na fonte) — valor não é alterado nem inventado.

**Fornecedores:** `lead_time`/`minimum_quantity` nulos não renderizam `0 dia(s)`; só exibidos quando a fonte informa.

## 6. Contratos alterados (doc 63 atualizado)

```text
api-delpi:   GET /products/search  group_code: valor único → CSV (IN parametrizado)
api-delpi:   GET /products/filter-options  [NOVO]  engineering view
façade:      GET /v1/products      group_code CSV forwarding
façade:      GET /v1/products/filter-options  [NOVO]
```

- Sem campo comercial/custo/fiscal exposto (`view=engineering` preservado).
- Route ordering: literais antes de `/{code}`/`/{product_code}` em ambas as APIs.
- Sem WRITE contract → edição permanece `not_implemented` (residual owner-blocked).

## 7. Testes

| Camada | Resultado |
|---|---|
| api-delpi (suite grupo/filter-options) | 10 pass |
| api-delpi (superfície produto/meta) | 13 pass |
| engineering-api (suite completa, SHA final) | **491 pass / 10 skip** |
| vitest (frontend, SHA final) | **186 pass / 19 files** |
| tsc / eslint / vite build | 0 erros / 0 erros / `App-Cy0HjvWS.js` |
| Playwright (SSO real, dev stack com código do worktree) | **15/15 — desktop 5, tablet 5, mobile 5** |

E2E cobre: catálogo→ficha, multiselect grupo+tipo com dados reais, busca reativa com `?code=` na URL, `?tab=` deep link, back/forward, normalização de aba inválida, ausência de TypeError/página preta.

## 8. Deploy e smoke produtivo

```text
DEPLOY_PREVIOUS_SHA: 447218e365
DEPLOYED_SHA:        a8ee1025fe  (rebase sobre origin/main; commits 3804618eb2 + a8ee1025fe)
PROCEDIMENTO:        git pull --ff-only + up-prod-sequential.sh --build api-delpi engineering-api engineering
SERVIÇOS:            delpi-api-delpi (healthy), delpi-engineering-api (healthy), delpi-engineering — demais 90+ containers intocados
BUNDLE PROD:         assets/App-Cy0HjvWS.js contém "filter-options" e "where-used"
```

**Smoke autenticado (usuário `products.smoke`, identidade delegada via gateway interno):** 13/13

```text
health 200 · list 200 total=55356 · filter-options 200 groups=110 types=19
group_code=1001,1002 CSV → itens todos ∈ {1001,1002}
product_type=MP,PI CSV → 200
detail 90260862 → 200 (desc='' honesta) · structure → 200 items=0 (sem crash — era o bug)
where-used/suppliers/price-history → 200 · drawing 404 honesto
not-found 404 · no-auth 401
POPULADO: 80013071 CABO CAPNOGRAFO → structure items=6 · 10211279 parents=2
DRAWING: 70260001 → meta 200 + PDF 200 magic=%PDF-1.6 (181KB)
```

Teardown completo: usuário KC + row Core deletados; scripts removidos.

## 9. Paridade EVA

`product.search` aceita `group_code`/`product_type` na allowlist — strings CSV passam ao owner sem mudança de schema/registry. Mesmo gateway `delegated_auxiliary` da façade (caminho único provado nos probes). `product.update` permanece `not_implemented` (sem WRITE contract).

## 10. Residuais (owner-blocked / ambientais)

- `product.update`/edição: sem contrato WRITE oficial → desabilitado honesto.
- `revision_history` cadastral: sem contrato (doc 63 §2.7).
- Filtro server-side por situação: owner não expõe (§G-3).
- Descrições de grupo: sem contrato canônico SBM010 — opções mostram código oficial apenas.
- Descrições `#` na fonte: tratamento de apresentação, não correção de dado (owner TOTVS).
- Core PermissionResolver sem invalidação cross-process → smoke exigiu superadmin temporário (doc 59, débito Core).
- Erros de log observados (`Strategic Indicators API timeout`) pertencem à superfície dashboard commercial — não relacionados.

## 11. Matriz de aceite

PRFIX-01..32: 30 PASS · 2 RESIDUAL_OWNER_BLOCKED (PRFIX-18 parcial — descrição é dado oficial, tratamento de apresentação aplicado; PRFIX-26 light/dark herdado do design system — sem CSS próprio de tema).

**Veredito:** ACCEPT_WITH_RESIDUAL — crash eliminado na causa (envelope), navegação orientada por URL, filtros reativos com multiselect oficial, dados honestos, deploy canônico e smoke produtivo completo.
