import {
  canvasTableCellsToStringMatrix,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

const SLIDE_WIDTH = 13.333;
const SLIDE_HEIGHT = 7.5;

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

function pptxPosition(frame: ComunicadoFrame) {
  return {
    x: (frame.x / 100) * SLIDE_WIDTH,
    y: (frame.y / 100) * SLIDE_HEIGHT,
    w: (frame.w / 100) * SLIDE_WIDTH,
    h: (frame.h / 100) * SLIDE_HEIGHT,
  };
}

function color(value: string | undefined, fallback: string): string {
  const normalized = value?.trim().replace(/^#/, "");
  return normalized && /^[0-9a-f]{6}$/i.test(normalized) ? normalized : fallback;
}

export async function exportSlidePptx(
  config: ComunicadoConfig,
  filename = "slide.pptx",
): Promise<void> {
  const { default: PptxGenJS } = await import("pptxgenjs");
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Minha Delpi";
  pptx.subject = "Tela do TV Dashboard";
  const slide = pptx.addSlide();

  if (config.background?.type === "color") {
    slide.background = { color: color(config.background.value, "FFFFFF") };
  } else if (config.background?.type === "image" && config.background.url) {
    try {
      slide.addImage({ path: config.background.url, x: 0, y: 0, w: SLIDE_WIDTH, h: SLIDE_HEIGHT });
    } catch {
      // A exportação continua sem o fundo quando a URL não é aceita pelo PptxGenJS.
    }
  }

  for (const element of mapComunicadoBlocksToPptxElements(config.blocks)) {
    const position = pptxPosition(element.frame);
    const style = element.block.style ?? {};
    if (element.kind === "text" || element.kind === "placeholder") {
      slide.addText(element.text, {
        ...position,
        fontFace: style.fontFamily?.split(",")[0]?.trim() || "Arial",
        fontSize: style.fontSize ? Math.max(8, style.fontSize * 0.75) : 18,
        bold: style.fontWeight === "bold",
        italic: style.fontStyle === "italic",
        color: color(style.color, "1F2937"),
        align: style.textAlign === "justify" ? "justify" : style.textAlign,
        valign: style.verticalAlign,
        margin: 0.08,
      });
    } else if (element.kind === "shape") {
      slide.addShape(pptx.ShapeType.rect, {
        ...position,
        fill: { color: color(style.fill ?? style.backgroundColor, "DCE6F1") },
        line: {
          color: color(style.stroke ?? style.borderColor, "64748B"),
          width: style.strokeWidth ?? style.borderWidth ?? 1,
        },
      });
      if (element.text) slide.addText(element.text, { ...position, align: "center", valign: "middle" });
    } else if (element.kind === "image") {
      try {
        slide.addImage({ path: element.url, ...position });
      } catch {
        slide.addText("[Imagem]", { ...position, align: "center", valign: "middle" });
      }
    } else if (element.kind === "table") {
      slide.addTable(
        element.rows.map((row, rowIndex) =>
          row.map((text) => ({
            text,
            options: element.headerRow && rowIndex === 0 ? { bold: true } : undefined,
          })),
        ),
        {
        ...position,
        border: { type: "solid", color: color(style.borderColor, "94A3B8"), pt: 1 },
        color: color(style.color, "1F2937"),
        fill: { color: color(style.backgroundColor, "FFFFFF") },
        fontFace: style.fontFamily?.split(",")[0]?.trim() || "Arial",
        fontSize: style.fontSize ? Math.max(8, style.fontSize * 0.75) : 14,
        margin: 0.05,
        },
      );
    }
  }

  const output = await pptx.write({ outputType: "blob", compression: true });
  const blob = output instanceof Blob ? output : new Blob([output as BlobPart]);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename.endsWith(".pptx") ? filename : `${filename}.pptx`;
  anchor.click();
  URL.revokeObjectURL(url);
}
