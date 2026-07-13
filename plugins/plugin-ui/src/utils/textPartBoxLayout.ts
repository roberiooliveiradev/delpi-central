import type { CSSProperties } from "react";

export type TextPartVerticalAlign = "top" | "middle" | "bottom";

export function isTextPartVerticalAlign(value: unknown): value is TextPartVerticalAlign {
  return value === "top" || value === "middle" || value === "bottom";
}

/** Mesmo contrato das caixas de texto do deck (`comunicadoVisualBox`). */
export function verticalAlignToJustifyContent(
  verticalAlign: TextPartVerticalAlign | string | null | undefined,
): NonNullable<CSSProperties["justifyContent"]> {
  if (verticalAlign === "middle") return "center";
  if (verticalAlign === "bottom") return "flex-end";
  return "flex-start";
}

export function textAlignToAlignItems(
  textAlign: string | null | undefined,
): NonNullable<CSSProperties["alignItems"]> {
  if (textAlign === "left") return "flex-start";
  if (textAlign === "right") return "flex-end";
  if (textAlign === "center" || textAlign === "justify") return "center";
  return "stretch";
}

export type TextPartColumnBoxLayoutOptions = {
  textAlign?: string | null;
  verticalAlign?: TextPartVerticalAlign | string | null;
  /** Usado quando `verticalAlign` está ausente. */
  defaultVerticalAlign?: TextPartVerticalAlign;
  /**
   * Preenche o host (`width/height: 100%`) — necessário para o eixo vertical
   * ter espaço (partes com frame absoluto).
   */
  fillHost?: boolean;
};

/**
 * Layout flex em coluna para partes tipográficas com caixa/frame.
 * `verticalAlign` → `justifyContent`; `textAlign` → `alignItems` + `textAlign`.
 */
export function resolveTextPartColumnBoxLayout(
  options?: TextPartColumnBoxLayoutOptions,
): CSSProperties {
  const verticalAlign = isTextPartVerticalAlign(options?.verticalAlign)
    ? options.verticalAlign
    : (options?.defaultVerticalAlign ?? "top");
  const fillHost = options?.fillHost !== false;
  const css: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    boxSizing: "border-box",
  };
  if (fillHost) {
    css.width = "100%";
    css.height = "100%";
  } else if (options?.textAlign) {
    css.width = "100%";
  }
  css.justifyContent = verticalAlignToJustifyContent(verticalAlign);
  if (options?.textAlign) {
    css.alignItems = textAlignToAlignItems(options.textAlign);
    css.textAlign = options.textAlign as CSSProperties["textAlign"];
  }
  return css;
}
