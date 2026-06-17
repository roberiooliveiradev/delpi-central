# Estrutura de componentes — Minha DELPI Chat (MFE)

> Atualizado em **16/06/2026** após PR-1–26 ([`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md)).

## Mapa de pastas feature

```text
src/ui/components/
├── shared/              # Primitivos cross-feature (overlay, modal, menus, composer base)
│   ├── overlay/         # AnchoredMenuPortal, ModalPortal, menuPositionUtils
│   ├── modal/           # ChatModal
│   ├── composer/        # ComposerOptionSelector, ChatInputPlusMenu
│   └── menus/           # ActionMenuPanel, DropdownMenuTrigger
├── presentation/        # Apresentação rica (ChatRich*, segmentBuilders/, CSS)
├── composer/            # ChatInput, mention menu, selectors formato/modo
├── message/             # Conteúdo do assistente + timeline (ChatMessageList)
├── workspace/           # Arquivos de projeto/agente (dropzone, cards, ingest CSS)
├── admin/               # Painel administrativo (shell + abas modulares)
└── [legado na raiz]     # ChatSidebar, modais finos, chatPresentation, etc.
```

Barrels públicos:

| Pasta | Barrel | Consumo preferido |
|-------|--------|-------------------|
| `shared/` | `shared/index.ts` | `import { ChatModal } from "./shared"` |
| `presentation/` | `presentation/index.ts` | `import { ChatRichTable } from "./presentation"` |
| `composer/` | `composer/index.ts` | `import { ChatInput } from "./composer"` |
| `message/` | `message/index.ts` | `import { ChatAssistantContent } from "./message"` |
| `workspace/` | `workspace/index.ts` | `import { WorkspaceFileDropzone } from "./workspace"` |

## Re-exports legados

Removidos em **PR-26**. Usar apenas barrels e pastas feature (`message/`, `presentation/`, `composer/`, `workspace/`, `shared/`).

Exceção CSS: `rich-presentation-shared.css` na raiz ainda reexporta `presentation/rich-presentation-shared.css` (consumido por `ChatActionResults.css`).

## CSS compartilhado

| Camada | Arquivo |
|--------|---------|
| Tokens plugin | `src/index.css` |
| Tema escuro | `src/ui/styles/_theme-dark.css` |
| Barrel styles | `src/ui/styles/index.css` |
| Apresentação rica | `presentation/rich-presentation-shared.css` — ver [`rich-presentation-css.md`](./rich-presentation-css.md) |
| Segment builders | `presentation/segmentBuilders/` — stack, renderPlan, visual collector |
| Overlay/modal | `shared/overlay/*`, `modal-layer.css` |
| Responsivo global | `src/ui/layout/workspace-responsive.css` |

## O que ainda fica na raiz (PR-22+)

Candidatos futuros a `message/`:

- `chatPresentation.ts` (compartilhado com `presentation/` e builders na raiz)

**Já em `message/` (PR-21–23):** segmentos, `ChatMessageList`, `assistantProseRendering`.

Candidatos futuros a `workspace/`:

- `ChatProjectHome.tsx`, `ChatAddContextDialog.tsx` (parcial — já consomem `workspace/`)

## Referências

- Roadmap completo: [`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md)
- Quando criar primitivo: roadmap §12 + [`admin/README.md`](../src/ui/components/admin/README.md)
