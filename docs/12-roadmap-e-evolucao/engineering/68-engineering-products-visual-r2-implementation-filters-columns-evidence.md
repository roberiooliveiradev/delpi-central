# 68 — ENGINEERING.PRODUCTS.VISUAL.R2.FULL — Implementation, Filters, Columns & Deployment Evidence

**Status:** IMPLEMENTED + DEPLOYED (produção). **Data:** 2026-10-31.
**Especificação de autoridade:** [67](67-engineering-products-visual-master-r2-all-pages-helpdesk-filters.md). **Base:** `7086824a1d` → **SHA final:** `07c0815ea2` (main) → merge prod `0c7f42e1`.

## 1. GATE A — Inventário Helpdesk/Plugin UI (matriz de reuso)

| Componente | Owner | Reuso | Implementação Produtos |
|---|---|---|---|
| `AnchoredPanelPortal` (popover ancorado) | plugin-ui `components/shape` | direto | painel Filtros (mesma config do Helpdesk: bare/bottom/end/gap6/onDismiss) |
| `TicketListFilterBuilder` | helpdesk (privado) | NÃO importado | composição neutra equivalente (`ProductAdvancedFilters`) — Abstraction Gate: 1 consumidor, sem nova abstração compartilhada |
| `createDashboardFiltersKit` (FiltersRow/FilterInput/FilterSelect) | plugin-ui `components/layout` | direto | campos Campo/Valor das regras |
| `createDashboardMultiSelectField` | plugin-ui | direto | valores "é um de" (grupo/tipo) |
| `TableColumnVisibilityMenu` + `useTableColumnVisibility` + localStorage prefs | plugin-ui `components/data`+`utils` | direto | gestor Colunas com reordenação por drag agora ligada (`orderedColumns`/`reorderColumns`) |
| `ProductStructureTree`/`RichTree`, `useFilePreviewLoader`+`FilePreviewView`, `EngineeringDetailCard` | plugin-ui/engineering | direto | ficha R2 |

## 2. Implementado

- **Filtros avançados** (`ProductAdvancedFilters` + `productFilterRules.ts`): critérios FIELD+OPERATOR+VALUE somente com operadores do contrato — Código/Ref. cliente "começa com", Descrição "contém", Grupo/Tipo "é um de", Subgrupo "é igual a". Draft local; "Aplicar filtros" commita atomicamente no estado canônico da URL (push de histórico, page=1); fechar sem aplicar descarta draft; "Limpar" no painel limpa só o draft; "Limpar filtros" do hero zera rápidos+avançados+URL+debounce+requests. Badge de filtros aplicados no gatilho; chip removível `Subgrupo: X` na toolbar (único campo sem controle no hero).
- **Colunas dinâmicas:** padrão visíveis Código/Descrição/Tipo/Grupo/UM/Ref. cliente/Rev./Situação + 7 opcionais do payload `view=engineering` (subgroup, drawing_code, secondary_unit, production_line, default_warehouse, barcode, net_weight — zero N+1, sem custo/preço). Preferência `engineering-products-list` em localStorage (oficial do kit; documentado como local, não cross-device).
- **Ficha:** Estrutura/Onde é usado em card oficial com contagem + Expandir/Recolher todos (teto 600 nós, `expandDepth` aditivo + remount por época); Desenhos em workspace compacto (barra de metadados + ações Abrir ampliado/Baixar PDF + viewer `min(78vh)`; found=false → estado honesto); Visão geral com atalho contextual para Desenhos quando `drawing_code` existe.
- **Fixes de baseline:** badge `error`→`danger` (variante inexistente no kit — bug de baseline); `ProductStructureData`/`ProductStructureNode` passam a admitir `null` dos payloads reais.

## 3. Contratos verificados (sem mudança de API)

`subgroup` já suportado end-to-end: engineering-api `search_products` → delegated_auxiliary → api-delpi `/products/search` (WHERE SB1.B1_SUBGRUP) → OpenAPI baseline → allowlist DAVI `product.subgroup` → EVA `product.search` (registry + tool_bridge). Colunas opcionais presentes em `PRODUCT_DETAIL_ENGINEERING_FIELDS`. Nenhum novo contrato, nenhuma nova tool MCP, nenhuma elevação de permissão.

## 4. Testes e evidência

- **Unit/typecheck/lint/build (SHA `07c0815ea2`):** `tsc` 0 erros; eslint 0 erros (17 warnings preexistentes do padrão set-state-in-effect); vitest 201 testes — 11 novos `productFilterRules` + cobertura `sub=` em `productRoutes.test.ts`; `vite build` OK.
- **E2E estendido** (`e2e/specs/products.spec.ts`): painel avançado (draft sem request, apply atômico `sub=`, chip, Limpar global), gestor Colunas (opcionais ocultas→toggle→Restaurar), Expandir/Recolher todos, workspace Desenhos.
- **BLOQUEIO de ambiente (EXECUTION_DRIFT):** E2E browser local INCONCLUSIVE — stack dev usa `keycloak:24.0` mas o realm importado exige authenticator `organization` (KC≥25); erro "Unexpected error when handling authentication request" impede SSO local. Requer decisão de owner de infra (upgrade de imagem/flow), fora do escopo do diff.

## 5. Deploy e smoke produtivo

- Push `feat/engineering-products-e2e:main` (ff) → `origin/main = 07c0815ea2`.
- Prod `operador@192.168.1.237`: HEAD local divergia (`c0879c1da` merge+commit local `100f31c1f`) → `git merge origin/main` não destrutivo → `0c7f42e1` → `./infra/scripts/up-prod-sequential.sh --build engineering` → `delpi-engineering` recriado.
- Smoke: bundle `style-KatXeyGK.css` idêntico ao build local (contém `adv-filters`/`applied-chip`); `GET /apps/engineering/` 200; `remoteEntry.js` 200; `engineering-api /v1/health` 401 (auth-gated). Logs nginx limpos.
- **Rollback:** `git checkout 7086824a1d` no servidor + rebuild `engineering`.

## 6. Matriz PRVIS-01..28

- **PASS:** 01–09 (toolbar/hero/filtros/draft/URL/limpar), 10–12 (colunas/fonte oficial/nulls), 13–20 (abas/estrutura/onde-usado/fornecedores/desenhos/histórico honesto), 21 (Editar bloqueado), 23–24 (AuthZ/EVA sem nova tool), 27 (docs), 28 (bloqueios documentados).
- **INCONCLUSIVE (ambiente):** 22 (viewports/temas — E2E browser bloqueado por KC local), 25 (browser SSO), 26 (deploy feito; smoke HTTP OK; homologação browser prod pendente de SSO).

## 7. Residuais

1. Stack dev Keycloak 24 × realm com authenticator `organization` — owner infra (bloqueia E2E browser local; prod usa KC próprio funcional).
2. Prod repo divergido (`git pull --ff-only` impossível) — deploy usou merge não destrutivo; recomenda-se realinhar prod para ff-only futuro.
3. Homologação visual browser em produção pendente de sessão SSO — smoke HTTP/bundle provado.
