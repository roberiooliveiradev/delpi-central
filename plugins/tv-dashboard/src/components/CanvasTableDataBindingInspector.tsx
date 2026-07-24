import { FormSelectControl } from "@delpi/plugin-ui/index";
import {
  TEXT_FIELD_AGGREGATION_OPTIONS,
  applyCanvasTableDataRef,
  buildCanvasTableDataLinkPatch,
  discoverResolvedFieldOptions,
  formatCanvasTableDataBindingLabel,
  listCanvasTableDataBindings,
  normalizeCanvasTableCell,
  suggestCanvasTableCellDataRef,
  type ApplyCanvasTableDataRefScope,
  type ComunicadoTextDataRef,
  type TextProjectionFormat,
} from "@delpi/tv-dashboard-presentation";
import { useMemo } from "react";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DataSourceLinkSection } from "./DataSourceLinkSection";
import { DynamicContentInsertControl } from "./DynamicContentInsertControl";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

const H = TV_DASHBOARD_HELP_TOOLTIPS.data;
const FORMAT_OPTIONS: Array<{ value: TextProjectionFormat; label: string }> = [
  { value: "number", label: "Número" },
  { value: "percent", label: "Percentual" },
  { value: "currency", label: "Moeda" },
  { value: "compact", label: "Compacto" },
  { value: "raw", label: "Texto bruto" },
  { value: "date", label: "Data" },
];

const AGG_LABEL = Object.fromEntries(
  TEXT_FIELD_AGGREGATION_OPTIONS.map((item) => [item.value, item.label]),
) as Record<string, string>;

type Props = {
  pane?: boolean;
  layout?: PanelLayout;
  route?: TvDataRouteCatalogItem | null;
  onOpenDataSources?: () => void;
};

/** Vincular fonte à Grade e campo a uma célula / coluna / corpo. */
export function CanvasTableDataBindingInspector({
  pane = false,
  layout = "pane",
  route = null,
  onOpenDataSources,
}: Props) {
  const {
    selected,
    blocks,
    updateSelected,
    updateBlock,
    openDataCatalog,
    selectedCanvasTableCell,
    selectCanvasTableCell,
  } = useComunicadoEditor();
  const isRibbon = layout === "ribbon";
  const compactSelect = isRibbon ? "delpi-ui-select--compact" : undefined;

  const table = selected?.type === "canvas_table" ? selected : null;
  const cellSel =
    table && selectedCanvasTableCell?.blockId === table.id ? selectedCanvasTableCell : null;
  const selectedCell =
    table && cellSel
      ? normalizeCanvasTableCell(table.cells[cellSel.row]?.[cellSel.col])
      : null;

  const catalogFields = useMemo(
    () =>
      (route?.valueFields ?? []).map((field) => ({
        field: String(field),
        label: route?.valueFieldLabels?.[String(field)] ?? String(field),
      })),
    [route?.valueFieldLabels, route?.valueFields],
  );

  const sourceId = table?.dataSourceId?.trim() ?? "";
  const linkedSource = sourceId ? blocks.find((block) => block.id === sourceId) ?? null : null;
  const resolved =
    linkedSource && "resolved" in linkedSource && linkedSource.resolved
      ? linkedSource.resolved
      : table?.resolved;

  const fieldOptions = useMemo(
    () =>
      discoverResolvedFieldOptions(
        resolved,
        catalogFields,
        linkedSource && "fieldLabels" in linkedSource
          ? (linkedSource as { fieldLabels?: Record<string, string> }).fieldLabels
          : undefined,
      ),
    [catalogFields, linkedSource, resolved],
  );

  const bindings = useMemo(
    () => (table ? listCanvasTableDataBindings(table) : []),
    [table],
  );

  if (!table) return null;

  function linkSource(nextSourceId: string) {
    if (!nextSourceId.trim()) {
      updateSelected({
        dataSourceId: undefined,
        resolved: undefined,
      });
      return;
    }
    const source = blocks.find((block) => block.id === nextSourceId);
    const sourceResolved =
      source && "resolved" in source && source.resolved ? source.resolved : resolved;
    const patch = buildCanvasTableDataLinkPatch({
      dataSourceId: nextSourceId,
      resolved: sourceResolved,
      catalogFields,
      targetCell: cellSel,
      existingCells: table.cells,
    });
    updateSelected(patch);
  }

  function patchCellDataRef(
    nextRef: ComunicadoTextDataRef | null,
    scope: ApplyCanvasTableDataRefScope = "cell",
  ) {
    if (!cellSel) return;
    const next = applyCanvasTableDataRef(table, cellSel, nextRef, scope);
    updateBlock(table.id, { cells: next.cells, dataSourceId: table.dataSourceId });
  }

  function ensureFieldOnCell(field: string) {
    if (!cellSel || !selectedCell) return;
    const preferSeries = selectedCell.kind === "sparkline";
    const suggested =
      suggestCanvasTableCellDataRef(resolved, catalogFields, preferSeries) ?? {
        field,
        aggregation: preferSeries ? ("list" as const) : ("first" as const),
        format: "number" as const,
      };
    patchCellDataRef({
      ...suggested,
      field,
      format: selectedCell.dataRef?.format ?? suggested.format,
      aggregation: selectedCell.dataRef?.aggregation ?? suggested.aggregation,
    });
  }

  const openCatalog = onOpenDataSources ?? (() => openDataCatalog("insert"));
  const dataRef = selectedCell?.dataRef;
  const bindingCountLabel =
    bindings.length === 0
      ? "Nenhum campo vinculado"
      : bindings.length === 1
        ? "1 campo vinculado"
        : `${bindings.length} campos vinculados`;

  return (
    <>
      <DataSourceLinkSection
        blocks={blocks}
        selectedId={table.id}
        sourceId={sourceId}
        compactSelect={compactSelect}
        pane={pane}
        onChangeSourceId={linkSource}
        onOpenCatalog={openCatalog}
        catalogLabel="Inserir nova fonte…"
        emptyHint={
          sourceId
            ? undefined
            : "Escolha uma fonte deste slide para alimentar células da Grade."
        }
      />

      {sourceId ? (
        <DeckPropertySection
          title="Campo na célula"
          hint={H.canvasTableDataBinding ?? H.textDataBinding ?? H.viewBinding}
          pane={pane}
        >
          <p className="td-subtitle td-canvas-table-bindings__count">{bindingCountLabel}</p>

          {bindings.length > 0 ? (
            <ul className="td-canvas-table-bindings" aria-label="Campos vinculados na Grade">
              {bindings.map((entry) => {
                const active =
                  cellSel?.row === entry.row && cellSel?.col === entry.col;
                const fieldLabel =
                  fieldOptions.find((item) => item.field === entry.field)?.label ??
                  entry.field;
                return (
                  <li key={`${entry.row}:${entry.col}:${entry.field}`}>
                    <button
                      type="button"
                      className={[
                        "td-canvas-table-bindings__item",
                        active ? "td-canvas-table-bindings__item--active" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() =>
                        selectCanvasTableCell(table.id, { row: entry.row, col: entry.col })
                      }
                    >
                      {formatCanvasTableDataBindingLabel(
                        {
                          ...entry,
                          field: fieldLabel,
                        },
                        AGG_LABEL[entry.aggregation] ?? entry.aggregation,
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : null}

          {!cellSel ? (
            <p className="td-subtitle">
              Selecione uma célula na Grade para vincular um campo próprio (cada célula pode ter
              um dado diferente).
            </p>
          ) : (
            <>
              <p className="td-subtitle">
                Célula {cellSel.row + 1}×{cellSel.col + 1}
                {selectedCell?.kind === "sparkline" ? " (sparkline)" : ""}
              </p>
              <div className="td-dynamic-content-insert--inspector">
                <DynamicContentInsertControl variant="inspector" />
              </div>
              <DeckField label="Campo">
                <FormSelectControl
                  className={compactSelect}
                  value={dataRef?.field ?? ""}
                  onChange={(value) => {
                    if (!value.trim()) {
                      patchCellDataRef(null);
                      return;
                    }
                    ensureFieldOnCell(value);
                  }}
                  options={[
                    { value: "", label: "Sem dados (estático)" },
                    ...fieldOptions.map((item) => ({
                      value: item.field,
                      label: item.label,
                    })),
                  ]}
                />
              </DeckField>
              {dataRef?.field ? (
                <>
                  <DeckField label="Agregação">
                    <FormSelectControl
                      className={compactSelect}
                      value={dataRef.aggregation ?? "first"}
                      onChange={(value) =>
                        patchCellDataRef({
                          ...dataRef,
                          aggregation: value as ComunicadoTextDataRef["aggregation"],
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
                      value={dataRef.format ?? "number"}
                      onChange={(value) =>
                        patchCellDataRef({
                          ...dataRef,
                          format: value as TextProjectionFormat,
                        })
                      }
                      options={FORMAT_OPTIONS.map((item) => ({
                        value: item.value,
                        label: item.label,
                      }))}
                    />
                  </DeckField>
                  <div className="td-deck-ribbon__toolbar-row">
                    <button
                      type="button"
                      className="td-btn td-btn--sm"
                      onClick={() => patchCellDataRef(dataRef, "column")}
                    >
                      Aplicar à coluna
                    </button>
                    <button
                      type="button"
                      className="td-btn td-btn--sm td-btn--ghost"
                      onClick={() => patchCellDataRef(dataRef, "body")}
                    >
                      Aplicar ao corpo
                    </button>
                    <button
                      type="button"
                      className="td-btn td-btn--sm td-btn--ghost"
                      onClick={() => patchCellDataRef(null)}
                    >
                      Remover vínculo
                    </button>
                  </div>
                </>
              ) : null}
            </>
          )}
        </DeckPropertySection>
      ) : null}
    </>
  );
}

export function canShowCanvasTableDataBindingInspector(
  selected: { type: string } | null | undefined,
): boolean {
  return selected?.type === "canvas_table";
}
