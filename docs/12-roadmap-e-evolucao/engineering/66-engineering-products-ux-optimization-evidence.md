# 66 — ENGINEERING.PRODUCTS.UX.OPTIMIZATION.R1 — Compact Catalog, Native BOM Tree, PDF Preview & Production Evidence

**Status:** DEPLOYED_PROD — ACCEPT_WITH_RESIDUAL
**Executado:** 2026-10-30
**Executor:** Devin (EVA Coordination)

---

## 1. Escopo

Três melhorias de UX no módulo Produtos (somente apresentação — sem mudança de contrato):

- **A.** Catálogo compacto: hero `density="compact"`, Limpar filtros no slot `actions` (visível só com filtro aplicado), tabela fill-height com scroll interno e cabeçalho sticky, contagem sem duplicidade.
- **B.** Estrutura/Onde é usado: árvore textual substituída pelo componente oficial colapsável (`ProductStructureTree`/`RichTree` do bounded context LMPs).
- **C.** Desenhos: preview PDF automático via viewer oficial (`useFilePreviewLoader` + `FilePreviewView`).

## 2. Causa dos espaços e decisões

| Problema | Causa | Correção |
|---|---|---|
| Hero alto | `density="comfortable"` (default) | `density="compact"` — variante oficial do `PageHero` |
| Limpar sempre visível | render incondicional em linha própria | `actions` do hero + render condicional (`hasActiveFilters`) |
| Tabela fora do viewport | cadeia sem altura limitada (page scrolla em `.content`) | `:has(.engineering-products--fill)` trava a página no mount (bounded); `DataTableSection fillHeight` → `layout="scroll"` do kit (`overflow:auto` + thead sticky) e paginação fora da área rolável; fallback `max-height:480px` volta ao scroll de página |
| Contagem duplicada `55356 registro(s) 55356 registro(s)` | `hint` repetia `list.total` + meta do header da section | `hint` passa a mostrar só nota de ordenação; meta oficial única |
| Árvore textual | `ProductTree` local com indentação | `ProductStructureTree`+`StructureLegend` sob escopo `.engineering-lmps` (só classe de escopo — sem copiar CSS) |
| PDF só sob botão | iframe manual com blob local | `useFilePreviewLoader` (cancel + revoke de object URL no cleanup) + `FilePreviewView` (viewer nativo: zoom/páginas/fullscreen do Chromium) + ações Abrir ampliado / Baixar PDF |

**Bug real encontrado e corrigido:** race de Limpar × debounce — clicar Limpar antes do debounce de 400ms deixava o draft sujo, e o timer pendente recomitava o texto na URL (filtro "voltava"). `clearFilters` agora reseta o draft sincronamente antes de navegar. Sem `setDraft` aqui, o efeito só seria neutralizado pela identidade de `applied` — que não muda quando a URL já está limpa.

## 3. Mudanças compartilhadas (aditivas)

- `DataTableSection`: prop `fillHeight` (default off — NC/LMPs/suppliers inalterados) → modificador `engineering-table-section--fill` + `layout="scroll"`.
- `RichTree`: prop `onNodeNavigate` (default off); nó vira botão apenas quando `node.navCode` presente.
- `RichTreeNode.navCode` (opcional): código navegável do nó — setado no mapper; omitido na raiz sintética e em código placeholder `—`.
- `productStructureTree`: filhos também lidos de `node.parents` (consulta reversa where-used); `components`/`items` preservados.
- `ProductStructureTree`: `onNodeNavigate` + `footerLabel` passthrough.
- Shim `plugin-ui.d.ts`: declarações `FilePreviewView`, `useFilePreviewLoader`, `FilePreviewContentState`, `UseFilePreviewLoaderOptions`, `FilePreviewLabels`, `FilePreviewKind`, `FilePreviewSource`.

**Segurança PDF:** fluxo inalterado — `fetchProductDrawingPdf` autenticado via façade → owner → file server; blob → object URL temporária revogada no cleanup do hook oficial; nenhum token em URL; nenhum acesso direto a file share.

## 4. Testes

| Camada | Resultado |
|---|---|
| tsc / eslint / vite build | 0 erros / 0 erros (17 warnings preexistentes) / `App-BfIAuKsw.js` |
| vitest | **190/190** (novo `productStructureTree.test.ts`: parents key, navCode, multinível, nulo) |
| Playwright desktop | 4 pass + 1 skip (tipo sem opções no dev) |
| Playwright tablet | 4 pass + 1 skip |
| Playwright mobile | 4 pass + 1 skip |

E2E cobre: Limpar oculto→visível→oculto, `delpi-ui-table-wrap--scroll`, paginação fora do scroll, árvore `.lmps-rich-tree` com toggle `aria-expanded`, preview `.delpi-ui-file-preview__pdf` automático ou estado honesto, tabs/`?tab=`/back/forward, sem TypeError.

Sem alteração de contrato → sem testes backend novos; paridade EVA preservada por construção.

## 5. Deploy e smoke

```text
DEPLOY_PREVIOUS_SHA: 18b2c192e6
DEPLOYED_PROD_SHA:   e234470ba5  (único commit, só plugins/engineering)
PROCEDIMENTO:        git pull --ff-only + up-prod-sequential.sh --build engineering
SERVIÇOS:            delpi-engineering apenas (MFE) — APIs não tocadas
BUNDLE PROD:         assets/App-BfIAuKsw.js (lmps-rich-tree, onNodeNavigate)
                     assets/style-DDZPJuEA.css (table-wrap--scroll, engineering-products--fill)
HEALTH:              delpi-engineering Up, logs limpos
SMOKE:               bundle servido verificado; backend inalterado (rotas já
                     homologadas no doc 65); validação visual das 3 URLs
                     (lista / ?tab=structure / ?tab=drawings em 90264258)
```

**Rollback:** rebuild `infra-engineering` em `18b2c192e6`; sem migrations/flags/backend.

## 6. Residuais

- E2E skip `multiselect de Tipo` em dev: `filter-options` dev sem dados (ambiente, não defeito).
- Zoom/páginas do PDF: controles nativos do viewer Chromium no iframe (padrão do kit); toolbar custom não implementada (não existe no kit).
- Produto `90264258` para homologação visual pós-deploy fica registrado como verificação de usuário final; smoke técnico de bundle/health concluído.
- Demais residuais herdados do doc 65 (sem WRITE, sem SBM010, descrições `#` oficiais).

## 7. Matriz de aceite

PRUX-01..34: 32 PASS · 2 parciais documentados (PRUX-26 backend N/A por construção — sem contrato novo; PRUX-32 smoke técnico prod completo, validação visual final delegada ao usuário nas 3 URLs canônicas).
