import { FormatRibbonTypographySections } from "../formatRibbon/FormatRibbonTypographySections";
import type { SelectionSectionLayout } from "./types";

/**
 * Tipografia global da tabela — mesma UI canônica Fonte/Parágrafo dos demais complexos.
 * Persistência via `resolveSelectedTextFormatTarget` → `complexGlobal` / `part` table.
 */
export function TableTypographySection({ layout }: { layout: SelectionSectionLayout }) {
  return <FormatRibbonTypographySections embed={layout === "pane"} />;
}
