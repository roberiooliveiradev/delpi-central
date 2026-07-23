import {
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  type ComunicadoBlock,
  type ComunicadoKpiOptions,
  type ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { KpiColorsStylesMenu } from "../KpiColorsStylesMenu";
import { KpiViewOptionsInspector } from "../KpiViewOptionsInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import type { SelectionSectionLayout } from "./types";

/**
 * Aparência / elementos do KPI.
 * Pane: inspetor completo. Ribbon: presets + tons (paridade com chartStyles).
 */
export function KpiAppearanceSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "kpi_view") return null;

  if (layout === "ribbon") {
    const block = selected as ComunicadoKpiViewBlock;
    const options = mergeComunicadoKpiOptions({
      ...block.kpiOptions,
      ...partsToKpiOptions(block.kpiParts),
    });
    const persistOptions = (nextOptions: ComunicadoKpiOptions) => {
      updateSelected({
        kpiOptions: nextOptions,
        kpiParts: mergeKpiPartsWithOptions(block.kpiParts, nextOptions),
      } as Partial<ComunicadoBlock>);
    };
    return (
      <div className="td-deck-ribbon__kpi-appearance">
        <KpiColorsStylesMenu
          options={options}
          onApplyOptions={(next) => persistOptions(mergeComunicadoKpiOptions(next))}
        />
      </div>
    );
  }

  return <KpiViewOptionsInspector pane />;
}
