import {
  DisplayFormatDialog,
  DisplayFormatRibbonGroup,
  type DisplayFormatPreviewLoader,
  type DisplayFormatSpec,
} from "@delpi/plugin-ui/index";
import {
  mergeChartPartsWithOptions,
  mergeKpiPartsWithOptions,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, useState } from "react";

import { fetchDisplayFormatPreviews } from "../../api/displayFormatPreviewApi";
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import {
  applyDisplayFormatSpecToBlock,
  resolveCurrentDisplayFormatSpec,
  resolveDisplayFormatDescriptor,
  resolveDisplayFormatSample,
} from "../../utils/displayFormatSelection";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

/**
 * Grupo Número — ribbon + inspetor compacto (mesmo componente do kit).
 * O modal Formatar fica fora do `DeckRibbonGroup` para sobreviver ao dismiss
 * do popover quando o grupo está colapsado.
 */
export function NumberFormatSection({ layout }: { layout: SelectionSectionLayout }) {
  const {
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedTableParts,
    selectedCanvasTableCell,
    textEditSelection,
    lastPartialTextEditSelection,
    updateSelected,
  } = useComunicadoEditor();
  const [formatDialogOpen, setFormatDialogOpen] = useState(false);

  const activeTextEdit =
    textEditSelection ??
    (lastPartialTextEditSelection &&
    selected &&
    lastPartialTextEditSelection.blockId === selected.id
      ? lastPartialTextEditSelection
      : null);

  const ctx = {
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedTableParts,
    selectedCanvasTableCell,
    textEditSelection: activeTextEdit,
  };
  const descriptor = resolveDisplayFormatDescriptor(ctx);
  const previewLoader = useCallback<DisplayFormatPreviewLoader>(
    (request) => fetchDisplayFormatPreviews(request),
    [],
  );

  if (!selected || !descriptor) return null;

  const spec = resolveCurrentDisplayFormatSpec(ctx);
  const sample = resolveDisplayFormatSample(ctx);

  const onChange = (next: DisplayFormatSpec) => {
    const patch = applyDisplayFormatSpecToBlock(ctx, next);
    if (!patch) return;
    if (selected.type === "chart_view" && "chartOptions" in patch && patch.chartOptions) {
      updateSelected({
        ...patch,
        chartParts: mergeChartPartsWithOptions(selected.chartParts, patch.chartOptions),
      } as Partial<ComunicadoBlock>);
      return;
    }
    if (selected.type === "kpi_view" && "kpiOptions" in patch && patch.kpiOptions) {
      updateSelected({
        ...patch,
        kpiParts: mergeKpiPartsWithOptions(selected.kpiParts, patch.kpiOptions),
      } as Partial<ComunicadoBlock>);
      return;
    }
    updateSelected(patch);
  };

  const body = (
    <DisplayFormatRibbonGroup
      spec={spec}
      onChange={onChange}
      target={descriptor.target}
      targetHint={descriptor.hint}
      sampleValue={sample.value}
      semanticType={sample.semanticType}
      valueSource={sample.valueSource}
      previewLoader={previewLoader}
      density={layout === "pane" ? "compact" : "ribbon"}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      formatDialog={{ open: formatDialogOpen, onOpenChange: setFormatDialogOpen }}
    />
  );

  const formatDialog = (
    <DisplayFormatDialog
      open={formatDialogOpen}
      onClose={() => setFormatDialogOpen(false)}
      spec={spec}
      onApply={onChange}
      sampleValue={sample.value}
      semanticType={sample.semanticType}
      valueSource={sample.valueSource}
      previewLoader={previewLoader}
      target={descriptor.target}
      targetHint={descriptor.hint}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    />
  );

  if (layout === "pane") {
    return (
      <>
        <SelectionPaneSection title="Número" hint="Formato de exibição (categorias + personalizado).">
          {body}
        </SelectionPaneSection>
        {formatDialog}
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup groupId="number-format" label="Número" hint="Formato de número, data e percentual.">
        {body}
      </DeckRibbonGroup>
      {formatDialog}
    </>
  );
}
