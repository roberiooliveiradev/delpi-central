# Roadmap — refatoração frontend (Minha DELPI Chat)

> Atualizado em **16/06/2026**  
> Escopo: plugin `plugins/minha-delpi-chat` (MFE React + Module Federation)  
> Objetivo: reduzir duplicação, padronizar componentes compartilhados, CSS organizado e consumo consistente dos tokens `--mdc-*` do portal.

Complementa a regra Cursor [`plugins-visual-design-system.mdc`](../../../.cursor/rules/plugins-visual-design-system.mdc) e o README do plugin.

---

## 1. Problema

O chat principal acumula **~160 componentes** na raiz de `src/ui/components/`, com **~129 arquivos CSS** co-localizados. O admin já tem primitivos maduros (`admin/shared/`), mas o chat reimplementa padrões visuais e de overlay várias vezes.

| Sintoma | Impacto |
|---------|---------|
| Selectors/menus com markup duplicado | Bugfix visual exige N arquivos |
| Menus com portal inconsistente | Corte em mobile, z-index sobre sidebar |
| Modais com markup repetido | `modal-layer.css` cresce a cada feature |
| Hex/cores fora de tokens | Dark mode quebrado ou inconsistente |
| `shared/` subutilizado | Difícil saber o que é primitivo vs feature |

---

## 2. Arquitetura alvo

```text
src/ui/
├── styles/                    # tokens + overlay + menu — barrel ui/styles/index.css
├── layout/                    # chat-layout, workspace-responsive, transitions
├── components/
│   ├── shared/                # primitivos cross-feature (overlay, modal, menus)
│   ├── presentation/          # ChatRich* + rich-presentation-shared.css
│   ├── composer/              # ChatInput, mention, selectors
│   ├── message/               # ChatAssistantContent, registry, segmentos
│   ├── workspace/             # WorkspaceFile*, ingest CSS, ProjectHome (alvo PR-36)
│   ├── shell/                 # Sidebar, ContextBar, ContextTopbar
│   ├── admin/shared/          # primitivos admin — referência
│   └── [legado raiz]          # Hub chatPresentation, modais finos, export, … (ver component-structure.md)
```

Mapa detalhado: [`component-structure.md`](./component-structure.md).

### Princípios

1. **Uma regra, um módulo** — posicionamento de menu → `menuPositionUtils`; portal → `AnchoredMenuPortal`; textos PT do assistente ficam na API (não no MFE).
2. **Feature fina** — `ChatPresentationFormatSelector` só mapeia ícones; lógica visual no `shared/`.
3. **Tokens antes de hex** — superfície/texto/sombra via `var(--mdc-*)` ou `color-mix` sobre tokens.
4. **Portal canônico** — `resolveOverlayPortalContainer()` → `#mdc-modal-root` (nunca `document.body` para overlays do chat).
5. **Responsivo obrigatório** — breakpoints 1024 / 768 / 480 px; área de toque ≥ 44×44 px.

---

## 3. Estado atual (já entregue — jun/2026)

| Item | Caminho | Notas |
|------|---------|-------|
| Tokens de popover | `src/index.css` | `--mdc-popover-*`, `--mdc-menu-item-*`, aliases formais |
| Portal ancorado | `shared/overlay/AnchoredMenuPortal.tsx` | Scrim + painel + posicionamento |
| Hook de layout | `shared/overlay/useAnchoredMenuLayout.ts` | resize, scroll, Escape |
| CSS popover/ação | `shared/overlay/menu-popover.css`, `action-menu.css` | |
| Selector genérico | `shared/composer/ComposerOptionSelector.tsx` | Formato + modo de resposta |
| Painel de ações | `shared/menus/ActionMenuPanel.tsx` | Ícone + rótulo + danger |
| Posicionamento | `menuPositionUtils.ts` | `resolveComposerOptionMenuPosition`, `resolveActionMenuPosition` |
| Migrações | `ChatPresentationFormatSelector`, `ChatResponseModeSelector`, `ChatProjectCard`, `ChatConversationMenu` | Wrappers finos ou uso direto dos primitivos |
| Menu 「+」 composer | `shared/composer/ChatInputPlusMenu.tsx`, placement `composer-panel` | Portal + scroll; sem `overflow:hidden` no pai |
| **`ChatModal`** | `shared/modal/ChatModal.tsx` | Shell centrado; Confirm/Alert/Prompt migrados |
| Testes | `menuPositionUtils.test.ts` | 5 casos |

### Aliases legados (migração gradual)

Classes legadas `mdc-chat-response-mode__*` removidas (C6 jun/2026); usar só `mdc-composer-option-selector__*`.

---

## 4. Backlog completo

Legenda: **P** prioridade (1 = mais urgente), **Risco** baixo / médio / alto, **Esforço** S / M / L.

### Fase A — Overlays e menus (alto impacto UX)

| # | P | Tarefa | Arquivos / escopo | Risco | Esforço | Critério de pronto |
|---|---|--------|-------------------|-------|---------|-------------------|
| A1 | 1 | Menu **「+」** do composer em portal | `ChatInputPlusMenu`, `ChatInput.tsx` | Médio | M | ✅ PR-2 jun/2026 |
| A2 | 1 | Unificar **mention menu** com tokens popover | `ChatComposerMentionMenu.tsx/css` | Baixo | S | ✅ tokens `--mdc-popover-*` |
| A3 | 2 | **`ChatTableRowMenu`** sobre `AnchoredMenuPortal` | `ChatTableRowMenu.tsx` | Médio | M | ✅ PR-4 jun/2026 — placement `context-menu`, shell `overlay` |
| A4 | 2 | **`ChatAssistantMessageMenu`** idem | `ChatAssistantMessageMenu.tsx` | Baixo | S | ✅ via `ChatTableRowMenu` |
| A5 | 2 | **`ChatContextBar`** chip menu | `ChatContextBar.tsx` | Baixo | S | Já usa `ChatTableRowMenu` — validar após A3 |
| A6 | 3 | **`ChatOnboardingTour`** alinhar portal | `ChatOnboardingTour.tsx` (hoje `document.body`) | Médio | M | ✅ PR-8 jun/2026 — `ModalPortal` + coords contidas |
| A7 | 3 | Extrair **`DropdownMenuTrigger`** opcional | `shared/menus/` | Baixo | S | ✅ PR-16 jun/2026 |

### Fase B — Modais e diálogos

| # | P | Tarefa | Arquivos / escopo | Risco | Esforço | Critério de pronto |
|---|---|--------|-------------------|-------|---------|-------------------|
| B1 | 1 | Criar **`ChatModal`** compound | `shared/modal/ChatModal.tsx`, `chat-modal.css` | Médio | L | ✅ PR-3 jun/2026 |
| B2 | 1 | Migrar diálogos simples | `ChatConfirmDialog`, `ChatAlertDialog`, `ChatPromptDialog` | Médio | M | ✅ PR-3 jun/2026 |
| B3 | 2 | Migrar diálogos médios | `ChatShortcutPromptDialog`, `ChatSidebarArchivedDialog`, `ChatMemoryUsedDialog` | Médio | M | ✅ PR-6 jun/2026 |
| B4 | 2 | Migrar painéis grandes | `ChatAddContextDialog`, `ChatHelpPanel`, `ChatCanvas`, `ChatExpandModal` | Alto | L | ✅ PR-9/10 + `ChatCanvas`/`ChatExpandModal` jun/2026 |
| B5 | 2 | Migrar modais workspace | `ChatProjectCreateModal`, `ChatAttachmentPreviewModal`, inline em `ChatProjectHome` | Médio | M | ✅ jun/2026 |
| B6 | 3 | Reduzir **`modal-layer.css`** | Listas manuais de `-backdrop` | Médio | M | ✅ PR-15 jun/2026 — `mobileLayout` + scrim genérico |
| B7 | 3 | Mover **`ModalPortal`** para `shared/overlay/` | `ModalPortal.tsx`, `modalPortalTarget.ts` | Baixo | S | ✅ PR-13 jun/2026 |

**Inventário de modais (14+):**

- `ChatConfirmDialog`, `ChatAlertDialog`, `ChatPromptDialog`
- `ChatShortcutPromptDialog`, `ChatSidebarArchivedDialog`
- `ChatAddContextDialog`, `ChatMemoryUsedDialog`, `ChatHelpPanel`
- `ChatCanvas`, `ChatExpandModal`, `ChatAttachmentPreviewModal`
- `ChatProjectCreateModal`, `ChatWebSearchResearchPanel` (se existir)
- Inline: `ChatProjectHome.tsx`, `useWorkspaceFilePreviewModal.tsx`

### Fase C — CSS e design tokens

| # | P | Tarefa | Arquivos / escopo | Risco | Esforço | Critério de pronto |
|---|---|--------|-------------------|-------|---------|-------------------|
| C1 | 1 | **Deduplicar dark mode** em `index.css` | Blocos `:root[data-theme="dark"]` vs `@media (prefers-color-scheme: dark)` | Baixo | M | ✅ PR-5 jun/2026 — `ui/styles/_theme-dark.css` |
| C2 | 2 | Camada **`ui/styles/`** | `tokens.css`, `overlay.css`, `menu.css`, `composer.css` | Médio | M | ✅ PR-11 jun/2026 — barrel `ui/styles/index.css` |
| C3 | 2 | Varredura **hex → tokens** (chat) | Ver tabela §5 | Baixo | M | ✅ PR-7 core · PR-19 help/tour/agent-home/preview |
| C4 | 3 | Alinhar **`ChatInput__menu`** ao `menu-popover.css` | `ChatInput.css` | Baixo | S | ✅ fundo/borda portaled + posição `composer-panel` |
| C5 | 3 | **`rich-presentation-shared.css`** — revisar duplicação com `ChatRich*.css` | KPI, chart, table | Médio | L | ✅ PR-17 — [`rich-presentation-css.md`](./rich-presentation-css.md) |
| C6 | 4 | Remover aliases legados **`mdc-chat-response-mode__*`** | `composer-option-selector.css` | Baixo | S | ✅ PR-14 jun/2026 |

### Fase D — Estrutura de componentes

| # | P | Tarefa | Escopo | Risco | Esforço |
|---|---|--------|--------|-------|---------|
| D1 | 2 | Mover primitivos overlay para `shared/` | `ModalPortal`, `menuPositionUtils`, `modalPortalTarget` | Baixo | S | ✅ jun/2026 |
| D2 | 2 | **`shared/index.ts`** — exportar tudo que for público | Barrel único | Baixo | S | ✅ PR-16 jun/2026 |
| D3 | 3 | Agrupar features em subpastas | `message/`, `presentation/`, `workspace/`, `composer/` | Alto | L | ✅ PR-18–20 — `presentation/`, `composer/`, `message/`, `workspace/` |
| D4 | 3 | Paridade admin ↔ chat | Copiar padrão `AdminFileDropzone` → wrappers workspace | Médio | M | ✅ PR-19 — CSS de campo unificado em `workspaceFileIngest.css` |
| D5 | 4 | Documentar **quando criar primitivo** | Este doc + `admin/README.md` | Baixo | S | ✅ PR-17 jun/2026 — §12 roadmap + admin/README |

### Fase E — Responsividade e mobile

| # | P | Tarefa | Escopo | Critério de pronto |
|---|---|--------|--------|-------------------|
| E1 | 1 | Checklist composer (selectors, +, mention) | Viewport 390×844, 360×640 | ✅ testes menuPositionUtils jun/2026 |
| E2 | 2 | Toolbar composer em **360px** | `ChatInput.css` `@media (max-width: 360px)` | ✅ wrap flex já presente |
| E3 | 2 | Modais **sheet** no mobile | `ChatModal` + `modal-layer.css` | ✅ PR-15 `mobileLayout` |
| E4 | 3 | Tabelas rich presentation | `ChatRichTable`, `DataTable` patterns | scroll horizontal intencional ou card mode | ✅ PR-17 — card mode ≤768px + `data-label` |
| E5 | 3 | Admin shell mobile | Já parcial em `workspace-responsive.css` | Validar abas e tabelas admin | ✅ PR-18 — card mode AdminDataTable + tab header mobile |

### Fase F — Testes e qualidade

| # | P | Tarefa | Escopo |
|---|---|--------|--------|
| F1 | 1 | Testes **`menuPositionUtils`** | Cobrir flip horizontal action menu + edge cases viewport | ✅ PR-16 jun/2026 |
| F2 | 2 | Testes **`ComposerOptionSelector`** | Render, seleção, aria (vitest + RTL se adotado) | ✅ PR-15 jun/2026 |
| F3 | 2 | **`npm run build`** no CI por PR | Regra `plugins-frontend-build.mdc` | ✅ PR-20 — workflow `minha-delpi-ai-api-presentation.yml` |
| F4 | 3 | Snapshot visual manual | Checklist §7 após cada fase A/B |

---

## 5. Inventário — cores hardcoded a migrar

Priorizar arquivos **fora** de `:root` (tokens de marca na raiz são aceitáveis).

| Arquivo | Problema | Token sugerido | Status |
|---------|----------|----------------|--------|
| `ChatDecisionCard.css` | `#dcfce7`, `#166534`, etc. | `--mdc-success` + `color-mix` | ✅ PR-21+ |
| `workspaceFileIngest.css` | Gradientes `#4f8df7`, `#f06a5b` | `--mdc-primary`, `--mdc-danger`, `--mdc-success` | ✅ PR-19 |
| `ChatAttachmentCard.css` | `#c0392b` | `--mdc-danger` | ✅ PR-7 |
| `ChatRichChart.css` / TS heatmap | `#93c5fd`, `#1d4ed8` | `--mdc-chart-series-*` via `resolveChartSeriesColor` | ✅ PR-42 |
| `ChatRichTree.css` badges | `#2563eb`, `#7c3aed`, `#059669` | `--mdc-chart-series-*` | ✅ PR-42 |
| `shared/IngestProgressIndicator.css` | Fallbacks Google `#1a73e8` | `--mdc-primary` | ✅ PR-19 |
| `admin/overview/AdminOverviewTab.css` | `#2563eb`, `#5c6578` | `--mdc-primary`, `--mdc-text-muted` | ✅ PR-18 |

---

## 6. Inventário — duplicação conhecida

| Padrão | Ocorrências | Canônico alvo |
|--------|-------------|---------------|
| Selector pill + listbox | ~~2~~ → 1 | `ComposerOptionSelector` ✅ |
| Portal + posição + Escape | 4+ menus | `AnchoredMenuPortal` ✅ (parcial) |
| Menu ícone + label + danger | Conversation, ProjectCard, TableRow | `ActionMenuPanel` ✅ (parcial) |
| Scrim + panel centrado | 14 modais | `ChatModal` ✅ |
| Sombra popover `#000 28%` | Input menu, mention, legado | `--mdc-popover-shadow` ✅ (parcial) |
| `canUsePortal` + `useLayoutEffect` | Vários | `useAnchoredMenuLayout` ✅ |

---

## 7. Checklist de validação (cada PR de UI)

- [ ] Claro **e** escuro (`data-theme` no portal)
- [ ] Desktop (≥1024px) e mobile (≤768px, ≤480px)
- [ ] Composer no rodapé — menus não cortados
- [ ] `#mdc-modal-root` — overlay não cobre sidebar do host
- [ ] `npm run build` ok
- [ ] Testes unitários do escopo passando
- [ ] Nenhum texto PT novo hardcoded fora de `src/content/` (sync API quando aplicável)

---

## 8. Ordem recomendada de PRs

```text
PR-1 ✅  shared/ + ComposerOptionSelector + AnchoredMenuPortal + migrações selectors/cards
PR-2 ✅  A1 — Menu 「+」 do ChatInput em portal (`ChatInputPlusMenu`, `composer-panel`)
PR-3 ✅  B1 + B2 — ChatModal + Confirm/Alert/Prompt
PR-4 ✅  A3 — ChatTableRowMenu unificado
PR-5 ✅  C1 — Dark mode deduplicado
PR-6 ✅  B3 — demais diálogos médios
PR-7 ✅  C3 — Varredura hex (chat core)
PR-8 ✅  A6 — Onboarding tour portal
PR-9 ✅  B4 — ChatAddContextDialog → ChatModal
PR-10 ✅  B4 — ChatHelpPanel → ChatModal (drawer-end)
PR-11 ✅  C2 — ui/styles/ barrel + fix posição menu 「+」
PR-12 ✅  B4/B5 — Canvas, Expand, AttachmentPreview, WebSearch, ProjectHome settings
PR-13 ✅  B7/D1 — ModalPortal + modalPortalTarget em shared/overlay; backdrop genérico
PR-14 ✅  C6 — remove aliases mdc-chat-response-mode__*; fix anchorAbove menus
PR-15 ✅  B6/D1/F2 — modal-layer enxuto, menuPositionUtils em shared/overlay, testes ComposerOptionSelector
PR-16 ✅  A7/D2/E1/F1 — DropdownMenuTrigger, testes mobile composer, flip action menu
PR-17 ✅  C5/D5/E4 — rich-presentation-shared consolidado, doc primitivos, tabelas mobile card mode
PR-18 ✅  D3/E5 — pasta presentation/ + admin mobile (AdminDataTable card mode)
PR-19 ✅  D3 composer/ + C3 hex + D4 dropzone paridade
PR-20 ✅  D3 message/workspace + F3 CI build gate
PR-21 ✅  C3 hex chips · message/ useAssistantContentSegments + AssistantStackSection · docs component-structure
PR-22 ✅  message/ ChatMessageList + timeline + ChatThinkingDots
PR-23 ✅  message/ assistantProseRendering (canônico prosa)
PR-24 ✅  imports canônicos message/* + shared/overlay; preview builder usa chat-landing
PR-25 ✅  presentation/segmentBuilders/ (stack, renderPlan, visual collector, …)
PR-26 ✅  remoção stubs legados + CI paths + barrel composer
PR-27 ✅  presentation/pipeline/ — módulos presentation*.ts da raiz
PR-28 ✅  regressão stack/layout — explicitSessionFormat, presentation.role, decision.layoutMode
PR-29 ✅  chart builders → presentation/pipeline/ (axis, aggregation, build-from-table)
PR-30 ✅  tree/chart normalize → pipeline; doc hub; remove stub CSS raiz
PR-31 ✅  humanizedCoverageNotice → message/
PR-32 ✅  chatAssistantMessageActions → message/; chartExplain → pipeline/
PR-33 ✅  chatMarkdown → message/ (prosa + strip section markers)
PR-34 ✅  testFixtures → message/; tableCellFormatting → presentation/
PR-35 ✅  shell/ — ChatSidebar*, ChatContextBar, ChatContextTopbar, chatSidebarUtils
PR-36 ✅  workspace/ — ChatProjectHome, ChatProjectCard, ChatProjectCreateModal, ChatAddContextDialog
PR-37 ✅  message/ — InteractivityBlock, Sources, DecisionCard, ChatMarkdown, MermaidBlock
PR-38 ✅  presentation/export/ — exportUtils, chartPngExport, chartCanvasMarkdown, dashboardExportCsv
PR-39 ✅  presentation/presentationMetadataReaders.ts — get*FromToolCalls, render plan, coverage
PR-40 ✅  presentation/presentationMarkdownNormalization.ts — strip*, tablePresentationToMarkdown
PR-41 ✅  presentation/presentationPairResolver.ts — pair resolver, merge tabelas/gráficos
PR-42 ✅  hex bare em apresentação rica + máscaras; fallbacks `var(--token)` residual aceito
PR-43 ✅  presentation/ — export/copy buttons, chartPresentationUx, chartViewState, chatDrillDown
PR-44 ✅  shared/modal/ — alert/confirm/prompt dialogs + hooks use*Dialog
PR-45 ✅  canvas/ — ChatCanvas, ChatInlineCanvas, chatCanvas utils
PR-46 ✅  shared/modal MemoryUsed; shell HelpPanel; workspace AttachmentPreview + WebSearch
PR-47 ✅  shared/menus TableRowMenu; canvas ExpandModal; message edit/streaming/feedback panels
PR-48 ✅  shell ConversationMenu + OnboardingTour; message empty/follow-up/action panels
PR-49 ✅  shared layout primitives; shell list item; workspace attachment/agent; message trust/debug
PR-50 ✅  overlay CSS → ui/styles/; DropdownMenuTrigger em ContextTopbar + ProjectHome
PR-51 ✅  chatClipboard + testes hub → presentation/; raiz só `chatPresentation.ts`
PR-52 ✅  barrels presentation/; Fase H encerrada no roadmap
PR-53 ✅  DropdownMenuTrigger no menu assistente; agentBuilder/; hex modais
```

### Fase G — Limpeza da raiz (PR-34+)

Meta: reduzir **55 TS/TSX + ~37 CSS** na raiz (jun/2026) para **shell + hub + orquestração de página**.

| PR | Escopo | Status |
|----|--------|--------|
| PR-34 | `testFixtures` → `message/`; `tableCellFormatting` → `presentation/` | ✅ |
| PR-35 | `shell/` — `ChatSidebar*`, `ChatContextBar`, `ChatContextTopbar` | ✅ |
| PR-36 | `workspace/` — `ChatProjectHome`, `ChatProjectCard`, `ChatAddContextDialog`, modais projeto | ✅ |
| PR-37 | `message/` — `ChatInteractivityBlock`, `ChatSources`, `ChatDecisionCard`, `ChatMarkdown.tsx`, `ChatMermaidBlock` | ✅ |
| PR-38 | `presentation/export/` — `exportUtils`, `chartPngExport`, `chartCanvasMarkdown`, `dashboardExportCsv` | ✅ |
| PR-39 | `presentationMetadataReaders.ts` — readers metadata puros | ✅ |
| PR-40 | `presentationMarkdownNormalization.ts` — strip*, table markdown | ✅ |
| PR-41 | `presentationPairResolver.ts` — pair resolver, merge tabelas | ✅ |
| PR-42 | C3 hex residual + checklist F4 §7 | ✅ |

Definição **100% refactor estrutural**: Fase G (PR-42) + **Fase H** (PR-46–51) ✅ — hub fatiado, raiz só `chatPresentation.ts`, CSS em `ui/styles/` e feature folders.

Ver matriz completa em [`component-structure.md`](./component-structure.md) e [`chat-presentation-hub.md`](./chat-presentation-hub.md).

### Fases concluídas (jun/2026)

Fases **A–F** entregues (PR-1–26). **Pipeline + message** (PR-27–34). **Fase G** (PR-35–42). **Fase H** (PR-46–51): limpeza da raiz, overlay CSS, `DropdownMenuTrigger`, hub isolado ✅.

---

## 9. Anti-padrões (não fazer)

- `createPortal(..., document.body)` para UI do chat (exceto tour legado até A6).
- Copiar bloco de menu com `MENU_WIDTH` / listeners inline.
- Nova modal com classe `-backdrop` listada manualmente em `modal-layer.css` sem passar por `ChatModal`.
- Cores `#fff` / `#000` para superfície ou texto de componente.
- Lógica de apresentação/intenção no MFE que deveria vir da API (`metadata`, pipeline).
- Patch só no MFE para comportamento definido na API sem contrato.

---

## 10. Referências

| Recurso | Caminho |
|---------|---------|
| Tokens plugin | `src/index.css` |
| Styles barrel | `src/ui/styles/index.css` |
| Overlay layer | `src/ui/styles/overlay.css` → `chat-overlay-layer.css`, `modal-layer.css` |
| Modal layer | `src/ui/styles/modal-layer.css` |
| Posicionamento | `src/ui/components/shared/overlay/menuPositionUtils.ts` |
| Shared barrel | `src/ui/components/shared/index.ts` (+ `DropdownMenuTrigger`) |
| Portal target | `src/ui/components/shared/overlay/modalPortalTarget.ts` |
| Admin primitivos | `src/ui/components/admin/shared/` |
| Regra design system | `.cursor/rules/plugins-visual-design-system.mdc` |
| Build obrigatório | `.cursor/rules/plugins-frontend-build.mdc` |
| Prosa/markdown assistente | `message/assistantProseRendering.ts` (canônico MFE) |
| Hub metadata apresentação | [`chat-presentation-hub.md`](./chat-presentation-hub.md) |
| Export apresentação (CSV/XLSX/PDF/PNG) | `presentation/export/` — ver hub § já extraído |
| Apresentação rica API | `chat-assistant-content-presentation.md` (API) |
| CSS apresentação rica (MFE) | `docs/rich-presentation-css.md` |
| Estrutura feature folders | `docs/component-structure.md` |

---

## 11. Métricas de conclusão (definição de “feito”)

| Métrica | Hoje (jun/2026) | Meta |
|---------|-----------------|------|
| PRs estruturais entregues | 52 (Fases A–H) | Fase H ✅ |
| Arquivos TS/TSX na raiz `components/` | 1 | hub `chatPresentation.ts` ✅ |
| Arquivos CSS na raiz `components/` | 0 | co-localizados com feature ou `ui/styles/` ✅ |
| Módulos em `presentation/pipeline/` | 57 arquivos TS/TSX (pasta inteira) | estável; hub fatiado PR-39–41 |
| Módulos em `presentation/export/` | 8 arquivos TS/TSX | exportUtils, PNG, canvas markdown, dashboard CSV ✅ |
| Módulos em `message/` | 59 arquivos TS/TSX | empty/follow-up/actions + InteractivityBlock, Sources, markdown ✅ |
| Componentes em `shared/` (excl. admin) | 28 arquivos | ≥15 (overlay + modal + menus + layout) ✅ |
| Modais usando `ChatModal` | 14 / ~14 | 14 / 14 ✅ |
| Menus com portal canônico | ~8 / ~8 | 8 / 8 ✅ |
| Arquivos CSS com hex bare (superfície/texto, chat) | 0 | 0 ✅ |
| Arquivos CSS com hex em fallback `var(--*, #…)` | 0 em `shared/modal/` | tokens em `index.css` ✅ |
| Duplicação selector composer | 0 | 0 ✅ |
| Testes CI apresentação (vitest) | 49 / 49 pass | verde em todo PR pipeline |

---

## 12. Quando criar primitivo (`shared/`)

Use este checklist antes de extrair ou adicionar componente em `ui/components/shared/`:

| Critério | Pergunta |
|----------|----------|
| Repetição | O padrão aparece em **2+** features (menus, modais, selectors)? |
| Contrato | Props genéricas (`open`, `items`, `anchorRef`) sem domínio de chat? |
| Pipeline | A regra **não** deveria estar na API (`metadata`, pipeline)? |
| Portal/tokens | Usa `resolveOverlayPortalContainer()` e `--mdc-*`? |

**Extrair** quando todas forem sim. **Não extrair** para `if` de uma tela, wrapper de uma linha ou lógica que pertence ao pipeline da API.

Namespaces:

- **Chat:** `ui/components/shared/` — overlay, modal, composer, menus
- **Admin:** `ui/components/admin/shared/` — KPI, tabela, header de aba
- **Apresentação rica (CSS):** `rich-presentation-shared.css` — ver [`rich-presentation-css.md`](./rich-presentation-css.md)

---

*Manter este documento atualizado ao fechar cada PR da fase correspondente.*
