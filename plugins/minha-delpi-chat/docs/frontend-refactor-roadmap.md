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
├── styles/                    # (futuro) tokens + overlay + menu — barrel único
├── layout/                    # chat-layout, workspace-responsive, transitions
├── components/
│   ├── shared/                # primitivos cross-feature
│   │   ├── overlay/           # AnchoredMenuPortal, useAnchoredMenuLayout
│   │   ├── composer/          # ComposerOptionSelector
│   │   ├── menus/             # ActionMenuPanel
│   │   └── modal/             # (futuro) ChatModal
│   ├── admin/shared/          # já maduro — referência
│   └── [feature]/             # ChatMessageList, ChatRichChart, …
```

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

Classes `mdc-chat-response-mode__*` ainda válidas via seletores duplicados em `composer-option-selector.css`. Remover quando não houver referências externas.

---

## 4. Backlog completo

Legenda: **P** prioridade (1 = mais urgente), **Risco** baixo / médio / alto, **Esforço** S / M / L.

### Fase A — Overlays e menus (alto impacto UX)

| # | P | Tarefa | Arquivos / escopo | Risco | Esforço | Critério de pronto |
|---|---|--------|-------------------|-------|---------|-------------------|
| A1 | 1 | Menu **「+」** do composer em portal | `ChatInputPlusMenu`, `ChatInput.tsx` | Médio | M | ✅ PR-2 jun/2026 |
| A2 | 1 | Unificar **mention menu** com tokens popover | `ChatComposerMentionMenu.tsx/css` | Baixo | S | Usa `--mdc-popover-shadow`; considerar portal se ainda cortar |
| A3 | 2 | **`ChatTableRowMenu`** sobre `AnchoredMenuPortal` | `ChatTableRowMenu.tsx` | Médio | M | ✅ PR-4 jun/2026 — placement `context-menu`, shell `overlay` |
| A4 | 2 | **`ChatAssistantMessageMenu`** idem | `ChatAssistantMessageMenu.tsx` | Baixo | S | Consome `ActionMenuPanel` ou wrapper |
| A5 | 2 | **`ChatContextBar`** chip menu | `ChatContextBar.tsx` | Baixo | S | Já usa `ChatTableRowMenu` — validar após A3 |
| A6 | 3 | **`ChatOnboardingTour`** alinhar portal | `ChatOnboardingTour.tsx` (hoje `document.body`) | Médio | M | ✅ PR-8 jun/2026 — `ModalPortal` + coords contidas |
| A7 | 3 | Extrair **`DropdownMenuTrigger`** opcional | `shared/menus/` | Baixo | S | Padrão botão ⋯ + `AnchoredMenuPortal` para cards/listas |

### Fase B — Modais e diálogos

| # | P | Tarefa | Arquivos / escopo | Risco | Esforço | Critério de pronto |
|---|---|--------|-------------------|-------|---------|-------------------|
| B1 | 1 | Criar **`ChatModal`** compound | `shared/modal/ChatModal.tsx`, `chat-modal.css` | Médio | L | ✅ PR-3 jun/2026 |
| B2 | 1 | Migrar diálogos simples | `ChatConfirmDialog`, `ChatAlertDialog`, `ChatPromptDialog` | Médio | M | ✅ PR-3 jun/2026 |
| B3 | 2 | Migrar diálogos médios | `ChatShortcutPromptDialog`, `ChatSidebarArchivedDialog`, `ChatMemoryUsedDialog` | Médio | M | ✅ PR-6 jun/2026 |
| B4 | 2 | Migrar painéis grandes | `ChatAddContextDialog`, `ChatHelpPanel`, `ChatCanvas`, `ChatExpandModal` | Alto | L | `ChatAddContextDialog` ✅ PR-9 · `ChatHelpPanel` ✅ jun/2026 |
| B5 | 2 | Migrar modais workspace | `ChatProjectCreateModal`, `ChatAttachmentPreviewModal`, inline em `ChatProjectHome` | Médio | M | |
| B6 | 3 | Reduzir **`modal-layer.css`** | Listas manuais de `-backdrop` | Médio | M | Usar `data-modal-size` ou classes genéricas `.mdc-chat-modal--*` |
| B7 | 3 | Mover **`ModalPortal`** para `shared/overlay/` | `ModalPortal.tsx`, `modalPortalTarget.ts` | Baixo | S | Re-export na raiz até consumidores migrarem |

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
| C2 | 2 | Camada **`ui/styles/`** | `tokens.css`, `overlay.css`, `menu.css`, `composer.css` | Médio | M | `index.css` só importa barrel; componentes importam feature CSS |
| C3 | 2 | Varredura **hex → tokens** (chat) | Ver tabela §5 | Baixo | M | ✅ PR-7 jun/2026 — inventário §5 migrado |
| C4 | 3 | Alinhar **`ChatInput__menu`** ao `menu-popover.css` | `ChatInput.css` | Baixo | S | Mesma sombra, radius, hover |
| C5 | 3 | **`rich-presentation-shared.css`** — revisar duplicação com `ChatRich*.css` | KPI, chart, table | Médio | L | Documentar o que é compartilhado vs específico |
| C6 | 4 | Remover aliases legados **`mdc-chat-response-mode__*`** | `composer-option-selector.css` | Baixo | S | Só após grep zero referências |

### Fase D — Estrutura de componentes

| # | P | Tarefa | Escopo | Risco | Esforço |
|---|---|--------|--------|-------|---------|
| D1 | 2 | Mover primitivos overlay para `shared/` | `ModalPortal`, `menuPositionUtils`, `modalPortalTarget` | Baixo | S |
| D2 | 2 | **`shared/index.ts`** — exportar tudo que for público | Barrel único | Baixo | S |
| D3 | 3 | Agrupar features em subpastas | `message/`, `presentation/`, `workspace/`, `composer/` | Alto | L | Só com re-exports para não quebrar imports |
| D4 | 3 | Paridade admin ↔ chat | Copiar padrão `AdminFileDropzone` → wrappers workspace | Médio | M |
| D5 | 4 | Documentar **quando criar primitivo** | Este doc + `admin/README.md` | Baixo | S |

### Fase E — Responsividade e mobile

| # | P | Tarefa | Escopo | Critério de pronto |
|---|---|--------|--------|-------------------|
| E1 | 1 | Checklist composer (selectors, +, mention) | Viewport 390×844, 360×640 | Menus roláveis, sem corte superior |
| E2 | 2 | Toolbar composer em **360px** | `ChatInput.css` `@media (max-width: 360px)` | wrap sem overflow horizontal |
| E3 | 2 | Modais **sheet** no mobile | `ChatModal` + `modal-layer.css` | Painel full-width inferior ou centrado com padding safe-area |
| E4 | 3 | Tabelas rich presentation | `ChatRichTable`, `DataTable` patterns | scroll horizontal intencional ou card mode |
| E5 | 3 | Admin shell mobile | Já parcial em `workspace-responsive.css` | Validar abas e tabelas admin |

### Fase F — Testes e qualidade

| # | P | Tarefa | Escopo |
|---|---|--------|--------|
| F1 | 1 | Testes **`menuPositionUtils`** | Cobrir flip horizontal action menu + edge cases viewport |
| F2 | 2 | Testes **`ComposerOptionSelector`** | Render, seleção, aria (vitest + RTL se adotado) |
| F3 | 2 | **`npm run build`** no CI por PR | Regra `plugins-frontend-build.mdc` |
| F4 | 3 | Snapshot visual manual | Checklist §7 após cada fase A/B |

---

## 5. Inventário — cores hardcoded a migrar

Priorizar arquivos **fora** de `:root` (tokens de marca na raiz são aceitáveis).

| Arquivo | Problema | Token sugerido |
|---------|----------|----------------|
| `ChatDecisionCard.css` | `#dcfce7`, `#166534`, etc. | `--mdc-success` + `color-mix` |
| `workspaceFileIngest.css` | Gradientes `#4f8df7`, `#f06a5b` | `--mdc-primary`, `--mdc-danger`, `--mdc-success` |
| `ChatAttachmentCard.css` | `#c0392b` | `--mdc-danger` |
| `ChatRichChart.css` | `#93c5fd`, `#1d4ed8` | `--mdc-chart-series-*` |
| `shared/IngestProgressIndicator.css` | Fallbacks Google `#1a73e8` | `--mdc-primary` sem fallback estranho |
| `admin/overview/AdminOverviewTab.css` | `#2563eb`, `#5c6578` | `--mdc-primary`, `--mdc-text-muted` |

---

## 6. Inventário — duplicação conhecida

| Padrão | Ocorrências | Canônico alvo |
|--------|-------------|---------------|
| Selector pill + listbox | ~~2~~ → 1 | `ComposerOptionSelector` ✅ |
| Portal + posição + Escape | 4+ menus | `AnchoredMenuPortal` ✅ (parcial) |
| Menu ícone + label + danger | Conversation, ProjectCard, TableRow | `ActionMenuPanel` ✅ (parcial) |
| Scrim + panel centrado | 14 modais | `ChatModal` (pendente) |
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
PR-11    C2 — ui/styles/ barrel
```

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
| Overlay layer | `src/ui/components/chat-overlay-layer.css` |
| Modal layer | `src/ui/components/modal-layer.css` |
| Posicionamento | `src/ui/components/menuPositionUtils.ts` |
| Shared barrel | `src/ui/components/shared/index.ts` |
| Admin primitivos | `src/ui/components/admin/shared/` |
| Regra design system | `.cursor/rules/plugins-visual-design-system.mdc` |
| Build obrigatório | `.cursor/rules/plugins-frontend-build.mdc` |
| Prosa/markdown assistente | `assistantProseRendering.ts` (canônico MFE) |
| Apresentação rica API | `chat-assistant-content-presentation.md` (API) |

---

## 11. Métricas de conclusão (definição de “feito”)

| Métrica | Hoje (jun/2026) | Meta |
|---------|-----------------|------|
| Componentes em `shared/` (excl. admin) | 6 arquivos | ≥15 (overlay + modal + menus) |
| Modais usando `ChatModal` | 0 / ~14 | 14 / 14 |
| Menus com portal canônico | ~4 / ~8 | 8 / 8 |
| Arquivos CSS com hex fora de token (chat) | ~10+ | 0 (superfície/texto) |
| Duplicação selector composer | 0 | 0 ✅ |

---

*Manter este documento atualizado ao fechar cada PR da fase correspondente.*
