# X4.REST-STATUS.S2.R1 — Correção de ancoragem do widget flutuante

**Data:** 2026-10-26 · **Task:** `X4.REST-STATUS.S2.R1` · **Owner:**
`plugins/supplies` (MFE apenas) · **Base:** S2 (`85883e5f2e`).

## 1. Sintoma comprovado

Na ficha `/apps/supplies/suppliers/002469/01` (conteúdo ausente por
indisponibilidade da REST produtiva), o widget recolhido funcionava, mas ao
expandir o painel aparecia parcialmente fora da área visível — topo cortado,
indicadores inacessíveis.

## 2. Causa raiz

`portal/src/index.css` aplica ao host federado a animação de entrada de rota:

```css
.app-host--route-enter {
  animation: appHostRouteEnter 0.48s ease-out both;
}
```

O keyframe final (`transform: translateY(0)`) fica **retido** pelo fill-mode
`both` após o fim da animação. Pela especificação CSS Transforms, **qualquer**
valor de `transform` num ancestral — inclusive a identidade — cria um
containing block para descendentes `position: fixed`.

Resultado: o `position: fixed; bottom` do widget deixou de ancorar na
viewport e passou a ancorar na caixa do `.app-host` (a área de conteúdo da
página, que é rolada junto com o conteúdo). Em páginas curtas/em erro, a
geometria resultante projetava o painel expandido para fora da viewport —
exatamente o recorte capturado pelo PO.

Aumentar `z-index` não resolveria: o problema é de containing block, não de
empilhamento.

## 3. Correção

`SupplierIntegrationStatusCard` agora renderiza o widget via
`createPortal(..., document.body)` — mesmo mecanismo que o kit usa em
`FixedPanelPortal`/`AnchoredPanelPortal` para escapar de clips por
`overflow`/`transform`/stacking. O wrapper do portal reaplica
`.dashboard-supplies-portal`, pois os tokens `--sp-*` e todos os seletores
do widget são escopados nessa classe (o tema segue `:root[data-theme]`,
alcançado normalmente no body).

Complemento de geometria: `__details` passou a limitar a altura pela
viewport real — `max-height: min(55dvh, calc(100dvh - 180px), 480px)` —
garantindo que head + erro + notas + ação caibam sempre dentro da tela.

## 4. Preservado

- Máquina de estados `closed/collapsed/expanded` e cache de módulo
  (navegação lista↔ficha sem refetch nem reabertura).
- Escape recolhe; fechar devolve foco ao FAB; `aria-expanded`/`aria-controls`.
- Única chamada REST continua sendo «Verificar integração»; zero POST/PUT.
- z-index 30 — abaixo de modais/overlays oficiais (1200).
- Zero alteração em `api-delpi`, `supplies-api`, contratos, RBAC, flags.

## 5. Testes

Suíte estrutural em 15 testes — novos casos S2.R1: portal no body com
wrapper de escopo; bound de altura pela viewport (`calc(100dvh - …)`) +
scroll interno. Regressão MFE: **478/478**. `tsc -b`, `vite build` e eslint
limpos; `git diff --check` limpo.

Nota honesta: a prova geométrica real (`getBoundingClientRect` na viewport)
exige navegador autenticado — registrada como `INCONCLUSIVE` até smoke
visual; a correção remove estruturalmente a causa (containing block por
transform) e limita a altura pela viewport por construção.

## 6. Deploy e residuais

- Deploy canônico: `up-prod-sequential.sh --build supplies`.
- Residual: smoke visual autenticado pendente de sessão.
