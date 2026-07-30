# Editor BPMN (`FlowchartEditor`) — guia de consumo

Família canônica: `plugins/plugin-ui/src/components/bpmn/` (subpastas `model`, `editor`, `nodes`, `mermaid`, `layout`, `export`, `hooks`, `shell`).

CSS: `plugins/plugin-ui/src/styles/bpmn/` (classes `.delpi-ui-bpmn-*`, tokens `--delpi-ui-bpmn-*`). Shell do canvas: `.delpi-ui-flowchart-shell`. Aliases `tm-diagram-*` / `--tm-diagram-*` existem só para compat temporária.

**Domínio (persistência, validação, BPMN XML, merge as-is/to-be) fica no MFE/API do plugin** — o kit é headless (`value` / `onChange`).

## Checklist Module Federation

1. `vite.config.ts`: `remotes: pluginUiRemote()`, `shared: { ...FEDERATION_SHARED_WITH_DIAGRAM }` (alias `FEDERATION_SHARED_WITH_BPMN` = mesmo objeto).
2. `bootstrap.tsx`: `await preparePluginUiRemote()` antes do render.
3. Import: `import { FlowchartEditor, emptyFlowchart, type FlowchartV1 } from "@delpi/plugin-ui/index"`.
4. Estilos do remote: cobertos por `preparePluginUiRemote()` → `@delpi/plugin-ui/styles`.
5. Docker: `<<: *plugin-ui-federated`, **sem** `COPY plugin-ui`.
6. Tokens no root do dashboard (`.dashboard-{plugin}`): mapear `--delpi-ui-*` / vars do portal; o editor usa `--delpi-ui-bpmn-*` definidos no kit sob `.delpi-ui-flowchart-shell`.

Peers pesados (`@xyflow/react`, `mermaid`, `html-to-image`) ficam no remote; o MFE declara tipagem/peer conforme o `package.json` do kit.

## Wrapper mínimo

Labels PT-BR **obrigatórios** via props (sem default no kit). Copie o padrão do Transformômetro:

```tsx
import { forwardRef, type ComponentProps } from "react";
import {
  FlowchartEditor as BaseFlowchartEditor,
  type FlowchartEditorHandle,
  type FlowchartEditorLabels,
} from "@delpi/plugin-ui/index";

type Props = Omit<
  ComponentProps<typeof BaseFlowchartEditor>,
  "labels" | "confirm" | "colorMode" | "shellClassName"
> & { labels?: FlowchartEditorLabels };

export const FlowchartEditor = forwardRef<FlowchartEditorHandle, Props>(
  function FlowchartEditor({ labels = MY_PLUGIN_LABELS, ...props }, ref) {
    const confirm = useConfirm(); // do plugin
    const isDark = useMyDarkMode();
    return (
      <BaseFlowchartEditor
        ref={ref}
        {...props}
        labels={labels}
        confirm={confirm}
        colorMode={isDark ? "dark" : "light"}
        shellClassName="dashboard-meu-plugin"
      />
    );
  }
);
```

Referência de labels: `plugins/transformometro/src/content/flowchartEditorLabels.ts` (tipo `FlowchartEditorLabels`).

## Chrome 2-tier (página dedicada)

Em modo editável (`!readOnly` + `showTemplates`), o editor monta [`EditorChrome`](../src/components/layout/EditorChrome.tsx) + ribbon com [`EditorRibbonSection`](../src/components/ribbon/EditorRibbonSection.tsx) / [`RibbonTile`](../src/components/ribbon/RibbonTile.tsx):

- **Head:** Voltar (`chromeLeading.onBack`) · undo/redo · Elementos/Modelos · Como usar · Desenho/Mermaid · título
- **Ribbon:** seções por categoria BPMN; colapso responsivo (direita→esquerda) abre popover via `RibbonGroup`
- **Props:** `chromeLeading?: { onBack?; backLabel?; title? }` — o Transformômetro passa isso em `/diagrama/edit`

CSS: `styles/editor-chrome.css`, `styles/ribbon-tile.css`, `styles/ribbon-overflow.css`.

## Estado e persistência

- Modelo canônico: `FlowchartV1` (`emptyFlowchart()`, templates `applyLinearTemplate` / `applyDecisionTemplate` / `applySwimlaneBpmnTemplate`).
- Conversão: `flowchartToMermaid` / `mermaidToFlowchart`.
- Export PNG: ref `FlowchartEditorHandle.exportPng` ou `exportReactFlowDiagramPng`.
- Salvar/carregar: use case + API do **seu** plugin — não há endpoint genérico no kit.

## Estrutura interna (orientação)

| Pasta | Responsabilidade |
|-------|------------------|
| `model/` | `FlowchartV1`, catálogo BPMN, labels type |
| `editor/` | `FlowchartEditor` + toolbar/status/dock |
| `nodes/` | Nós BPMN, lanes, edges |
| `mermaid/` | Preview + round-trip Mermaid |
| `layout/` | Swimlanes, routing, fit view |
| `export/` | PNG |
| `hooks/` | Histórico, dark mode |
| `shell/` | Fullscreen frame, layout context, classes shell |

Barrel público: `src/components/bpmn/index.ts` → reexportado em `src/index.ts`. Shim legado: `components/diagram` → `bpmn`.

## Catálogo e testes

- Demo: `src/catalog/demos/bpmn.tsx`
- Testes: `src/components/bpmn/**/*.test.*`
- Doc API props: [component-catalog.md](./component-catalog.md) § família `bpmn`
