import type { ComunicadoConfig, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import {
  mapComunicadoBlocksToPptxElements,
  type PptxSlideElement,
} from "./exportSlidePptxElements";
import {
  normalizePptxHex,
  resolvePptxFillColor,
  resolvePptxStrokeColor,
  resolvePptxTextColor,
} from "./exportSlidePptxPaint";

export type { PptxSlideElement };
export { mapComunicadoBlocksToPptxElements };

const SLIDE_WIDTH = 13.333;
const SLIDE_HEIGHT = 7.5;

function pptxPosition(frame: ComunicadoFrame) {
  return {
    x: (frame.x / 100) * SLIDE_WIDTH,
    y: (frame.y / 100) * SLIDE_HEIGHT,
    w: (frame.w / 100) * SLIDE_WIDTH,
    h: (frame.h / 100) * SLIDE_HEIGHT,
  };
}

type PptxDeck = Awaited<ReturnType<typeof loadPptxCtor>> extends new () => infer I ? I : never;
type PptxSlide = ReturnType<PptxDeck["addSlide"]>;

async function loadPptxCtor() {
  const mod = await import("pptxgenjs");
  return mod.default;
}

function paintPptxSlide(pptx: PptxDeck, slide: PptxSlide, config: ComunicadoConfig) {
  if (config.background?.type === "color") {
    slide.background = { color: normalizePptxHex(config.background.value, "FFFFFF") };
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
        color: resolvePptxTextColor(style),
        align: style.textAlign === "justify" ? "justify" : style.textAlign,
        valign: style.verticalAlign,
        margin: 0.08,
      });
    } else if (element.kind === "shape") {
      slide.addShape(pptx.ShapeType.rect, {
        ...position,
        fill: { color: resolvePptxFillColor(style) },
        line: {
          color: resolvePptxStrokeColor(style),
          width: style.strokeWidth ?? style.borderWidth ?? 1,
        },
      });
      if (element.text) {
        slide.addText(element.text, {
          ...position,
          align: "center",
          valign: "middle",
          color: resolvePptxTextColor(style),
        });
      }
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
          border: {
            type: "solid",
            color: resolvePptxStrokeColor(style, "94A3B8"),
            pt: 1,
          },
          color: resolvePptxTextColor(style),
          fill: { color: resolvePptxFillColor(style, "FFFFFF") },
          fontFace: style.fontFamily?.split(",")[0]?.trim() || "Arial",
          fontSize: style.fontSize ? Math.max(8, style.fontSize * 0.75) : 14,
          margin: 0.05,
        },
      );
    }
  }
}

export async function exportSlidesPptx(
  configs: ComunicadoConfig[],
  filename = "slide.pptx",
): Promise<void> {
  if (configs.length === 0) {
    throw new Error("Nenhuma tela personalizada para exportar.");
  }
  const PptxGenJS = await loadPptxCtor();
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Minha Delpi";
  pptx.subject = "Telas do TV Dashboard";
  for (const config of configs) {
    paintPptxSlide(pptx, pptx.addSlide(), config);
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

export async function exportSlidePptx(
  config: ComunicadoConfig,
  filename = "slide.pptx",
): Promise<void> {
  await exportSlidesPptx([config], filename);
}
