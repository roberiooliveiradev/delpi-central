import type { SelectionSectionLayout } from "../selectionSections/types";
import { VisualBoxFormaChrome } from "./VisualBoxFormaChrome";

/**
 * @deprecated Preferir `VisualBoxFormaChrome` / seção `shapeChrome`.
 * Mantido como alias — mesmo componente da Forma (texto sem fundo por padrão).
 */
export function FormatRibbonTextBoxChrome({
  bare = false,
  layout = "ribbon",
}: {
  bare?: boolean;
  layout?: SelectionSectionLayout;
} = {}) {
  return <VisualBoxFormaChrome layout={layout} bare={bare} />;
}
