import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  TEXT_FIELD_AGGREGATION_OPTIONS,
  buildTextDataLinkPatch,
  discoverResolvedFieldOptions,
  isComunicadoVisualBoxBlock,
  type ComunicadoTextProjection,
  type TextProjectionFormat,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DataSourceLinkSection } from "./DataSourceLinkSection";
import { KpiColorRulesEditor } from "./KpiColorRulesEditor";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

const H = TV_DASHBOARD_HELP_TOOLTIPS.data;
const FORMAT_OPTIONS: Array<{ value: TextProjectionFormat; label: string }> = [
  { value: "number", label: "Número" },
  { value: "percent", label: "Percentual" },
  { value: "compact", label: "Compacto" },
  { value: "raw", label: "Texto bruto" },
  { value: "date", label: "Data" },
];

type Props = {
  pane?: boolean;
  layout?: PanelLayout;
  route?: TvDataRouteCatalogItem | null;
  onOpenDataSources?: () => void;
};

export function TextDataBindingInspector({
  pane = false,
  layout = "pane",
  route = null,
  onOpenDataSources,
}: Props) {
  const { selected, blocks, updateSelected, openDataCatalog } = useComunicadoEditor();
  const isRibbon = layout === "ribbon";
  const compactSelect = isRibbon ? "delpi-ui-select--compact" : undefined;
  const compactNative = isRibbon ? "delpi-ui-native-control--compact" : undefined;

  if (!selected || !isComunicadoVisualBoxBlock(selected)) return null;

  const sourceId = selected.dataSourceId?.trim() ?? "";
  const linkedSource = sourceId ? blocks.find((block) => block.id === sourceId) ?? null : null;
  const resolved =
    linkedSource && "resolved" in linkedSource && linkedSource.resolved
      ? linkedSource.resolved
      : "resolved" in selected && selected.resolved
        ? selected.resolved
        : undefined;

  const fieldOptions = discoverResolvedFieldOptions(
    resolved,
    (route?.valueFields ?? []).map((field) => ({
      field: String(field),
      label: route?.valueFieldLabels?.[String(field)] ?? String(field),
    })),
    linkedSource && "fieldLabels" in linkedSource
      ? (linkedSource as { fieldLabels?: Record<string, string> }).fieldLabels
      : undefined,
  );

  const projection = selected.textProjection ?? { field: "" };

  function patchProjection(patch: Partial<ComunicadoTextProjection>) {
    const next: ComunicadoTextProjection = {
      field: projection.field,
      ...projection,
      ...patch,
    };
    updateSelected({ textProjection: next.field.trim() ? next : undefined } as Partial<typeof selected>);
  }

  function linkSource(nextSourceId: string) {
    if (!nextSourceId.trim()) {
      updateSelected({
        dataSourceId: undefined,
        textProjection: undefined,
        resolved: undefined,
      } as Partial<typeof selected>);
      return;
    }
    const source = blocks.find((block) => block.id === nextSourceId);
    const sourceResolved =
      source && "resolved" in source && source.resolved ? source.resolved : resolved;
    const patch = buildTextDataLinkPatch({
      dataSourceId: nextSourceId,
      resolved: sourceResolved,
      existing: selected.textProjection,
    });
    updateSelected(patch as Partial<typeof selected>);
  }

  const openCatalog = onOpenDataSources ?? (() => openDataCatalog("insert"));

  return (
    <>
      <DataSourceLinkSection
        blocks={blocks}
        selectedId={selected.id}
        sourceId={sourceId}
        compactSelect={compactSelect}
        pane={pane}
        onChangeSourceId={linkSource}
        onOpenCatalog={openCatalog}
        catalogLabel="Inserir nova fonte…"
        emptyHint={
          sourceId
            ? undefined
            : "Escolha uma fonte deste slide ou insira uma nova no catálogo."
        }
      />

      {sourceId ? (
        <>
          <DeckPropertySection
            title="Campo dinâmico"
            hint={H.textDataBinding ?? H.viewBinding}
            pane={pane}
          >
            <DeckField label="Campo">
              <FormSelectControl
                className={compactSelect}
                value={projection.field ?? ""}
                onChange={(value) => patchProjection({ field: value })}
                options={[
                  { value: "", label: "Selecione…" },
                  ...fieldOptions.map((item) => ({ value: item.field, label: item.label })),
                ]}
              />
            </DeckField>
            <DeckField label="Agregação">
              <FormSelectControl
                className={compactSelect}
                value={projection.aggregation ?? "first"}
                onChange={(value) =>
                  patchProjection({
                    aggregation: value as ComunicadoTextProjection["aggregation"],
                  })
                }
                options={TEXT_FIELD_AGGREGATION_OPTIONS.map((item) => ({
                  value: item.value,
                  label: item.label,
                }))}
              />
            </DeckField>
            <DeckField label="Formato">
              <FormSelectControl
                className={compactSelect}
                value={projection.format ?? "number"}
                onChange={(value) => patchProjection({ format: value as TextProjectionFormat })}
                options={FORMAT_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
              />
            </DeckField>
            <DeckField label="Prefixo">
              <NativeTextControl
                className={compactNative}
                value={projection.prefix ?? ""}
                onChange={(value) => patchProjection({ prefix: value || undefined })}
              />
            </DeckField>
            <DeckField label="Sufixo">
              <NativeTextControl
                className={compactNative}
                value={projection.suffix ?? ""}
                onChange={(value) => patchProjection({ suffix: value || undefined })}
              />
            </DeckField>
            <DeckField label="Se vazio">
              <NativeTextControl
                className={compactNative}
                value={projection.fallback ?? ""}
                placeholder="—"
                onChange={(value) => patchProjection({ fallback: value || undefined })}
              />
            </DeckField>
          </DeckPropertySection>
          <DeckPropertySection title="Cores por valor" pane={pane} defaultOpen={false}>
            <KpiColorRulesEditor
              idPrefix="td-text-data"
              compact={isRibbon}
              rules={projection.colorRules ?? []}
              onChange={(rules) => patchProjection({ colorRules: rules })}
            />
          </DeckPropertySection>
        </>
      ) : null}
    </>
  );
}

export function canShowTextDataBindingInspector(selected: { type: string } | null | undefined): boolean {
  return Boolean(selected && isComunicadoVisualBoxBlock(selected as never));
}
