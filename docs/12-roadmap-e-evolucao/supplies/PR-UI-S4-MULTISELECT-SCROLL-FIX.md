# PR.UI.S4 — MultiSelect Dropdown Scroll (Centro de custo)

**Data:** 2026-10-23 · **Owner da correção:** `@delpi/plugin-ui` (design system compartilhado) · **Status:** PASS

## Sintoma

Filtro **Centro de custo** em `/apps/supplies/purchase-requests`: o dropdown mostra
muitas opções (facet com 54+ itens), mas **não rola** — as opções do fim da lista
ficam inacessíveis, nem com mouse wheel, teclado ou barra de rolagem.

## Causa-raiz (comprovada com Chromium headless + CSS de produção)

Os seletores wildcard do `select-control.css`, criados para capturar variações de
prefixo de plugin (`cm-select__*`, `sp-select__*`, ...), **também casam com as
classes `-multi-select__*`**, porque `-select__list` é substring de
`-multi-select__list` e `-select__panel--portal` é substring de
`-multi-select__panel--portal`:

```css
/* select-control.css (antes) — casa multi-select por substring! */
[class*="-select__panel--portal"] {
  max-height: min(70vh, 480px);
  overflow: hidden;          /* corta o painel em 480px */
}
[class*="-select__panel--portal"] [class*="-select__list"] {
  max-height: none;          /* remove o limite da lista do multi-select */
}
```

Efeito medido no painel portal do multi-select (repro produção, `ul` com 54 itens):

| Métrica | Antes | Depois do fix |
|---|---|---|
| `scrollHeight` | 1780 | 1780 |
| `clientHeight` | **1780** (= scrollHeight → sem overflow) | **386** (< scrollHeight → rolável) |
| `max-height` computed | `none` | `none` (lista preenche o painel) |
| `scrollTop` após wheel | **0** (nada rola) | **1394** ✅ |
| `canScroll` | `false` | `true` |

Com `max-height:none`, a lista do multi-select crescia até a altura total do
conteúdo; o painel (com `overflow:hidden` herdado do select) recortava em 480px.
Resultado: itens inferiores **fisicamente fora da área visível e nenhuma região
rolável** — o `overflow:auto` da lista nunca engatilhava porque a altura não era
limitada.

Hipóteses descartadas por evidência: CSS do supplies (não altera essas classes),
posicionamento/z-index do `AnchoredPanelPortal` (painel renderizava corretamente),
scrollbar invisível (scrollHeight==clientHeight provava ausência de overflow),
federation (CSS entregue intacto, defeito era semântico).

## Correção (menor diff no owner canônico)

**Arquivo:** `plugins/plugin-ui/src/styles/select-control.css` — todos os
wildcards `-select__*` receberam negação para não capturar `-multi-select__*`:

```css
[class*="-select__panel--portal"]:not([class*="-multi-select__panel--portal"]) { ... }
[class*="-select__panel--portal"]:not([class*="-multi-select__panel--portal"])
  [class*="-select__search"]:not([class*="-multi-select__search"]) { ... }
[class*="-select__panel--portal"]:not([class*="-multi-select__panel--portal"])
  [class*="-select__list"]:not([class*="-multi-select__list"]) { ... }
```

**Arquivo:** `plugins/plugin-ui/src/styles/multi-select.css` — o multi-select
portaled passa a ter o **mesmo contrato canônico de scroll do select**: painel
limita altura, busca e ações ficam fixas, **somente a lista rola**:

```css
.delpi-ui-multi-select__panel--portal,
[class*="-multi-select__panel--portal"] {
  max-height: min(70vh, 480px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.delpi-ui-multi-select__panel--portal .delpi-ui-multi-select__search,
.delpi-ui-multi-select__panel--portal .delpi-ui-multi-select__actions,
.delpi-ui-multi-select__panel--portal .delpi-ui-multi-select__create,
/* + wildcards equivalentes */
{ flex: 0 0 auto; }

.delpi-ui-multi-select__panel--portal .delpi-ui-multi-select__list,
[class*="-multi-select__panel--portal"] [class*="-multi-select__list"] {
  min-height: 0;
  max-height: none;
  flex: 1 1 auto;
  overflow: auto;
}
```

Benefício adicional ao modo portal: antes o painel não tinha cap — podia exceder
viewports baixos; agora ele limita em `min(70vh, 480px)` com busca/ações
("Selecionar visíveis" / "Limpar") sempre visíveis e acessíveis.

**Não alterado:** API pública da factory, DOM/classnames, comportamento não-portal
(lista continua com `max-height: min(50vh, 320px)`), tokens de design. Nenhum
override local em `plugins/supplies` — a correção é no owner compartilhado.

## Consumidores

Todos os MFEs que usam `createDashboardMultiSelectField`/`MultiSelectField` do
`@delpi/plugin-ui` recebem o fix automaticamente via federation remote
(`plugin_ui/styles` é servido pelo `delpi-plugin-ui`): supplies
(purchase-requests, purchase-orders, deliveries, inventory, overview),
purchase-requests, dashboard-supplies, commercial, dashboards (commercial,
engineering, financial, lmps, production, quality), eficiencia-fabril,
financeiro-inadimplencia, kaizometro, maintenance, quality-action-plans,
transformometro, bpmn-editor — sem rebuild individual dos MFEs.

## Testes

- **Novo:** `plugins/plugin-ui/src/styles/multi-select.scroll.test.ts`
  - (a) contrato portal do multi-select: painel `overflow:hidden` +
    `max-height:min(70vh,480px)` + coluna flex; lista `overflow:auto` +
    `max-height:none` + `flex:1 1 auto`;
  - (b) sibling guard: **todo** wildcard `-select__*` em `select-control.css`
    deve estar negado com `:not([class*="-multi-select__` — impede regressão
    do vazamento que causou o bug.
- `select-control.scroll.test.ts` existente segue verde (select inalterado).
- Suíte completa plugin-ui: **2324/2324**.
- Repro Chromium (mouse wheel): scroll 0 → 1394 ✅; primeiro e último item
  acessíveis; painel ainda capado em 480px.
- `tsc --noEmit` limpo; `vite build` OK.

## Acessibilidade / teclado

- Sem mudança de DOM/ARIA: o `role`/foco seguem no componente; a rolagem agora é
  possível nativamente (wheel, touchpad, scrollbar, PageDown/Home/End com foco
  dentro da lista).
- Busca e comandos permanecem fora da área rolável — sempre alcançáveis.

## Deploy

Apenas `delpi-plugin-ui` (o CSS é entregue pelo remote de federation; nenhum MFE
embute o CSS do kit). Rebuild indiscriminado de outros apps não foi necessário —
mecanismo comprovado: `preparePluginUiRemote()` faz `import
"@delpi/plugin-ui/styles"` resolvido via `federationShareScope` para o remote.

## Residuais

- `VISUAL_SCROLL_SMOKE = INCONCLUSIVE` — sem navegador autenticado; validação de
  wheel feita em repro DOM+CSS de produção (headless Chromium real).
- `End`/`PageDown` fora de foco nativo depende do componente focável — o DOM e o
  ARIA não mudaram; o defeito reportado (ausência de região de scroll) está
  resolvido.


## Revisão GPT — PR.UI.S4 (2026-10-23)

**Decisão:** `ACCEPT_WITH_RESIDUAL` para correção em código e publicação técnica; `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Foram inspecionados no source `1e51c1ae6b` os estilos `plugins/plugin-ui/src/styles/select-control.css` e `multi-select.css`, o teste `multi-select.scroll.test.ts` e o presente documento. A colisão por substring de `-select__*` com `-multi-select__*` é compatível com os seletores encontrados. O diff exclui o multi-select dos wildcards conflitantes do Select e configura no MultiSelect portaled painel flex limitado a `min(70vh,480px)`, busca/ações fora do scroll e lista `min-height:0; flex:1 1 auto; overflow:auto`. A correção está no **owner `@delpi/plugin-ui`**, sem override CSS em Supplies e sem alteração de contrato público.

**Evidência executor-reported (não reexecutada pelo GPT):** Chromium headless reproduziu `scrollTop=0` antes e `1394` depois, `clientHeight=1780→386`, primeiro/último item acessíveis; suíte kit `2324/2324`, typecheck/build PASS; deploy somente `plugin-ui` imagem `sha256:37868d89c63f` e stylesheet `style-CLZDCNXE.css`. Esses testes provam o CSS e o DOM de reprodução, mas **não** substituem smoke da página autenticada no navegador do PO. `LINT=INCONCLUSIVE` no executor (eslint v9 versus configuração legada), não declarar lint PASS.

**Residuais:** verificar em produção autenticada wheel/touchpad/teclado e seleção da última opção do Centro de custo, tema e viewport; fazer teste sibling funcional de ao menos um outro consumidor do mesmo remote quando possível; monitorar seletor wildcard residual em `popover-surface.css` para regressão cosmética (não classificado como causa de scroll). `CONTRACT_IMPACT=NONE`. `CODE=ACCEPT`; `DEPLOY=PASS (executor-reported)`; `VISUAL=INCONCLUSIVE`. Nenhuma mudança autorizada em fluxo ERP ou cutover de fornecedores.
