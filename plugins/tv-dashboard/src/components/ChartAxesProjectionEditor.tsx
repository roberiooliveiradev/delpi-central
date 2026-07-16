import { FormSelectControl, NativeCheckboxControl } from "@delpi/plugin-ui/index";
import type { ChartViewProjection } from "@delpi/tv-dashboard-presentation";

import type { ValueFieldOption } from "./ValueFieldsMultiSelect";

type Props = {
  idPrefix: string;
  options: ValueFieldOption[];
  chartProjection?: ChartViewProjection | null;
  onChange: (next: ChartViewProjection | undefined) => void;
  compact?: boolean;
};

/**
 * Eixo X (categoria) + séries Y para chart_view.
 */
export function ChartAxesProjectionEditor({
  idPrefix,
  options,
  chartProjection,
  onChange,
  compact = false,
}: Props) {
  if (options.length === 0) return null;

  const categoryField = chartProjection?.categoryField ?? "";
  const seriesFields = new Set((chartProjection?.series ?? []).map((item) => item.field));
  const hasProjection = Boolean(chartProjection?.categoryField || chartProjection?.series?.length);

  const persist = (next: ChartViewProjection) => {
    if (!next.categoryField && (!next.series || next.series.length === 0)) {
      onChange(undefined);
      return;
    }
    onChange(next);
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
          ? "Categoria no eixo X e uma ou mais séries no eixo Y"
          : "Automático (série da rota). Escolha campos para projetar."}
      </p>
      <FormSelectControl
        id={`${idPrefix}-category`}
        className={compact ? "delpi-ui-select--compact" : undefined}
        ariaLabel="Campo do eixo X (categoria)"
        value={categoryField}
        onChange={(value) => {
          persist({
            categoryField: value || undefined,
            series: chartProjection?.series,
          });
        }}
        options={[
          { value: "", label: "Categoria automática" },
          ...options.map((opt) => ({ value: opt.field, label: `X · ${opt.label}` })),
        ]}
      />
      {options.map((option) => {
        const checked = seriesFields.has(option.field);
        return (
          <NativeCheckboxControl
            key={option.field}
            id={`${idPrefix}-series-${option.field}`}
            className="td-deck-inspector__checkbox"
            checked={checked}
            label={`Y · ${option.label}`}
            onChange={(nextChecked) => {
              const current = chartProjection?.series ?? [];
              const nextSeries = nextChecked
                ? [...current.filter((item) => item.field !== option.field), { field: option.field }]
                : current.filter((item) => item.field !== option.field);
              persist({
                categoryField: chartProjection?.categoryField,
                series: nextSeries.length > 0 ? nextSeries : undefined,
              });
            }}
          />
        );
      })}
    </div>
  );
}
