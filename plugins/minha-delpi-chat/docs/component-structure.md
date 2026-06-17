# Estrutura de componentes — Minha DELPI Chat (MFE)

> Atualizado em **16/06/2026** após PR-1–20 ([`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md)).

## Mapa de pastas feature

```text
src/ui/components/
├── shared/              # Primitivos cross-feature (overlay, modal, menus, composer base)
│   ├── overlay/         # AnchoredMenuPortal, ModalPortal, menuPositionUtils
│   ├── modal/           # ChatModal
│   ├── composer/        # ComposerOptionSelector, ChatInputPlusMenu
│   └── menus/           # ActionMenuPanel, DropdownMenuTrigger
├── presentation/        # Apresentação rica (tabela, gráfico, KPI, árvore, dashboard)
├── composer/            # ChatInput, mention menu, selectors formato/modo
├── message/             # Conteúdo do assistente (segmentos, registry, chrome)
├── workspace/           # Arquivos de projeto/agente (dropzone, cards, ingest CSS)
├── admin/               # Painel administrativo (shell + abas modulares)
└── [legado na raiz]     # ChatMessageList, ChatSidebar, modais finos, etc.
```

Barrels públicos:

| Pasta | Barrel | Consumo preferido |
|-------|--------|-------------------|
| `shared/` | `shared/index.ts` | `import { ChatModal } from "./shared"` |
| `presentation/` | `presentation/index.ts` | `import { ChatRichTable } from "./presentation"` |
| `composer/` | `composer/index.ts` | `import { ChatInput } from "./composer"` |
| `message/` | `message/index.ts` | `import { ChatAssistantContent } from "./message"` |
| `workspace/` | `workspace/index.ts` | `import { WorkspaceFileDropzone } from "./workspace"` |

## Re-exports legados (compatibilidade)

Arquivos na **raiz** de `components/` que só reexportam — **não** adicionar lógica nova:

| Stub | Destino canônico |
|------|------------------|
| `ChatRich*.tsx` | `presentation/` |
| `ChatInput.tsx` | `composer/` |
| `ChatAssistantContent.tsx` | `message/` |
| `assistantContent*.ts` | `message/` |
| `useAssistantContentSegments.ts` | `message/` |
| `AssistantStackSection.tsx` | `message/` |
| `workspace-files/*` | `workspace/` |
| `rich-presentation-shared.css` | `presentation/rich-presentation-shared.css` |
| `menuPositionUtils.ts` | `shared/overlay/menuPositionUtils.ts` |

Novos imports devem usar o caminho canônico (pasta feature ou barrel).

## CSS compartilhado

| Camada | Arquivo |
|--------|---------|
| Tokens plugin | `src/index.css` |
| Tema escuro | `src/ui/styles/_theme-dark.css` |
| Barrel styles | `src/ui/styles/index.css` |
| Apresentação rica | `presentation/rich-presentation-shared.css` — ver [`rich-presentation-css.md`](./rich-presentation-css.md) |
| Overlay/modal | `shared/overlay/*`, `modal-layer.css` |
| Responsivo global | `src/ui/layout/workspace-responsive.css` |

## O que ainda fica na raiz (PR-21+)

Candidatos futuros a `message/`:

- `ChatMessageList.tsx` (+ CSS) — timeline principal
- `assistantProseRendering.ts`, `chatPresentation.ts` (lógica de apresentação consumida pelo message)

**Já em `message/` (PR-21):** `useAssistantContentSegments`, `AssistantStackSection`.

Candidatos futuros a `workspace/`:

- `ChatProjectHome.tsx`, `ChatAddContextDialog.tsx` (parcial — já consomem `workspace/`)

## Referências

- Roadmap completo: [`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md)
- Quando criar primitivo: roadmap §12 + [`admin/README.md`](../src/ui/components/admin/README.md)
