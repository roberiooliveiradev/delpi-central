import {
  bindingTargetId,
  bindingTargetKind,
  catalogFieldsFromRouteLabels,
  discoverResolvedFieldOptions,
  buildViewFrameFitPatch,
  findDataModel,
  isDataSourceBlockType,
  patchFieldLabels,
  type ChartViewProjection,
  type ComunicadoBlock,
  type ComunicadoDataResolved,
  type ComunicadoDataSourceBlock,
  type ComunicadoTableViewBlock,
  type KpiViewProjection,
  type TableViewProjection,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, useMemo } from "react";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "../components/comunicadoEditorContext";
import { resolveVisibleKeys } from "../components/TableColumnsMultiSelect";
import type { ValueFieldOption } from "../components/ValueFieldsMultiSelect";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

export type ViewProjectionModel = {
  /** Bloco view selecionado (chart_view/kpi_view/table_view) ou null. */
  view: ComunicadoBlock | null;
  viewType: "chart_view" | "kpi_view" | "table_view" | null;
  /** Campos projetáveis (catálogo da rota + resolved do preview). */
  valueFieldOptions: ValueFieldOption[];
  tableColumnOptions: Array<{ key: string; label: string }>;
  applyTableProjection: (next: TableViewProjection | undefined) => void;
  applyKpiProjection: (next: KpiViewProjection | undefined) => void;
  applyChartProjection: (next: ChartViewProjection | undefined) => void;
  /** Renomear label de campo (modelo salvo ou fonte ligada). */
  renameField?: (key: string, label: string) => void;
  /** Labels de campos da fonte/modelo para o multi-select de colunas. */
  sourceFieldLabels?: Record<string, string>;
};

function viewValueFieldOptions(
  route: TvDataRouteCatalogItem | null | undefined,
  source: ComunicadoBlock | null,
  modelResolved?: ComunicadoDataResolved,
  modelFieldLabels?: Record<string, string>,
): ValueFieldOption[] {
  const catalog = catalogFieldsFromRouteLabels(
    route?.valueFields,
    route?.valueFieldLabels,
    route?.projectableFields,
  );
  const resolved =
    modelResolved ??
    (source && "resolved" in source && source.resolved ? source.resolved : undefined);
  const sourceFieldLabels =
    modelFieldLabels ??
    (source && isDataSourceBlockType(source.type)
      ? (source as ComunicadoDataSourceBlock).fieldLabels
      : undefined);
  return discoverResolvedFieldOptions(resolved, catalog, sourceFieldLabels);
}

/**
 * Projeções de campo das views (KPI, gráfico, tabela) — owner compartilhado
 * entre `VisualDataViewInspector` (painel) e o grupo «Campo» da ribbon (§41).
 */
export function useViewProjectionModel(
  view: ComunicadoBlock | null,
  route: TvDataRouteCatalogItem | null,
): ViewProjectionModel {
  const {
    blocks,
    config,
    updateSelected,
    updateBlock,
    reconcileTablePartsForVisibleKeys,
    reconcileChartPartForSeriesFields,
    getDataPreviewResolved,
    saveDataModel,
  } = useComunicadoEditor();

  const isView =
    view?.type === "chart_view" || view?.type === "kpi_view" || view?.type === "table_view";

  const targetId = view ? bindingTargetId(view) : "";
  const targetKind = view ? bindingTargetKind(view) : "none";
  const linkedModel =
    targetKind === "model" ? findDataModel(config, targetId) : null;
  const modelResolved = linkedModel ? getDataPreviewResolved?.(linkedModel.id) : undefined;
  const linkedSource =
    targetKind === "source" && targetId
      ? blocks.find(
          (block) => block.id === targetId && isDataSourceBlockType(block.type),
        ) ?? null
      : null;

  const valueFieldOptions = useMemo(
    () =>
      viewValueFieldOptions(route, linkedSource, modelResolved, linkedModel?.fieldLabels).map(
        (item) => ({
          ...item,
          fieldType: route?.valueFieldTypes?.[item.field],
        }),
      ),
    [route, linkedSource, modelResolved, linkedModel?.fieldLabels],
  );

  const tableColumnOptions = useMemo(
    () => valueFieldOptions.map((item) => ({ key: item.field, label: item.label })),
    [valueFieldOptions],
  );

  const applyTableProjection = useCallback(
    (next: TableViewProjection | undefined) => {
      if (!view || view.type !== "table_view") return;
      const tableBlock = view as ComunicadoTableViewBlock;
      const prevVisible = resolveVisibleKeys(tableColumnOptions, tableBlock.tableProjection);
      const nextVisible = resolveVisibleKeys(tableColumnOptions, next);
      reconcileTablePartsForVisibleKeys(prevVisible, nextVisible);
      const framePatch = buildViewFrameFitPatch({
        ...view,
        tableProjection: next,
      } as ComunicadoBlock);
      updateSelected({
        tableProjection: next,
        ...(framePatch ?? {}),
      } as Partial<ComunicadoTableViewBlock>);
    },
    [reconcileTablePartsForVisibleKeys, tableColumnOptions, updateSelected, view],
  );

  const applyKpiProjection = useCallback(
    (next: KpiViewProjection | undefined) => {
      if (!view) return;
      const framePatch = buildViewFrameFitPatch({
        ...view,
        kpiProjection: next,
      } as ComunicadoBlock);
      updateSelected({
        kpiProjection: next,
        ...(framePatch ?? {}),
      } as Partial<ComunicadoBlock>);
    },
    [updateSelected, view],
  );

  const applyChartProjection = useCallback(
    (next: ChartViewProjection | undefined) => {
      if (!view) return;
      const prevFields =
        (view.type === "chart_view" ? view.chartProjection?.series : null)?.map(
          (item) => item.field,
        ) ?? [];
      const nextFields = (next?.series ?? []).map((item) => item.field);
      reconcileChartPartForSeriesFields(prevFields, nextFields);
      const framePatch = buildViewFrameFitPatch({
        ...view,
        chartProjection: next,
      } as ComunicadoBlock);
      const enableGoal = Boolean(next?.goalField?.trim());
      const chartOptionsPatch =
        enableGoal && view.type === "chart_view"
          ? {
              chartOptions: {
                ...(view.chartOptions ?? {}),
                showGoalLine: true,
              },
            }
          : {};
      updateSelected({
        chartProjection: next,
        ...chartOptionsPatch,
        ...(framePatch ?? {}),
      } as Partial<ComunicadoBlock>);
    },
    [reconcileChartPartForSeriesFields, updateSelected, view],
  );

  const renameField = useMemo(() => {
    if (linkedModel) {
      return (key: string, label: string) => {
        void saveDataModel({
          ...linkedModel,
          fieldLabels: patchFieldLabels(linkedModel.fieldLabels, key, label),
        }).catch(() =>
          tvDashboardNotice(
            "Não foi possível salvar a alteração no modelo de dados.",
          ),
        );
      };
    }
    if (linkedSource && isDataSourceBlockType(linkedSource.type)) {
      return (key: string, label: string) => {
        const source = linkedSource as ComunicadoDataSourceBlock;
        updateBlock(source.id, {
          fieldLabels: patchFieldLabels(source.fieldLabels, key, label),
        } as Partial<ComunicadoBlock>);
      };
    }
    return undefined;
  }, [linkedModel, linkedSource, saveDataModel, updateBlock]);

  return {
    view: isView ? view : null,
    viewType: isView ? (view.type as ViewProjectionModel["viewType"]) : null,
    valueFieldOptions,
    tableColumnOptions,
    applyTableProjection,
    applyKpiProjection,
    applyChartProjection,
    renameField,
    sourceFieldLabels:
      linkedModel?.fieldLabels ??
      (linkedSource && isDataSourceBlockType(linkedSource.type)
        ? (linkedSource as ComunicadoDataSourceBlock).fieldLabels
        : undefined),
  };
}
