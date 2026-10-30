# GLPI #1353 — Revisão UI/UX, plugin-ui e temas claro/escuro — ACEITE TÉCNICO

> Data: 2026-10-30 · Escopo: `plugins/supplies` (MFE) + tokens do tema do plugin
> Commit: `cb02b69896` · Manifest: `supplies` 0.5.2 · Deploy: `delpi-supplies`
> URL: `https://minhadelpi.com.br/apps/supplies/consumption-audit`

## 1. Problema reportado (PO)

1. Linha selecionada na tabela de OPs com fundo claro + texto quase branco
   (ilegível, principalmente no tema escuro).
2. Checkboxes de seleção múltipla com aparência nativa/própria, fora do kit.
3. Revisão completa de cores, hover, foco, seleção, disabled e consistência
   com os demais apps modernos da Minha DELPI.

## 2. Causa raiz

- Tokens `--sp-accent-soft`, `--sp-primary`, `--sp-primary-soft` e
  `--sp-surface-alt` eram **usados mas nunca definidos** no tema do plugin;
  os fallbacks eram cores claras fixas (`#eef2ff`, `#f5f7ff`,
  `rgba(120,120,120,.06)`, `#1f6feb`). No escuro → fundo claro com texto claro.
- A tabela de resultados era `<table>` manual com `<input type="checkbox">`
  cru — fora do `plugin-ui` e sem o estado `is-selected` canônico.
- Paginação manual (dois botões + texto) em vez de `SuppliesCompactPagination`.

## 3. Correção aplicada (owner: `plugins/supplies`)

| Item | Antes | Depois |
|---|---|---|
| Tabela de OPs | `<table>` manual, linha clicável sem teclado | `SuppliesDataTable` (`layout="section"`, `onRowClick` com Enter/Espaço, `getRowClassName` → `is-selected`) |
| Checkbox | `<input type="checkbox">` nativo | `SuppliesFilterCheckbox` (`NativeCheckboxControl` oficial, `interactive: true` — clique não abre o detalhe) |
| Paginação | botões + texto manual | `SuppliesCompactPagination` (labels PT-BR do kit: `N linha(s) · Página X de Y`) |
| Tokens de estado | não definidos → fallback claro | `--sp-primary`, `--sp-primary-soft`, `--sp-accent-soft`, `--sp-surface-alt` definidos nos **dois** temas via `color-mix` sobre accent/surface |
| CSS morto | `__result-row`, `__pagination` | removido; `__table-wrap` mantido (usado nas tabelas de detalhe) |

Coluna de seleção marcada `interactive: true` → clique no checkbox **não**
navega para o detalhe; clique na linha (ou Enter/Espaço) abre a auditoria.
Seleção 2–10 preservada (`COMPARE_MAX`), disabled quando o máximo é atingido.

## 4. Gates

| Gate | Resultado |
|---|---|
| `vitest` consumption-audit | PASS 33/33 (+6 novos: DataTable, checkbox oficial, is-selected, CompactPagination, tokens × 2) |
| suíte `plugins/supplies` | PASS 558/558 |
| `tsc -b` / `eslint` arquivos tocados / `vite build` | PASS / PASS / PASS |
| bundle local | `App-YEExAMk8.js` (hash publicado em prod) |

## 5. Verificação visual (Playwright, Chromium headless, stack dev, SSO real)

Ambiente: `delpi-portal` + `delpi-supplies` (build local) via gateway `localhost`;
login SSO Keycloak real; dados Protheus de homologação (2319 OPs no recorte).

| Cenário | Evidência | Resultado |
|---|---|---|
| Tabela sem seleção — claro | `01-light-table.png` | PASS |
| Tabela com seleção — claro | `02-light-selected.png` | PASS — tinta accent 12%, texto escuro legível |
| Tabela com seleção — escuro | `03-dark-selected.png` | PASS — accent sobre superfície escura, texto branco legível |
| Tabela sem seleção — escuro | `04-dark-table.png` | PASS |
| Detalhe da OP — claro/escuro | `10-detail-light.png` / `09-detail-dark.png` | PASS — hero, filtros, banner de evidência, grade resumo |
| Comparação 2 OPs — claro/escuro | `11-compare-light.png` / `12-compare-dark.png` | PASS — tabelas de totais por UOM legíveis (`/comparison` HTTP 200) |
| Mobile 390px | `15-mobile-light-full.png` | PASS — região da tabela com scroll horizontal, paginação e ação utilizáveis |
| Marcadores do kit no DOM | — | `delpi-ui-native-checkbox` ×10, `delpi-ui-table` ×1, **0** checkbox nativo cru |

### Contraste medido (linha selecionada, composição real sobre superfície)

| Tema | Texto | Fundo efetivo | Razão | WCAG AA (≥ 4,5:1) |
|---|---|---|---|---|
| Claro | rgb(0,56,102) | accent 12% sobre #fff | **10,48:1** | PASS |
| Escuro | rgba(255,255,255,.94) | accent 12% sobre superfície escura | **11,80:1** | PASS |

Screenshot do PO confirmou o sintoma original; medida pós-fix prova a correção.

## 6. Deploy e smoke em produção

- `up-prod-sequential.sh --pull --fase mfe --build supplies` em
  `operador@srv-api` (somente o MFE; BFF/producer intocados).
- srv-api em `30875af8d` (origin/main avançou com commit comercial após o
  push — `cb02b6989` é seu pai; bundle contém o fix).
- Imagem `infra-supplies@9a14fca54011` (build 2026-10-30 07:02 UTC).
- Bundle `App-YEExAMk8.js` = hash do build local com as mudanças;
  `remoteEntry.js` expõe o novo `__federation_expose_App-C1fBAVom.js`.
- Smoke público: `remoteEntry.js` 200 · `App-YEExAMk8.js` 200 · rota 200.
- Marcadores no bundle prod: `is-selected`, `delpi-ui-native-checkbox` presentes.
- Smoke autenticado de dados: não reexecutado — superfície de contrato
  inalterada desde o smoke F1–F6 (PASS); a prova E2E autenticada foi feita no
  stack dev com o mesmo bundle (login → busca → seleção → comparação 200).

## 7. Inventário de componentes (resumo)

| Área | Componente | Estado |
|---|---|---|
| Hero/breadcrumb | `SuppliesPageHero`, `SuppliesPagePath` | já correto |
| Filtros | `SuppliesFilterBarShell`, `FiltersRow`, `SuppliesTextField`, `SuppliesSelectField`, `SuppliesDateField`, `SuppliesSegmentToggle`, `SuppliesClearFiltersButton` | já correto |
| Tabela OPs | `SuppliesDataTable` | **migrado nesta rodada** |
| Checkbox | `SuppliesFilterCheckbox` | **migrado nesta rodada** |
| Paginação | `SuppliesCompactPagination` | **migrado nesta rodada** |
| Ações | `SuppliesActionButton` (comparar) | já correto |
| Cards/banners/badges | `SuppliesSectionCard`, `SuppliesStateBanner`, `SuppliesStatusBadge`, `SuppliesEmptyState`, `SuppliesLoadingCard` | já correto |
| Tabelas de detalhe/movimentos | `<table>` HTML em cards internos | mantidas — contexto estático de detalhe, sem seleção/ordenação; tokens agora resolvem corretamente |

## 8. Residual / TO_INVENTORY

- `sp-safety-stock-branch-choice` (E11) também consumia `--sp-primary[-soft]`
  indefinido — agora resolve os novos tokens; fallbacks mortos (sem mudança
  visual esperada, mas a cor de foco/ativo passa a derivar do accent).
- Screenshot mobile do shell mostrou o drawer de navegação aberto por padrão
  — comportamento do Portal, não do MFE.
- Automação visual permanece ad-hoc (`/tmp/ca-visual-*.mjs`); se a revisão UI
  virar rotina, promover para `plugins/supplies/e2e/` com o harness de
  `plugins/engineering/e2e`.

## 9. Resultado

`DEPLOYED / TECHNICAL_GATE_PASS / READY_FOR_PO_VISUAL_REVIEW`
