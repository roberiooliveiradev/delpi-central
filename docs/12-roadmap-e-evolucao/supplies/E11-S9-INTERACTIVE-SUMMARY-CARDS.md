# E11.S9 — Cards de indicadores interativos (substituem a barra de filtros)

**Data:** 2026-10-24 · **Status:** IMPLEMENTADO · **Owner:** `plugins/supplies` (+ `plugins/plugin-ui`, extensão aditiva) · **Produto:** Portal Suprimentos, WF-16 / E11.

## O que mudou

Os seis cartões de indicadores do hero passam a ser **acionáveis** — clicar (ou Enter/Espaço) filtra a tabela. A barra separada de chips «Situação» da E11.S8 foi **removida**: não há dois sistemas de filtro.

| Card | Estado aplicado (contrato existente) |
|---|---|
| Materiais | `status=""` + `includeWithoutSafetyStock=true` (recorte completo) |
| Com estoque de segurança | `status=""` + `includeWithoutSafetyStock=false` |
| Sem estoque de segurança | `status=without_safety_stock` |
| Abaixo do estoque de segurança | `status=below_safety_stock` |
| No estoque de segurança | `status=at_safety_stock` |
| Acima do estoque de segurança | `status=above_safety_stock` |

## Card composto «Com estoque de segurança» — solução contratual

Verificado no produtor (`safety_stock_query_repository.fetch_summary` + `build_where_clauses`): o parâmetro contratual **existente** `include_without_safety_stock=false` aplica `status <> 'without_safety_stock'` no WHERE — exatamente a união abaixo/no/acima (materiais com parâmetro definido). **Sem filtro fictício, sem recálculo no MFE, sem novo contrato** → `EXECUTION_DRIFT` não disparado. URL representa a seleção explicitamente (`status` ausente + `includeWithoutSafetyStock=false`), F5/deep link restauram o card ativo.

## Sincronização e invariantes

- Fonte única: cards, select Status e toggle são visões de `query.status`/`query.includeWithoutSafetyStock` — ativo derivado (um por vez: status único ativa o card correspondente; `status=""` + toggle → «Materiais» ou «Com ES»).
- Select Status → card ativo automático; card → mesma URL/serialização (push → back/forward; F5).
- `patchQuery({...patch, page: 1})` — só os campos do card mudam; filial, grupo, UM, busca e ordenação preservados por omissão.
- Cards de status único **não tocam o toggle** (regra S8 mantida: combinação `status=without` + toggle off → estado vazio coerente, toggle nunca alterado silenciosamente).
- Contadores: **semântica inalterada** — summary é do recorte ativo (documentado desde S2/S8); nenhum número é apresentado como total independente.

## Kit reutilizado

- `PageHeroHighlight` (plugin-ui) ganhou `onSelect`/`active`/`ariaLabel` **opcionais e aditivos** — tile interativo renderiza `role="button"`, `tabIndex=0`, Enter/Espaço, `aria-pressed`, modificadores `--interactive`/`--pressed` (`page-hero.css`), espelhando o padrão já canônico de `SimpleKpiCard` (`delpi-ui-kpi-card--interactive/--pressed`). Zero breaking change nos consumidores.
- Investigação do Portal Comercial: seus «quick filters» são chips (`attentionChips`); cards interativos **não existiam** em nenhum portal → o padrão foi criado no owner canônico (kit), não duplicado no MFE.

## Arquivos

- `plugins/plugin-ui/src/components/layout/PageHero.tsx` (+ test) — interatividade opcional no highlight.
- `plugins/plugin-ui/src/styles/page-hero.css` — `--interactive`/`--pressed` (tokens do kit, temas claro/escuro, `prefers-reduced-motion`).
- `plugins/supplies/src/features/safety-stock/SafetyStockPage.tsx` — cards acionáveis; chips removidos.
- `plugins/supplies/src/features/safety-stock/content.ts` — strings de chips removidas (rótulos dos cards já eram os exigidos).
- `plugins/supplies/src/shims/plugin-ui.d.ts` — novos campos opcionais.
- `plugins/supplies/src/content/helpTooltips.ts` — hint do título explica que os cartões filtram; hint da barra removido.
- `plugins/supplies/src/content/userManualContent.ts` — bullet Manual + FAQ atualizados (sem referência à barra).
- `plugins/supplies/src/index.css` — regra chip-row revertida (safety-stock sem classe própria).
- `plugins/supplies/src/features/safety-stock/SafetyStock.structural.test.ts` — teste S9.

## Evidências de verificação

- **Testes MFE:** 438 pass (teste S9: 6 ids, `onSelect`/`active`/`ariaLabel`, composto via parâmetro contratual, status exatos, fonte única, sem chips/estado paralelo, `page: 1`).
- **Testes kit:** `PageHero.test.tsx` 7 pass (+1: tile `onSelect` → `role=button`, `aria-pressed`, clique dispara handler, tiles inertes inalterados).
- **TypeScript:** `tsc --noEmit` limpo (supplies + plugin-ui). **Build:** OK. **Lint:** feature zerada; baseline global inalterada.
- **Regressão:** props aditivas — demais consumidores de `PageHero` inalterados; demais páginas supplies sem chips de safety-stock.
- **Busca residual:** sem `SuppliesScopeChipBar`/`statusChips`/`quickFilters` em safety-stock; sem `ESTSEG` na UX; sem filtro fictício; sem `api-delpi`.
- **Visual autenticado:** `INCONCLUSIVE` — interatividade/foco/temas vêm do kit (mesmos tokens do `SimpleKpiCard` interativo); QA autenticado pendente do PO.

## Residuais e gate

- `GATE-FEATURE E11` permanece **INCONCLUSIVE** — jornada autenticada + QA visual do PO pendentes.
- Deploy: plugin-ui (remote, antes dos MFEs) + supplies — procedimento canônico, registrado na seção de evidência do commit/deploy abaixo.
- Rollback: `git pull` para `0668cdeb3c` (S8) + imagens anteriores de plugin-ui e supplies — não executado.


## Revisão GPT — E11.S9 (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para código/contrato/publicação, com `GATE-FEATURE E11=INCONCLUSIVE`. Conferidos no source `910d2315a1`: este documento, `SafetyStockPage.tsx` e `plugins/plugin-ui/src/components/layout/PageHero.tsx`. O `PageHeroHighlight` ganhou `onSelect`, `active` e `ariaLabel` opcionais; seis indicadores do MFE controlam os campos contratados `query.status`/`query.includeWithoutSafetyStock` com atualização de `page:1`, sem barra de chips paralela. A seleção composta `Com estoque de segurança` possui suporte real pelo filtro `includeWithoutSafetyStock=false` conforme inventário do produtor; nenhuma regra de cálculo adicional é necessária.

**Evidências reportadas pelo executor (não reexecutadas pelo GPT):** 438 testes MFE, 7 testes PageHero, tsc/build PASS, deploy remoto `plugin-ui` imagem `555b47ccf9d6` e `supplies` imagem `f99272d59581`. **Residual funcional para homologação:** `status=without_safety_stock` combinado a `includeWithoutSafetyStock=false` pode resultar em empty legítimo; verificar que a UX explica a combinação de filtros, sem modificar toggle silenciosamente. Também testar card ativo ↔ Status ↔ URL, F5/back, seleção por teclado e responsividade real em ambos os temas. `AUTHENTICATED_SMOKE=INCONCLUSIVE`; sem evidência visual autenticada não elevar o gate a PASS.
