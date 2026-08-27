import {
  FormSelectControl,
  NativeCheckboxControl,
  NativeTextControl,
} from "@delpi/plugin-ui/index";
import {
  chartAxesEditorHint,
  chartCategoryWellLabel,
  chartGoalWellLabel,
  chartPolicyHasGoalWell,
  chartSeriesWellLabel,
  resolveChartDataPolicy,
  resolveChartSeriesDefaultAggregation,
  VIEW_AGGREGATION_OPTIONS,
  type ChartSeriesProjection,
  type ChartViewProjection,
  type ComunicadoChartType,
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
  chartType?: ComunicadoChartType;
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
 * Eixo X (categoria) + séries Y + meta (coluna) com propriedades individuais.
 * Ao mudar a categoria de referência, ela sai do eixo Y e o gráfico reprojeta os pontos.
 */
export function ChartAxesProjectionEditor({
  idPrefix,
  options,
  chartProjection,
  onChange,
  compact = false,
  chartType = "line",
  focusedSeriesField = null,
  onSeriesActivate,
}: Props) {
  if (options.length === 0) return null;

  const policy = resolveChartDataPolicy(chartType);
  const isGauge = chartType === "gauge";
  const showGoalWell = chartPolicyHasGoalWell(chartType);
  const categoryField = chartProjection?.categoryField ?? "";
  const seriesList = chartProjection?.series ?? [];
  const goalField = chartProjection?.goalField ?? "";
  const goalAggregation = chartProjection?.goalAggregation ?? "first";
  const seriesMap = seriesByField(chartProjection);
  const hasProjection = Boolean(categoryField || seriesList.length || goalField);
  const seriesWell = chartSeriesWellLabel(policy);
  const goalWell = chartGoalWellLabel(policy);
  const maxSeries = Math.max(1, policy.maxSeries);
  const atSeriesLimit = seriesList.length >= maxSeries;
  const measureOptions = options.filter(
    (opt) => opt.fieldType !== "string" && opt.fieldType !== "date",
  );

  const persist = (next: ChartViewProjection) => {
    const cleanedSeries = (next.series ?? []).filter(
      (item) => !next.categoryField || item.field !== next.categoryField,
    );
    const cappedSeries =
      cleanedSeries.length > maxSeries ? cleanedSeries.slice(0, maxSeries) : cleanedSeries;
    const nextGoal = (next.goalField ?? "").trim();
    const payload: ChartViewProjection = {
      categoryField: next.categoryField || undefined,
      series: cappedSeries.length > 0 ? cappedSeries : undefined,
      ...(nextGoal
        ? {
            goalField: nextGoal,
            goalAggregation: next.goalAggregation ?? "first",
          }
        : {}),
    };
    if (!payload.categoryField && !payload.series?.length && !payload.goalField) {
      onChange(undefined);
      return;
    }
    onChange(payload);
  };

  const yOptions = options.filter((opt) => opt.field !== categoryField);

  const { canDrag, rowClassName, rowDropProps, handleDragProps } = useProjectionDragReorder(
    seriesList,
    (next) =>
      persist({
        categoryField: categoryField || undefined,
        series: next,
        goalField: goalField || undefined,
        goalAggregation,
      }),
  );

  const patchSeries = (field: string, patch: Partial<ChartSeriesProjection>) => {
    const current = seriesList.map((item) =>
      item.field === field ? { ...item, ...patch } : item,
    );
    persist({
      categoryField: categoryField || undefined,
      series: current,
      goalField: goalField || undefined,
      goalAggregation,
    });
  };

  return (
    <div
      className={
        compact
          ? "td-deck-inspector__value-fields td-deck-inspector__value-fields--compact"
          : "td-deck-inspector__value-fields"
      }
      role="group"
      aria-label={isGauge ? "Valor e meta do velocímetro" : "Eixos do gráfico"}
    >
      <p className="td-deck-inspector__hint">
        {chartAxesEditorHint(policy, hasProjection)}
        {!isGauge && maxSeries === 1
          ? " Este tipo de gráfico usa uma série de valor."
          : !isGauge
            ? ` Até ${maxSeries} séries.`
            : ""}
      </p>
      {!isGauge ? (
        <FormSelectControl
          id={`${idPrefix}-category`}
          className={compact ? "delpi-ui-select--compact" : undefined}
          ariaLabel={`${chartCategoryWellLabel(policy)}`}
          value={categoryField}
          onChange={(value) => {
            persist({
              categoryField: value || undefined,
              series: seriesList,
              goalField: goalField || undefined,
              goalAggregation,
            });
          }}
          options={[
            { value: "", label: `${chartCategoryWellLabel(policy)} automática` },
            ...options.map((opt) => ({
              value: opt.field,
              label: `${chartCategoryWellLabel(policy)} · ${opt.label}${opt.fieldType ? ` (${opt.fieldType})` : ""}`,
            })),
          ]}
        />
      ) : null}

      <p className="td-deck-inspector__hint">{seriesWell}</p>
      <div className="td-deck-inspector__projection-list" role="list" aria-label={seriesWell}>
        {yOptions.map((option) => {
          const checked = seriesMap.has(option.field);
          const series = seriesMap.get(option.field);
          const focused = focusedSeriesField === option.field;
          const orderIndex = seriesList.findIndex((item) => item.field === option.field);
          const rowLabel = `${seriesWell} · ${option.label}`;
          const baseClass = focused
            ? "td-deck-inspector__chart-series td-deck-inspector__chart-series--focused"
            : "td-deck-inspector__chart-series";
          const canActivate = Boolean(checked && onSeriesActivate && orderIndex >= 0);

          return (
            <div
              key={option.field}
              role="listitem"
              className={
                checked && orderIndex >= 0 ? rowClassName(baseClass, orderIndex) : baseClass
              }
              {...(checked && orderIndex >= 0 ? rowDropProps(orderIndex) : {})}
            >
              <div
                className="td-deck-inspector__chart-series-head"
                onClick={(event) => event.stopPropagation()}
                onKeyDown={(event) => event.stopPropagation()}
              >
                {checked && canDrag && !isGauge ? (
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
                <span
                  className="td-deck-inspector__column-toggle"
                  onClick={(event) => event.stopPropagation()}
                  onPointerDown={(event) => event.stopPropagation()}
                >
                  <NativeCheckboxControl
                    id={`${idPrefix}-series-${option.field}`}
                    className="td-deck-inspector__checkbox"
                    checked={checked}
                    disabled={!checked && atSeriesLimit && maxSeries > 1}
                    aria-label={`Incluir ${rowLabel}`}
                    onChange={(nextChecked) => {
                      if (nextChecked) {
                        const without = seriesList.filter((item) => item.field !== option.field);
                        const entry = {
                          field: option.field,
                          label: option.label,
                          aggregation: resolveChartSeriesDefaultAggregation(
                            policy,
                            option.fieldType,
                          ),
                        };
                        const nextSeries =
                          maxSeries === 1
                            ? [entry]
                            : without.length >= maxSeries
                              ? [...without.slice(0, maxSeries - 1), entry]
                              : [...without, entry];
                        persist({
                          categoryField: categoryField || undefined,
                          series: nextSeries,
                          goalField: goalField || undefined,
                          goalAggregation,
                        });
                        return;
                      }
                      persist({
                        categoryField: categoryField || undefined,
                        series: seriesList.filter((item) => item.field !== option.field),
                        goalField: goalField || undefined,
                        goalAggregation,
                      });
                    }}
                  />
                </span>
                {canActivate ? (
                  <button
                    type="button"
                    className="td-chart-element__label-btn"
                    title="Selecionar série no palco"
                    onClick={() => onSeriesActivate?.(option.field, orderIndex)}
                  >
                    {rowLabel}
                  </button>
                ) : (
                  <span className="td-chart-element__label">{rowLabel}</span>
                )}
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
                  {!isGauge ? (
                    <>
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
                    </>
                  ) : null}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>

      {showGoalWell ? (
        <>
          <p className="td-deck-inspector__hint">{goalWell}</p>
          <FormSelectControl
            id={`${idPrefix}-goal-field`}
            className={compact ? "delpi-ui-select--compact" : undefined}
            ariaLabel={goalWell}
            value={goalField}
            onChange={(value) => {
              persist({
                categoryField: categoryField || undefined,
                series: seriesList,
                goalField: value || undefined,
                goalAggregation: value ? goalAggregation : undefined,
              });
            }}
            options={[
              { value: "", label: `${goalWell} — nenhuma (só número fixo)` },
              ...measureOptions.map((opt) => ({
                value: opt.field,
                label: `${goalWell} · ${opt.label}`,
              })),
            ]}
          />
          {goalField ? (
            <FormSelectControl
              id={`${idPrefix}-goal-agg`}
              className={compact ? "delpi-ui-select--compact" : undefined}
              ariaLabel={`Agregação da ${goalWell.toLowerCase()}`}
              value={goalAggregation}
              onChange={(value) =>
                persist({
                  categoryField: categoryField || undefined,
                  series: seriesList,
                  goalField,
                  goalAggregation: value as ViewAggregation,
                })
              }
              options={VIEW_AGGREGATION_OPTIONS.map((item) => ({
                value: item.value,
                label: item.label,
              }))}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
