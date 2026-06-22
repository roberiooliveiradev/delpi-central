# Estrutura de componentes — Minha DELPI Chat (MFE)

> Atualizado em **22/06/2026** — módulo `src/export/` (exportação centralizada + PDF certificado DELPI).

## Mapa de pastas feature

```text
src/
├── export/              # Módulo canônico: CSV/XLSX/PDF/PNG, dispatch, PDF certificado DELPI (jun/2026)
│   └── pdf/             # HTML + impressão (logo, layout desenho = layout tabela)
└── ui/
    └── components/
        ├── shared/              # Primitivos cross-feature (overlay, modal, menus, composer base)
        │   ├── overlay/
        │   ├── modal/
        │   ├── composer/
        │   └── menus/
        ├── presentation/        # ChatRich*, pipeline/, export/ (payloads), CSS
        │   ├── pipeline/
        │   ├── export/          # CSV/XLSX, PNG, lousa; PDF → src/export/pdf/
        │   └── segmentBuilders/
        ├── composer/
        ├── message/
        ├── workspace/
        ├── shell/
        ├── canvas/
        ├── admin/
        └── [raiz ui/components] # Hub `chatPresentation.ts` apenas (PR-51)
```

Barrels públicos:

| Pasta | Barrel | Consumo preferido |
|-------|--------|-------------------|
| `src/export/` | `export/index.ts` | `import { runChatExport, exportPresentation } from "../export"` |
| `shared/` | `shared/index.ts` | `import { ChatModal } from "./shared"` |
| `presentation/` | `presentation/index.ts` | `import { ChatRichTable } from "./presentation"` |
| `presentation/export/` | `presentation/export/index.ts` | `import { exportPresentation } from "./presentation/export"` |
| `presentation/pipeline/` | `presentation/pipeline/index.ts` | stack, labels, chart/tree normalize |
| `composer/` | `composer/index.ts` | `import { ChatInput } from "./composer"` |
| `message/` | `message/index.ts` | `import { ChatAssistantContent } from "./message"` |
| `workspace/` | `workspace/index.ts` | `import { WorkspaceFileDropzone } from "./workspace"` |
| `shell/` | `shell/index.ts` | `import { ChatSidebar } from "./shell"` |
| `canvas/` | `canvas/index.ts` | `import { ChatCanvas } from "./canvas"` |

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
| Modais finos, sidebar, export buttons | Cross-feature |

**Em `presentation/` (PR-34, PR-38–41, PR-43):** `tableCellFormatting`, metadata readers, markdown normalization, pair resolver, export/copy buttons, `chartPresentationUx`, `chartViewState`, `chatDrillDown`.

**Em `presentation/export/` (PR-38):** `exportUtils`, `chartPngExport`, `chartCanvasMarkdown`, `dashboardExportCsv` — PDF delega a `src/export/pdf/`.

**Em `src/export/` (jun/2026):** `runChatExport`, `ChatExportButtons`, primitivos compartilhados, `pdf/` (layout certificado DELPI). Ver [`export.md`](./export.md).

**Em `message/` (PR-21–23, PR-31–34, PR-37):** segmentos, `ChatMessageList`, prosa, coverage, markdown (`chatMarkdown` + `ChatMarkdown`), sources, decision card, interactivity, mermaid.

**Em `shell/` (PR-35):** `ChatSidebar*`, `ChatContextBar`, `ChatContextTopbar`, `chatSidebarUtils`, `chatContextChipActions`.

**Em `workspace/` (PR-18–20, PR-36):** dropzone/cards/ingest, `ChatProjectHome`, `ChatProjectCard`, `ChatProjectCreateModal`, `ChatAddContextDialog`.

## Fase G — limpeza da raiz (concluída)

| PR | Destino | Arquivos-alvo |
|----|---------|---------------|
| PR-35 | `shell/` | Sidebar, ContextBar, ContextTopbar | ✅ |
| PR-36 | `workspace/` | ProjectHome, ProjectCard, modais projeto | ✅ |
| PR-37 | `message/` | InteractivityBlock, Sources, DecisionCard, ChatMarkdown, MermaidBlock | ✅ |
| PR-38 | `presentation/export/` | exportUtils, chartPngExport, chartCanvasMarkdown, dashboardExportCsv | ✅ |
| PR-39 | `presentationMetadataReaders.ts` | readers metadata puros | ✅ |
| PR-40 | `presentationMarkdownNormalization.ts` | strip*, table markdown | ✅ |
| PR-41 | `presentationPairResolver.ts` | pair resolver, merge tabelas | ✅ |
| PR-42 | C3 hex residual + checklist F4 | ver roadmap §5 | ✅ |

## Fase H — redução da raiz (pós-estrutural)

| PR | Destino | Arquivos-alvo |
|----|---------|---------------|
| PR-43 | `presentation/` | export/copy buttons, chart UX, drill-down | ✅ |
| PR-44 | `shared/modal/` | alert/confirm/prompt + hooks `use*Dialog` | ✅ |
| PR-45 | `canvas/` | ChatCanvas, ChatInlineCanvas, chatCanvas utils | ✅ |
| PR-46 | `shared/modal/`, `shell/`, `workspace/` | MemoryUsed, HelpPanel, AttachmentPreview, WebSearch | ✅ |

## Referências

- **Exportação (CSV/XLSX/PDF/PNG):** [`export.md`](./export.md)
- Roadmap: [`frontend-refactor-roadmap.md`](./frontend-refactor-roadmap.md)
- Hub apresentação: [`chat-presentation-hub.md`](./chat-presentation-hub.md)
- Primitivos admin: [`admin/README.md`](../src/ui/components/admin/README.md)
