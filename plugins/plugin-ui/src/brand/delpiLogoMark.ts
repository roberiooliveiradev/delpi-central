import type { HTMLAttributes } from "react";
import { createElement } from "react";

import logoDelpiMarkSvg from "../assets/logoDelpiMark.svg?raw";

/** Wordmark Delpi (sem slogan “Conexões Elétricas”) — markup SVG para impressão/HTML. */
export const DELPI_LOGO_MARK_SVG: string = String(logoDelpiMarkSvg).trim();

export type DelpiLogoMarkProps = HTMLAttributes<HTMLSpanElement> & {
  title?: string;
};

/**
 * Wordmark Delpi reutilizável (SVG inline).
 * Preferir em chrome de impressão/etiqueta via `DELPI_LOGO_MARK_SVG`.
 */
export function DelpiLogoMark({
  title = "DELPI",
  className,
  ...rest
}: DelpiLogoMarkProps) {
  return createElement("span", {
    ...rest,
    className,
    role: "img",
    "aria-label": title,
    dangerouslySetInnerHTML: { __html: DELPI_LOGO_MARK_SVG },
  });
}
