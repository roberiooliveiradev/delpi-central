# EVA / Portal Engenharia — Aba Roteiro: implementação fiel ao PNG aprovado

**TASK_ID:** `EVA-PORTAL-ROUTING-VISUAL-CONTRACT-IMPLEMENTATION-01`
**Estado:** `IMPLEMENTADO / EVIDÊNCIA COLETADA / VERIFICAÇÃO INDEPENDENTE EXECUTADA`
**Referência visual autoritativa:** `ux/routing/references/routing-all-tabs-dark-light-approved.png`
— PNG 1024×576, `sha256:89cea3e90f8b0557c73890094db5ce065e044006b0b21710680926d7bcef89fa`
(bytes íntegros do anexo do Product Owner; substitui `operations-compact-target.svg`,
agora SUPERSEDED).

## 1. Decisões de implementação (image-first, Plugin UI-native)

| Elemento do PNG | Decisão | Componente real |
|---|---|---|
| Cabeçalho compacto | `Roteiro de fabricação` + `{code} · Operações e análises de processo` + filtros à direita | `EngineeringSectionCard` + `EngineeringFiltersRow`/`FilterSelect` |
| Navegação interna | Operações / Balanceamento / Análise visual | `EngineeringTabs` (role=tablist) |
| 4 indicadores | Operações, Centro de trabalho, Recurso, Tempo padrão | `EngineeringKpiCard` ×4 |
| Cards de operação | Lista vertical expansível, sem DataTable | `EngineeringInteractiveDataCard` (COMPOSE) |
| Conteúdo expandido | Grid curta + lista de componentes | `EngineeringDetailFieldGrid` + `<ul>` compacta |
| Calculadora | Dois cards lado a lado: Condições (3 campos + resumo 2 indicadores) / Configuração opcional (2 campos + CTA) | `EngineeringDetailCard` ×2 em grid |
| Resultado | `Resultado do balanceamento` + badges + métricas | `EngineeringDetailCard` + `EngineeringStatusBadge` |
| Gráficos | Tempo por peça / Tempo × takt (takt como **barra** com legenda) / Distribuição simulada | `ConfigurableSeriesChart` via `EngineeringChartCard` |

`DataTable` permanece apenas na comparação de cenários (dados verdadeiramente
tabulares) — nunca como visualização primária de operações.

## 2. Defeitos encontrados e corrigidos pela validação visual/verificação

1. **Plot branco no dark (raiz real):** `backgroundColor` tematiza só a moldura;
   a área de plotagem é parte do gráfico (`chartParts.plotArea`) e defaulta para
   `OFFICE_CHART_PLOT_FILL` claro mesmo com `theme:"dark"`. Corrigido passando
   `chartParts={{ plotArea: { style: { fill: portalTheme.surface } } }}` —
   pixel auditado no plot: `(22,26,39)` dark / `(255,255,255)` light.
2. **Takt como barra (fidelidade ao PNG):** `Tempo × takt` passou de goal-line
   para `seriesList` [Tempo por peça, Takt] — legendas e composição do PNG.
   `colorScale by_goal`/`high_is_bad` preservado (usa `goalLineValue` sem linha).
3. **Validação de Pausas (bug real):** `?? 0` tornava "abc" silenciosamente 0 e
   enviava `available_minutes` incorreto ao domínio; agora parse explícito exige
   número ≥ 0 quando preenchido.
4. **Shim plugin-ui:** exports `Conversation*` espelhados do componente real
   (destrava `npm run typecheck` quebrado pelo commit concorrente `ec40197e3b`);
   `InteractiveDataCardField` e `chartParts` declarados conforme contrato real.

## 3. PLUGIN_UI_GAP registrado

- `InteractiveDataCard` não expõe `aria-expanded` para disclosure — mitigado com
  sufixo "— expandida" no `ariaLabel`; correção pertence ao owner do kit
  (registrado em `component-map.md` §Lacunas).

## 4. Evidência executada

- `npm run typecheck` verde; **478 testes** Vitest; `npm run build` ok.
- **20/20 Playwright reais** (SSO + Engineering API oficial, produto 90264302,
  dados REAL) — desktop, tablet, mobile, **390×844**, **320×720**, dark+light.
  Capturas em `plugins/engineering/e2e/artifacts/routing-contract/`:
  operations-{dark,light}, expanded, tech-details, balance-{empty,filled,result,
  comparison,validation}, visual-{dark,light}, empty-routing; zero pageerrors,
  zero chamadas diretas `/apps/api-delpi` (boundary BFF preservado).
- Comparação estado a estado vs PNG: hierarquia/cards/densidade/temas
  equivalentes; divergências apenas nos pontos já registrados (chevron no slot
  de ações do kit; barra de operação invisível quando tempo ≪ takt — dado real
  0,072 s vs 50,4 s, não placeholder).
- Verificador oficial: `INCONCLUSIVE` (devin CLI sem autenticação — bloqueio de
  infra, registrado em `.git/delpi-verifier/requests/eva-routing-visual-contract-01.md`).
- Fallback clean-context: `ACCEPT_WITH_RESIDUAL` → resíduos P1/P2 corrigidos
  (validação de pausas, takt-como-barra, shim, dead class); P3s documentados
  (aria-expanded gap, aria-controls de tabs inativas — padrão comum).

## 5. Resíduos conhecidos (não bloqueantes)

- `e2e/specs/products.spec.ts` contém marcadores de conflito **commitados** em
  `be614649b7` (defeito preexistente em main; lint falha ali independentemente
  deste diff) — owner: sessão PRC.
- Acessibilidade de tabs inativas (`aria-controls` para painel desmontado) —
  padrão aceito do kit.
- Smoke autenticado de produção pendente de principal humano Keycloak (mesmo
  padrão do AC-18 anterior).
