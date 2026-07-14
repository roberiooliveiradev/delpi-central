import { ShapeChromeSection } from "./ShapeChromeSection";
import type { SelectionSectionLayout } from "./types";

/**
 * @deprecated Preferir seção `shapeChrome` — mesmo chrome unificado (texto/shape).
 * Alias para não quebrar hosts que ainda resolvem `textBox`.
 */
export function TextBoxSection({ layout }: { layout: SelectionSectionLayout }) {
  return <ShapeChromeSection layout={layout} />;
}
