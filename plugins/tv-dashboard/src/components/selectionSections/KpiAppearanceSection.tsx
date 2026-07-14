import { KpiViewOptionsInspector } from "../KpiViewOptionsInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import type { SelectionSectionLayout } from "./types";

/**
 * Aparência / elementos do KPI — fonte: KpiViewOptionsInspector (pane).
 * Ribbon: omitido (chrome preenchimento/contorno fica em shapeChrome / ShapeRibbon).
 */
export function KpiAppearanceSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected } = useComunicadoEditor();
  if (layout === "ribbon") return null;
  if (!selected || selected.type !== "kpi_view") return null;
  return <KpiViewOptionsInspector pane />;
}
