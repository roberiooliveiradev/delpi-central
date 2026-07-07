import {
  EFFICIENCY_BAND_FILTER_OPTIONS,
  type ProductionEfficiencyBand,
} from "../constants/efficiencyBands";
import { DP_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ProductionOrderProductType } from "../types/production";
import { FieldLabel } from "@delpi/plugin-ui";
import { MultiSelectField, type MultiSelectOption } from "./MultiSelectField";

type ProductTypeFilter = ProductionOrderProductType | "";

type OeeAppointmentToolbarProps = {
  productTypeFilter: ProductTypeFilter;
  efficiencyBandFilter: ProductionEfficiencyBand[];
  selectedOps: string[];
  selectedOperators: string[];
  selectedWorkCenters: string[];
  opOptions: MultiSelectOption[];
  operatorOptions: MultiSelectOption[];
  workCenterOptions: MultiSelectOption[];
  onProductTypeFilterChange: (value: ProductTypeFilter) => void;
  onEfficiencyBandFilterChange: (value: ProductionEfficiencyBand[]) => void;
  onSelectedOpsChange: (value: string[]) => void;
  onSelectedOperatorsChange: (value: string[]) => void;
  onSelectedWorkCentersChange: (value: string[]) => void;
  disabled?: boolean;
};

export function OeeAppointmentToolbar({
  productTypeFilter,
  efficiencyBandFilter,
  selectedOps,
  selectedOperators,
  selectedWorkCenters,
  opOptions,
  operatorOptions,
  workCenterOptions,
  onProductTypeFilterChange,
  onEfficiencyBandFilterChange,
  onSelectedOpsChange,
  onSelectedOperatorsChange,
  onSelectedWorkCentersChange,
  disabled = false,
}: OeeAppointmentToolbarProps) {
  return (
    <section
      className="dp-filters-row dp-filters-row--extended"
      aria-label="Filtros de apontamento"
    >
      <MultiSelectField
        label="OP"
        labelHint={DP_HELP_TOOLTIPS.oee.filters.productionOrder}
        emptyLabel="Todas"
        searchable
        options={opOptions}
        selectedValues={selectedOps}
        onChange={onSelectedOpsChange}
        disabled={disabled}
      />

      <MultiSelectField
        label="Operador"
        labelHint={DP_HELP_TOOLTIPS.oee.filters.operator}
        emptyLabel="Todos"
        searchable
        options={operatorOptions}
        selectedValues={selectedOperators}
        onChange={onSelectedOperatorsChange}
        disabled={disabled}
      />

      <MultiSelectField
        label="Centro de trabalho"
        labelHint={DP_HELP_TOOLTIPS.oee.filters.workCenter}
        emptyLabel="Todos"
        searchable
        options={workCenterOptions}
        selectedValues={selectedWorkCenters}
        onChange={onSelectedWorkCentersChange}
        disabled={disabled}
      />

      <MultiSelectField
        label="Faixa de eficiência"
        labelHint={DP_HELP_TOOLTIPS.oee.filters.efficiencyBands}
        options={EFFICIENCY_BAND_FILTER_OPTIONS}
        selectedValues={efficiencyBandFilter}
        onChange={(values) =>
          onEfficiencyBandFilterChange(values as ProductionEfficiencyBand[])
        }
        emptyLabel="Todas as faixas"
        searchable
      />

      <div className="dp-filter-box">
        <FieldLabel
          label="Tipo de produto"
          hint={DP_HELP_TOOLTIPS.oee.filters.productType}
          className="dp-field__label"
        />
        <div className="dp-ppm-toggle" role="group" aria-label="Tipo de produto">
          {[
            { value: "", label: "PA e PI" },
            { value: "PA", label: "PA" },
            { value: "PI", label: "PI" },
          ].map((option) => (
            <button
              key={option.value || "all-types"}
              type="button"
              className={`dp-ppm-toggle__btn${
                productTypeFilter === option.value ? " dp-ppm-toggle__btn--active" : ""
              }`}
              disabled={disabled}
              onClick={() =>
                onProductTypeFilterChange(option.value as ProductTypeFilter)
              }
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
