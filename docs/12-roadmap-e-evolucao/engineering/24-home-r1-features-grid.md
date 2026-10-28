# ENGINEERING.HOME.R1 — Grid responsivo de Caminhos e funcionalidades

Status: implementado e publicado em `main`.
Baseline: `ba77512a07` (`origin/main`, pós LOADING.R1).

## Objetivo

Os três cards de seção (Trabalho, Análises, Suporte) da página Início
ficavam agrupados à esquerda com largura mínima, deixando uma faixa
vazia à direita. A missão é distribuí-los pela largura útil seguindo a
convenção já usada no Portal Suprimentos e nos demais portais — sem
criar sistema de grid paralelo.

## G0 — Inventário

### Referência Suprimentos

`plugins/supplies/src/index.css`:

```css
.dashboard-supplies-portal .sp-home-sections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--sp-grid-gap, 16px);
}
```

### Corroboração

`plugins/commercial/src/index.css` — `.cm-home-sections-grid` e demais
grades de cards usam **sempre** `repeat(auto-fit, minmax(..., 1fr))`
(200px/220px/240px/440px conforme o caso). Nenhum portal usa
`auto-fill` em grade de cards.

O card (`SectionRouteCard` do plugin-ui) tem `width: 100%` no CSS do
kit — a largura é governada pela célula do grid, sem `max-width`
restritivo interno.

## Causa raiz

`plugins/engineering/src/index.css` usava `auto-fill`:

```css
grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
```

Com `auto-fill`, o grid cria trilhas vazias para preencher o container
(ex.: 5 colunas de 240px num container de 1200px): os 3 cards reais
ocupam as primeiras trilhas com 240px e as trilhas fantasmas ficam
vazias à direita. Com `auto-fit`, as trilhas vazias colapsam e os
cards reais expandem para `1fr` — exatamente o comportamento dos
outros portais.

## Correção (menor diff)

`auto-fill` → `auto-fit` — mesma convenção literal do Suprimentos e do
Comercial (`repeat(auto-fit, minmax(240px, 1fr))` + `gap` no token
`--en-grid-gap`).

Comportamento resultante (idêntico aos portais canônicos):

- 3 cards em desktop amplo → distribuem a largura útil em `1fr` cada;
- cards futuros → quebram linha automaticamente, sem hardcode de
  colunas;
- busca com 1–2 cards → trilhas vazias colapsam, cards se expandem;
- mobile/tablet → media queries existentes (1 coluna) preservadas;
- sem overflow: `minmax(240px, 1fr)` + breakpoints já existentes.

Nenhuma alteração de componente, card, tokens de cor, catálogo,
favoritos, ícones, badges, AuthZ ou API.

## Validação

- Vitest `plugins/engineering`: **93/93** (11 files).
- `tsc --noEmit`: 0 erros. `eslint .`: 0. `vite build`: OK —
  `dist/assets/style-*.css` contém `auto-fit`.
- Temas: apenas geometria mudou — tokens claro/escuro intocados.
- QA visual autenticado: `TEST_NOT_RUN` (sem sessão; HTTP 200 não
  prova geometria).

## Deploy e smoke

- Push `main` (fast-forward) → `srv-api` `git pull --ff-only` →
  `up-prod-sequential.sh --build engineering`.
- Smoke público: `/apps/engineering` 200; CSS servido contém
  `auto-fit` na classe `engineering-home-sections-grid`.

## Residuais

- `VISUAL_QA`/smoke autenticado do grid (desktop/tablet/mobile,
  busca 1–2 cards, zoom 200%): `TEST_NOT_RUN` — mesmo gate de sessão
  Core (`PENDING_GRANT_APPROVAL`) de F3/R3/LOADING.R1.

## Arquivos

- `plugins/engineering/src/index.css` — `auto-fill` → `auto-fit`.
