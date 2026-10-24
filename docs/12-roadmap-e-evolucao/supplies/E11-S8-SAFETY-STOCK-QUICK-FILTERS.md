# E11.S8 — Filtros rápidos no Estoque de Segurança (padrão Portal Comercial)

**Data:** 2026-10-24 · **Status:** IMPLEMENTADO · **Owner:** `plugins/supplies` · **Produto:** Portal Suprimentos, WF-16 / E11.

## O que mudou

Barra de filtros rápidos por situação na página Estoque de Segurança — cinco botões que controlam **o mesmo estado `query.status`** do filtro Status existente. Não é um segundo sistema de filtragem: chips e select Status são duas visões do mesmo campo, logo a sincronização bidirecional (botão ↔ select ↔ URL ↔ F5/back/forward) é estrutural, não duplicada.

| Botão | `status` aplicado |
|---|---|
| Todos os materiais | `""` (remove só o filtro de status) |
| Abaixo do estoque de segurança | `below_safety_stock` |
| No estoque de segurança | `at_safety_stock` |
| Acima do estoque de segurança | `above_safety_stock` |
| Sem estoque de segurança | `without_safety_stock` |

- Posição: após os indicadores do hero e antes do `SafetyStockFilters` — mesmo padrão Comercial/SCs (chip row dentro do PageHero).
- Selecionar um chip aplica `patchQuery({ status, page: 1 })` → **só** status + página 1 mudam; filial, grupo, UM, busca, toggles e ordenação são preservados por omissão.
- Um botão ativo por vez, derivado de `query.status` (`""` → «Todos»); estado ativo via `aria-pressed` + modificador visual do kit (não depende só de cor).
- URL serializa `status` como antes (push no histórico → back/forward nativos; F5/deep link restauram o chip ativo).
- A combinação legítima `status=without_safety_stock` + `includeWithoutSafetyStock=false` pode retornar zero linhas → estado vazio coerente já existente; **o toggle nunca é alterado silenciosamente**.

## Padrão Comercial comprovado (AC-01)

- `plugins/commercial/src/pages/OpenOrdersPageImpl.tsx` monta `attentionChips` (`id/label/active/onSelect`, labels com contadores) e renderiza `CommercialScopeChipBar`.
- O componente é kit compartilhado: `createDashboardScopeChipBar` → `plugins/plugin-ui/src/components/feedback/ScopeChipBar.tsx` (`role="group"`, `aria-pressed`, modificador `active`, wrap responsivo, foco visível).
- **Supplies já expõe o equivalente canônico:** `SuppliesScopeChipBar` em `suppliesUi.ts`, já usado por `PurchaseRequestsPage`/`PurchaseOrdersPage` — **zero import cross-context**.

## Contadores (AC-09 — decisão: omitidos)

Inventário do contrato: `GET /safety-stock/summary` recebe `status` e o BFF repassa ao produtor; em `safety_stock_query_repository.fetch_summary` o `status` entra no `WHERE` do resumo. **Os contadores do summary são do recorte ativo, não totais gerais** — exibir números nos chips irmãos seria semanticamente falso (com `status=below`, os demais contadores viriam 0). A task autoriza omissão nesse caso → chips com **rótulos apenas**. Os indicadores do hero continuam exibindo os contadores do recorte (semântica já documentada desde a S2).

## Arquivos

- `plugins/supplies/src/features/safety-stock/SafetyStockPage.tsx` — `selectStatus` + `statusChips` (fonte única `query.status`) e `<SuppliesScopeChipBar>` no hero.
- `plugins/supplies/src/features/safety-stock/content.ts` — rótulos/aria-label dos chips (PT-BR).
- `plugins/supplies/src/content/helpTooltips.ts` — `SP_HELP.safetyStockQuickFilters` (hint no rótulo «Situação»).
- `plugins/supplies/src/content/userManualContent.ts` — bullet no Manual + FAQ sobre os filtros rápidos.
- `plugins/supplies/src/index.css` — `.sp-safety-stock__chip-row` agregada à regra chip-row existente (mesmo layout das demais listas).
- `plugins/supplies/src/features/safety-stock/SafetyStock.structural.test.ts` — teste S8 de veto/estrutura.

## Evidências de verificação

- **Testes MFE:** 438 pass (+1 teste estrutural S8: kit canônico, 4 status contratados + «Todos», fonte única, `page: 1`, sem `quickFilterStatus`, sem contadores nos chips, rótulos presentes).
- **TypeScript:** `tsc --noEmit` limpo. **Build:** OK. **`git diff --check`:** limpo.
- **Lint:** feature zerada; baseline global inalterada (10 erros/22 warnings pré-existentes de outros escopos) — `LINT_DELTA=0`.
- **Busca residual:** sem `ESTSEG` na UX, sem `quickFilterStatus`/estado paralelo, sem import de `plugins/commercial`, sem `api-delpi`, sem endpoint/fan-out novo.
- **Contratos:** somente os GETs existentes; `status` enviado como antes; zero permissão nova; AuthZ central intacta; sem recálculo.
- **Visual autenticado:** `INCONCLUSIVE` — responsividade/temas/teclado vêm do kit (`ScopeChipBar` compartilhado, mesmo componente já usado nas listas SCs/POs); QA autenticado pendente do PO.

## Residuais e gate

- `GATE-FEATURE E11` permanece **INCONCLUSIVE** — jornada autenticada + QA visual do PO (desktop/mobile, claro/escuro, teclado/foco, sync chips↔select) pendentes.
- Rollback: `git pull` para `3039f729c8` (HEAD anterior a S8) + imagem `ffa2e9e492ff` (S7) — não executado.


## Revisão GPT — E11.S8 (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL`.** Conferidos no source `0668cdeb3c`: este documento e `SafetyStockPage.tsx`. A implementação reutiliza `SuppliesScopeChipBar` e deriva os cinco chips do estado único `query.status`, aplicando `patchQuery({status, page: 1})`; não há estado de filtro paralelo. A omissão dos contadores está fundamentada no contrato: o `summary` é filtrado por status, de modo que valores nos chips irmãos não representariam totais independentes. Resultados 438 PASS, TypeScript/build e deploy (imagem `sha256:b883b846adfe`, bundle `App-1WJf6UiX.js`) são evidências reportadas pelo executor, não reexecutadas pelo GPT.

**Gate:** `E11_S8=ACCEPT_WITH_RESIDUAL`; `E11_DEPLOY_STATUS=PASS_DEPLOYED` conforme relatório do executor; `GATE-FEATURE E11=INCONCLUSIVE` porque não houve sessão federada autenticada nem evidência visual/teclado/mobile. Homologar sincronização chip ↔ select ↔ URL ↔ F5/back, preservação dos filtros e relação com a página própria de detalhe. Lint global 10 erros/22 warnings preexistentes fora da feature não alterados. Nenhum novo endpoint, permission ou cálculo autorizado nesta revisão.
