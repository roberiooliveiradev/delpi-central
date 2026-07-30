import {
  canvasTableCellsToStringMatrix,
  type ComunicadoBlock,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

export type PptxSlideElement =
  | { kind: "text"; text: string; frame: ComunicadoFrame; block: ComunicadoBlock }
  | { kind: "shape"; text?: string; frame: ComunicadoFrame; block: ComunicadoBlock }
  | { kind: "image"; url: string; frame: ComunicadoFrame; block: ComunicadoBlock }
  | {
      kind: "table";
      rows: string[][];
      headerRow: boolean;
      frame: ComunicadoFrame;
      block: ComunicadoBlock;
    }
  | { kind: "placeholder"; text: string; frame: ComunicadoFrame; block: ComunicadoBlock };

export function mapComunicadoBlocksToPptxElements(
  blocks: ComunicadoBlock[] = [],
): PptxSlideElement[] {
  return blocks.flatMap((block): PptxSlideElement[] => {
    if (block.type === "heading" || block.type === "text") {
      return [{ kind: "text", text: block.content, frame: block.frame, block }];
    }
    if (block.type === "shape") {
      return [{ kind: "shape", text: block.content, frame: block.frame, block }];
    }
    if (block.type === "image" && block.url) {
      return [{ kind: "image", url: block.url, frame: block.frame, block }];
    }
    if (block.type === "video") {
      return [{ kind: "placeholder", text: "[Vídeo]", frame: block.frame, block }];
    }
    if (block.type === "canvas_table") {
      return [{
        kind: "table",
        /* Sparkline: fallback do valor âncora / texto (sem SVG no PPTX). */
        rows: canvasTableCellsToStringMatrix(block.cells),
        headerRow: block.headerRow ?? false,
        frame: block.frame,
        block,
      }];
    }
    if (
      block.type === "chart_view" ||
      block.type === "table_view" ||
      block.type === "kpi_view" ||
      block.type.startsWith("data_")
    ) {
      const label =
        block.type === "chart_view"
          ? "Gráfico"
          : block.type === "table_view"
            ? "Tabela de dados"
            : block.type === "kpi_view"
              ? "KPI"
              : "Bloco de dados";
      return [{ kind: "placeholder", text: `[${label}]`, frame: block.frame, block }];
    }
    return [];
  });
}
