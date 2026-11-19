# UX V4.2 — design tokens, ajuda contextual e usabilidade guiada

**Status:** IMPLEMENTADO (HML pendente de evidência de deploy).
**Task:** `EVA-LBS-V42-DESIGN-TOKENS-CONTEXTUAL-HELP-UX-01`.
**Baseline:** bancada unificada V4.1 — a estrutura aprovada (rail de métodos,
contexto compartilhado, cabeçalho compacto, barra de ações, KPIs, M1/M5,
operações, cenários) **não foi redesenhada**.

## 1. Objetivo

Tornar a bancada autoexplicativa: o usuário entende onde está, o que cada
informação significa, o que pode fazer, qual é o próximo passo, quais são as
limitações do método e o que acontece ao executar cada ação — sem treinamento
prévio, com ajuda em português centralizada em catálogo de domínio e contraste
WCAG 2.2 AA medido nos dois temas.

## 2. Problemas identificados e correções

| Problema | Causa | Correção (owner) |
|---|---|---|
| Balão de aviso `.analysis-issues` claro demais no tema escuro | cor de texto/borda light-only no Studio | receita warning tokenizada em `studio.css` (`color-mix` sobre `--warning`/`--surface`/`--border`/`--text`) |
| Ícone de ajuda (?) quase invisível no tema escuro | gatilho usava `--delpi-ui-muted` translúcido (alfa ~0,5) | `help.css` passa a `--delpi-ui-text-muted` opaco (fallback `--delpi-ui-muted`) — **Plugin UI** |
| Item ativo do rail de métodos com contraste 3,12 no tema claro | `color: accent` puro sobre fundo branco | `collapsible-tool-rail.css`: `color-mix(accent 55%, text)` preserva a identidade azul e sobe para 5,0/7,8 — **Plugin UI** |
| Textos técnicos dispersos | termos inline nos componentes | catálogo central `src/ui/helpCatalog.ts` — **Studio** |
| Sem ajuda de método | — | disclosure `Como usar este método` com guias M1/M5 do catálogo |
| Estados vazios/erros sem próximo passo | mensagens neutras | textos orientadores com ação explícita |

## 3. Inventário de componentes reutilizados (Plugin UI)

Todos já existiam — **nenhum componente de ajuda foi criado no Studio**:

- `HelpTooltip` (ícone ou `wrap`), `HintAction` (hint em ação sem botão
  aninhado), `FieldLabel` (label com hint), `SectionHintLabel`,
  `TitleWithHelp`, `TabHintCell`, `KeyTip`.
- `SectionCard.hint`, `SimpleKpiCard.titleHint`, `DataTableColumn.headerHint`,
  `StateBox`, `StatusBadge`, `CollapsibleToolRail`,
  `ActionButton.softDisabled` (botão bloqueado permanece focável para a dica).

### Mudanças no Plugin UI (genéricas, sem conteúdo de domínio)

1. `src/styles/help.css` — folha única extraída de `styles.css`; importada por
   `styles.css` **e** `native-controls.css`, garantindo estilos do balão de
   ajuda no documento **e** dentro de shadow roots (o bubble portala para
   `document.body`, então o preview precisa da folha nos dois escopos).
2. `src/workspace-controls.ts` — `export * from "./components/help"` expõe a
   família help no subpath curado `@delpi/plugin-ui/workspace-controls`.
3. `ToolRailItem.description` (campo público já existente) passa a compor o
   `title` nativo do item do rail — descrições acessíveis sem tooltip novo.
4. Correções de contraste acima (`help.css`, `collapsible-tool-rail.css`).

## 4. Catálogo de ajuda — `src/ui/helpCatalog.ts`

Entradas tipadas (`id`, `title`, `summary`) e guias de método
(`objective`, `steps`, `interpretation`, `limitations`), todas em pt-BR:

- `SOURCE_HELP` — OBSERVED, PROVIDED, CALCULATED, SIMULATION, UNKNOWN, DRAFT_LOCAL.
- `STUDY_HELP` — produto, estudo manual, roteiro, filial, estágio, cenário, rascunho.
- `PRODUCTION_HELP` — modo/início/fim/duração do turno, pausa, tempo produtivo,
  demanda, lote, takt (com exemplo numérico), tempo padrão, setup.
- `BALANCE_HELP` — operação, posto, CT, recurso, carga por posto, maior carga,
  sem posto, Yamazumi, takt × carga, gargalo.
- `METHOD_HELP` — rail, M1–M6, `planned` (métodos M2–M4/M6 sempre descritos
  como planejados/indisponíveis, nunca executáveis).
- `ACTION_HELP` — todas as ações da barra, exportações e controles de
  posto/operação.
- `STATE_HELP` — sem takt (ação: Condições de produção), M1 manual sem análise
  oficial, estágio não coberto.
- `METHOD_GUIDES` — guias completos M1 e M5.

Precisão técnica garantida pelo catálogo: CT ≠ posto ≠ operador ≠ máquina;
visualização Yamazumi é `SIMULATION`; tempos ausentes são `UNKNOWN`, nunca
zero; resultado oficial só vem do domínio autorizado via `analysisState`.

## 5. Cobertura de ajuda contextual

| Superfície | Mecanismo |
|---|---|
| Cards de origem, formulários manual/roteiro (nome, código, filial, estágio) | `FieldLabel.hint` + `HintAction` nos botões |
| Badges OBSERVED/DRAFT_LOCAL/rascunho salvo | `HelpTooltip` adjacente |
| Seletor de cenário | `FieldLabel.hint` |
| Barra de ações (Novo cenário, Condições, Como usar, Mais ações, Trocar origem, CSV/Excel/PDF, Limpar) | `HintAction` por item |
| Condições de produção (modo, início/fim/duração, pausas, demanda, lote) | `SectionCard.hint` + `FieldLabel` por campo |
| KPIs (takt, tempo produtivo, maior carga, sem posto) | `SimpleKpiCard.titleHint` |
| Análise oficial M1 (título e botão) | `HelpTooltip` + `HintAction` (dinâmico quando bloqueado) |
| Yamazumi (seção, cabeçalhos da tabela de postos, mover/remover posto) | `hint` + `headerHint` + `HintAction` |
| Operações (seção, colunas op/CT/recurso/tempo/setup/origem/posto, adicionar/remover) | `hint` + `headerHint` + `HintAction` |
| Rail de métodos | `ToolRailItem.description` no `title` + status `Planejado` |
| Guia de método | disclosure `Como usar este método` (`aria-expanded`/`aria-controls`, `#method-guide`) — não sai do estudo |

Regras respeitadas: tooltips não substituem `aria-label`; ações destrutivas
mantêm confirmação; bloqueado usa `softDisabled` (focável, `aria-disabled`,
com explicação); nenhum comportamento fictício foi descrito.

## 6. Estados vazios e validação

- Operações vazio → `Nenhuma operação no estudo. Use «+ Adicionar operação» para começar.`
- Sem postos → mensagem + ação «+ Adicionar posto».
- Sem takt → explica a causa + ação «Condições de produção».
- M1 em estudo manual → diagnóstico local explícito, sem promessa de análise oficial.
- Validação de turno/pausas/demanda/lote → mensagens dizem o que aconteceu, o
  dado envolvido e como corrigir; códigos de erro preservados.
- Avisos (`UNKNOWN`, carga parcial, `stageCovered=false`) seguem como aviso,
  nunca erro bloqueante.

## 7. Tokens, contraste e acessibilidade

- Studio consome apenas tokens (`--delpi-ui-*` → tokens do host); sem hex novo.
- `tests/contrast-audit.mjs` mede **54 pares** (título, muted, seções,
  tabela th/td, rail, KPIs, botões primário/secundário, labels, gatilhos de
  ajuda, badges de proveniência, aviso warning, rodapé do gráfico) em light e
  dark: todos ≥ 4,5:1 (texto) / 3:1 (texto grande e ícones). Mínimos medidos:
  rail ativo 5,0; ajuda 7,07 (light) / 9,48 (dark); badges ≥ 9,19.
- Teclado/toque: gatilho focável, abre por hover/focus/click, **Escape fecha**;
  bubble portalado a `document.body` com flip/clamp — verificado no smoke.
- Shadow DOM: estilos de help presentes no shadow root e no documento
  (`styles.css` + `native-controls.css`/`workspace-controls.css`).

## 8. Invariantes preservadas

- Cálculos, dados oficiais, cenários, contratos do elemento — inalterados.
- Análise M1 continua `studio-analysis-run` → host/BFF; Studio só apresenta.
- Nenhuma dependência do balanceamento legado de `plugins/engineering`.
- Arquitetura V4.1 e rotas inalteradas; sem deploy de produção.

## 9. Evidências

- `tests/help-catalog.test.mjs` — 20 asserções: ids estáveis, termos
  obrigatórios, métodos planejados descritos como indisponíveis, guias M1/M5
  com objetivo/passos/interpretação/limitações.
- `tests/preview-smoke.mjs` — fluxo completo + V4.2: badges com balão, guia de
  método (abre/fecha, `aria-expanded`), tooltip por teclado + Escape, aviso
  warning com botão `aria-disabled` focável; 1440/1024/390/320 × light/dark.
- `tests/contrast-audit.mjs` — 54 pares medidos, WCAG AA.
- Plugin UI — vitest 2830/2830; `CollapsibleToolRail.test.tsx` cobre
  `description`→`title`; build + verify-host-exports OK.

## 10. Limitações conhecidas

- Itens `disabled` do rail não disparam tooltip de `title` no Chromium
  (limitação do navegador); o texto de status «Planejado» permanece visível.
- `description` do rail usa `title` nativo (tooltip do SO), não o balão do
  kit — decisão consciente para não aninhar interativos no item do rail.
