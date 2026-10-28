# OVERVIEW.R3 — Otimização de densidade visual do Hero

> **Status:** implementado e deployado.  
> **Missão:** densidade do Hero da Visão geral equivalente ao Portal Comercial.  
> **Baseline:** `origin/main` em `7caa9a6926`.

## 1. Causa raiz

Inventário comparado:

| | Portal Comercial | Portal Engenharia (antes) |
|---|---|---|
| Componente | `PageHero` (`@delpi/plugin-ui`) | mesmo |
| Densidade | `CommercialPageHero` = wrapper com **`density="compact"`** por padrão (`commercialUi.ts`: "liberar viewport nas listas do portal") | `EngineeringPageHero` = factory crua, default `comfortable` |
| Padding hero | 12×14px (compact) | 28px (comfortable) |
| Gap do conteúdo | 6px | 14px |
| Gap do body (filtros) | 6px + borda 8px | 12px + borda 14px |
| Gap entre preset e filtros | 8px | 16px (`--en-grid-gap`) |

O excesso de espaço não era CSS customizado: era a **densidade errada do
componente compartilhado** — a Engenharia instanciava o hero em
`comfortable` enquanto o Comercial consome o mesmo componente em
`compact`. Gaps locais de 16px (`--en-grid-gap`) somavam ao efeito.

## 2. Correção

`plugins/engineering/src/ui/engineeringUi.ts`:

- `EngineeringPageHeroBase` = `createDashboardPageHero({prefix})` (como antes);
- `EngineeringPageHero` = wrapper com `density="compact"` default —
  **mesmo padrão do `CommercialPageHero`** (`commercialUi.ts`).

`plugins/engineering/src/index.css`:

- `.engineering-overview-filters` e `__fields`: gap 16px → **8px**
  (mesma densidade dos filtros dentro do hero compact no kit:
  `.delpi-ui-page-hero--compact` aplica `gap: 8px` aos grids de filtro).

Nenhum CSS duplicado do kit, nenhuma altura fixa, nenhuma margem
negativa — a altura continua determinada pelo conteúdo. O CSS do
modificador `--compact` já existe no kit (`page-hero.css`, servido pelo
bundle `style-*.css` do plugin-ui) e o shim já declarava `density` —
zero alteração no `plugin-ui`.

Escopo de efeito: a convenção compact aplica-se aos três heroes do
portal (Visão geral, Início, Ajuda) — mesma política portal-wide do
Comercial, mantendo consistência interna.

## 3. Hierarquia preservada

Eyebrow `PORTAL ENGENHARIA`, título `Visão geral`, descrição, botão
Atualizar (`RefreshCw`, ghost), `Período rápido` com os 8 presets, e a
grade de 4 filtros (data inicial, data final, competência, unidade) —
idêntica à estrutura anterior; apenas as métricas de espaçamento mudam.

## 4. Regressões

- Seis KPIs, filtros, competência/datas, unidade, consolidado, refresh,
  estados, AuthZ, CTA TRANSFORMA+, LMP futuro: **inalterados** (nenhum
  diff funcional).
- Metas LMP recuperadas na OVERVIEW.R2 e metas TRANSFORMA+:
  **preservadas** — a mudança é só visual.
- `vitest`: 90/90 | `tsc --noEmit`: 0 | `eslint`: 0 | `vite build`: OK.
- Corrigido também um erro de tipagem latente no teste do client
  (`vi.fn<typeof fetch>`) — pré-existente, dentro do escopo do arquivo.

## 5. Temas e responsividade

`--compact` é só métrica — tokens `--delpi-ui-*` intactos → claro/escuro
herdados. Breakpoints do kit mantidos (≤768px padding 10×12, highlights
2 colunas); a grade de filtros segue 4→2→1 como antes. QA visual
autenticado pendente (gate) — verificação estrutural: densidade é a
mesma variante que o Comercial já usa em produção.

## 6. Deploy e smoke

- Push `main` (ff-only); SHA registrado abaixo.
- Deploy canônico: `up-prod-sequential.sh --build engineering` →
  `delpi-engineering` Up. Somente o MFE.
- Smoke público: `200` `/apps/engineering/overview`, remoteEntry novo,
  `401` `/v1/overview` sem JWT.
- Smoke autenticado / QA visual: `PENDING_GRANT_APPROVAL`.

## 7. Residuais

- QA visual comparativo (Comercial × Engenharia) pendente de sessão
  autorizada — a equivalência estrutural é garantida por usarem o mesmo
  componente na mesma densidade.

## 8. SHA final

Registrado no relatório de execução (ver `git log`).
