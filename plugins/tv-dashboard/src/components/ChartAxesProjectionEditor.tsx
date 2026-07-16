import {
  FormSelectControl,
  NativeCheckboxControl,
  NativeTextControl,
} from "@delpi/plugin-ui/index";
import {
  VIEW_AGGREGATION_OPTIONS,
  type ChartSeriesProjection,
  type ChartViewProjection,
  type ViewAggregation,
} from "@delpi/tv-dashboard-presentation";

import { useProjectionDragReorder } from "../hooks/useProjectionDragReorder";
import type { ValueFieldOption } from "./ValueFieldsMultiSelect";

export type ChartAxisFieldOption = ValueFieldOption & {
  fieldType?: "number" | "string" | "date";
};

type Props = {
  idPrefix: string;
  options: ChartAxisFieldOption[];
  chartProjection?: ChartViewProjection | null;
  onChange: (next: ChartViewProjection | undefined) => void;
  compact?: boolean;
  /** Série destacada (selecionada no palco). */
  focusedSeriesField?: string | null;
  /** Clique na linha da série → seleciona a parte no palco (Excel-like). */
  onSeriesActivate?: (field: string, seriesIndex: number) => void;
};

function seriesByField(
  projection: ChartViewProjection | null | undefined,
): Map<string, ChartSeriesProjection> {
  return new Map((projection?.series ?? []).map((item) => [item.field, item]));
}

/**
 * Eixo X (categoria) + séries Y com propriedades individuais.
 * Ao mudar a categoria de referência, ela sai do eixo Y e o gráfico reprojeta os pontos.
 */
export function ChartAxesProjectionEditor({
  idPrefix,
  options,
  chartProjection,
  onChange,
  compact = false,
  focusedSeriesField = null,
  onSeriesActivate,
}: Props) {
  if (options.length === 0) return null;

  const categoryField = chartProjection?.categoryField ?? "";
  const seriesList = chartProjection?.series ?? [];
  const seriesMap = seriesByField(chartProjection);
  const hasProjection = Boolean(categoryField || seriesList.length);

  const persist = (next: ChartViewProjection) => {
    const cleanedSeries = (next.series ?? []).filter(
      (item) => !next.categoryField || item.field !== next.categoryField,
    );
    const payload: ChartViewProjection = {
      categoryField: next.categoryField || undefined,
      series: cleanedSeries.length > 0 ? cleanedSeries : undefined,
    };
    if (!payload.categoryField && !payload.series?.length) {
      onChange(undefined);
      return;
    }
    onChange(payload);
  };

  const yOptions = options.filter((opt) => opt.field !== categoryField);

  const { canDrag, rowClassName, rowDropProps, handleDragProps } = useProjectionDragReorder(
    seriesList,
    (next) => persist({ categoryField: categoryField || undefined, series: next }),
  );

  const patchSeries = (field: string, patch: Partial<ChartSeriesProjection>) => {
    const current = seriesList.map((item) =>
      item.field === field ? { ...item, ...patch } : item,
    );
    persist({ categoryField: categoryField || undefined, series: current });
  };

  return (
    <div
      className={
        compact
          ? "td-deck-inspector__value-fields td-deck-inspector__value-fields--compact"
          : "td-deck-inspector__value-fields"
      }
      role="group"
      aria-label="Eixos do gráfico"
    >
      <p className="td-deck-inspector__hint">
        {hasProjection
          ? "X = categoria de referência; Y = séries (arraste para ordenar)"
          : "Automático (série da rota). Escolha a categoria X e as séries Y."}
      </p>
      <FormSelectControl
        id={`${idPrefix}-category`}
        className={compact ? "delpi-ui-select--compact" : undefined}
        ariaLabel="Campo do eixo X (categoria de referência)"
        value={categoryField}
        onChange={(value) => {
          persist({
            categoryField: value || undefined,
            series: seriesList,
          });
        }}
        options={[
          { value: "", label: "Categoria automática" },
          ...options.map((opt) => ({
            value: opt.field,
            label: `X · ${opt.label}${opt.fieldType ? ` (${opt.fieldType})` : ""}`,
          })),
        ]}
      />

      <p className="td-deck-inspector__hint">Séries no eixo Y</p>
      {yOptions.map((option) => {
        const checked = seriesMap.has(option.field);
        const series = seriesMap.get(option.field);
        const focused = focusedSeriesField === option.field;
        const orderIndex = seriesList.findIndex((item) => item.field === option.field);
        const baseClass = focused
          ? "td-deck-inspector__chart-series td-deck-inspector__chart-series--focused"
          : "td-deck-inspector__chart-series";

        return (
          <div
            key={option.field}
            className={
              checked && orderIndex >= 0 ? rowClassName(baseClass, orderIndex) : baseClass
            }
            {...(checked && orderIndex >= 0 ? rowDropProps(orderIndex) : {})}
            role={checked ? "button" : undefined}
            tabIndex={checked ? 0 : undefined}
            onClick={
              checked && onSeriesActivate
                ? () => onSeriesActivate(option.field, orderIndex)
                : undefined
            }
            onKeyDown={
              checked && onSeriesActivate
                ? (event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSeriesActivate(option.field, orderIndex);
                    }
                  }
                : undefined
            }
          >
            <div
              className="td-deck-inspector__chart-series-head"
              onClick={(event) => event.stopPropagation()}
              onKeyDown={(event) => event.stopPropagation()}
            >
              {checked && canDrag ? (
                <button
                  type="button"
                  className="td-deck-inspector__drag-handle"
                  aria-label={`Arrastar série ${option.label}`}
                  title="Arrastar para reordenar"
                  {...handleDragProps(orderIndex)}
                >
                  ⋮⋮
                </button>
              ) : null}
              <NativeCheckboxControl
                id={`${idPrefix}-series-${option.field}`}
                className="td-deck-inspector__checkbox"
                checked={checked}
                label={`Y · ${option.label}`}
                onChange={(nextChecked) => {
                  const current = seriesList.filter((item) => item.field !== option.field);
                  const nextSeries = nextChecked
                    ? [...current, { field: option.field, label: option.label }]
                    : current;
                  persist({
                    categoryField: categoryField || undefined,
                    series: nextSeries,
                  });
                }}
              />
            </div>
            {checked && series ? (
              <div className="td-deck-inspector__chart-series-controls">
                <FormSelectControl
                  id={`${idPrefix}-${option.field}-agg`}
                  className={compact ? "delpi-ui-select--compact" : undefined}
                  ariaLabel={`Método de cálculo de ${option.label}`}
                  value={series.aggregation ?? "first"}
                  onChange={(value) =>
                    patchSeries(option.field, { aggregation: value as ViewAggregation })
                  }
                  options={VIEW_AGGREGATION_OPTIONS.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                />
                <NativeTextControl
                  id={`${idPrefix}-${option.field}-label`}
                  className={compact ? "delpi-ui-native-control--compact" : undefined}
                  placeholder="Rótulo da série"
                  value={series.label ?? ""}
                  onChange={(value) =>
                    patchSeries(option.field, { label: value.trim() || undefined })
                  }
                />
                <NativeTextControl
                  id={`${idPrefix}-${option.field}-color`}
                  className={compact ? "delpi-ui-native-control--compact" : undefined}
                  placeholder="#089bdb"
                  value={series.color ?? ""}
                  onChange={(value) =>
                    patchSeries(option.field, { color: value.trim() || undefined })
                  }
                  ariaLabel={`Cor da série ${option.label}`}
                />
                <FormSelectControl
                  id={`${idPrefix}-${option.field}-plot`}
                  className={compact ? "delpi-ui-select--compact" : undefined}
                  ariaLabel={`Eixo da série ${option.label}`}
                  value={series.plotOn ?? "primary"}
                  onChange={(value) =>
                    patchSeries(option.field, {
                      plotOn: value === "secondary" ? "secondary" : "primary",
                    })
                  }
                  options={[
                    { value: "primary", label: "Eixo primário" },
                    { value: "secondary", label: "Eixo secundário" },
                  ]}
                />
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
