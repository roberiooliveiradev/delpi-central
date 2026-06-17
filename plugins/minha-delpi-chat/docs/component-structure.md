# Estrutura de componentes — Minha DELPI Chat (MFE)

> Atualizado em **16/06/2026** após PR-1–37 ([`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md)).

## Mapa de pastas feature

```text
src/ui/components/
├── shared/              # Primitivos cross-feature (overlay, modal, menus, composer base)
│   ├── overlay/         # AnchoredMenuPortal, ModalPortal, menuPositionUtils
│   ├── modal/           # ChatModal
│   ├── composer/        # ComposerOptionSelector, ChatInputPlusMenu
│   └── menus/           # ActionMenuPanel, DropdownMenuTrigger
├── presentation/        # Apresentação rica (ChatRich*, segmentBuilders/, pipeline/, CSS)
├── composer/            # ChatInput, mention menu, selectors formato/modo
├── message/             # Conteúdo do assistente + timeline (ChatMessageList)
├── workspace/           # Arquivos de projeto/agente (dropzone, cards, ingest CSS)
├── shell/               # Sidebar, ContextBar, ContextTopbar
├── admin/               # Painel administrativo (shell + abas modulares)
└── [raiz]               # Hub chatPresentation, modais finos, export/chart UX, etc.
```

Barrels públicos:

| Pasta | Barrel | Consumo preferido |
|-------|--------|-------------------|
| `shared/` | `shared/index.ts` | `import { ChatModal } from "./shared"` |
| `presentation/` | `presentation/index.ts` | `import { ChatRichTable } from "./presentation"` |
| `presentation/pipeline/` | `presentation/pipeline/index.ts` | stack, labels, chart/tree normalize |
| `composer/` | `composer/index.ts` | `import { ChatInput } from "./composer"` |
| `message/` | `message/index.ts` | `import { ChatAssistantContent } from "./message"` |
| `workspace/` | `workspace/index.ts` | `import { WorkspaceFileDropzone } from "./workspace"` |
| `shell/` | `shell/index.ts` | `import { ChatSidebar } from "./shell"` |

## Re-exports legados

Removidos em **PR-26**. Usar apenas barrels e pastas feature.

**PR-30:** removido stub CSS `components/rich-presentation-shared.css` — importar `presentation/rich-presentation-shared.css` diretamente.

## Hub `chatPresentation.ts` (raiz, intencional)

Orquestra metadata da API → segmentos/UI. **Não mover** o monolito sem fatiar por domínio (evita ciclo `message/` ↔ `presentation/`).

Documentação completa: [`chat-presentation-hub.md`](./chat-presentation-hub.md).

## CSS compartilhado

| Camada | Arquivo |
|--------|---------|
| Tokens plugin | `src/index.css` |
| Tema escuro | `src/ui/styles/_theme-dark.css` |
| Barrel styles | `src/ui/styles/index.css` |
| Apresentação rica | `presentation/rich-presentation-shared.css` — ver [`rich-presentation-css.md`](./rich-presentation-css.md) |
| Segment builders | `presentation/segmentBuilders/` — stack, renderPlan, visual collector |
| Pipeline apresentação | `presentation/pipeline/` — stack, dedup, labels, chart/tree builders, normalize |
| Overlay/modal | `shared/overlay/*`, `modal-layer.css` |
| Responsivo global | `src/ui/layout/workspace-responsive.css` |

## Raiz — o que permanece e o que saiu

| Permanece (hub / UX) | Motivo |
|----------------------|--------|
| `chatPresentation.ts` | Hub metadata ↔ UI — ver hub doc |
| `chartPngExport.ts`, `chartCanvasMarkdown.ts` | Export/canvas, não pipeline de dados |
| Modais finos, sidebar, export utils | Cross-feature |

**Em `presentation/pipeline/` (PR-27–30, PR-32):** stack plan, dedup, metadata, labels, telemetry, chart builders, tree utils, normalize, `chartExplain`.

**Em `presentation/` (PR-34):** `tableCellFormatting.ts` (células KPI/tabela).

**Em `message/` (PR-21–23, PR-31–34, PR-37):** segmentos, `ChatMessageList`, prosa, coverage, markdown (`chatMarkdown` + `ChatMarkdown`), sources, decision card, interactivity, mermaid.

**Em `shell/` (PR-35):** `ChatSidebar*`, `ChatContextBar`, `ChatContextTopbar`, `chatSidebarUtils`, `chatContextChipActions`.

**Em `workspace/` (PR-18–20, PR-36):** dropzone/cards/ingest, `ChatProjectHome`, `ChatProjectCard`, `ChatProjectCreateModal`, `ChatAddContextDialog`.

## Fase G — limpeza da raiz (pendente)

| PR | Destino | Arquivos-alvo |
|----|---------|---------------|
| PR-35 | `shell/` | Sidebar, ContextBar, ContextTopbar | ✅ |
| PR-36 | `workspace/` | ProjectHome, ProjectCard, modais projeto | ✅ |
| PR-37 | `message/` | InteractivityBlock, Sources, DecisionCard, ChatMarkdown, MermaidBlock | ✅ |
| PR-38 | `presentation/export/` | exportUtils, chartPngExport, chartCanvasMarkdown |
| PR-39–41 | fatias do hub | ver [`chat-presentation-hub.md`](./chat-presentation-hub.md) |

## Referências

- Roadmap: [`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md)
- Hub apresentação: [`chat-presentation-hub.md`](./chat-presentation-hub.md)
- Primitivos admin: [`admin/README.md`](../src/ui/components/admin/README.md)
