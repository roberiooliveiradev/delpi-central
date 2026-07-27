import type { EficienciaFabrilShift } from "../constants/shifts";
import type { EficienciaFabrilEfficiencyBand } from "../constants/efficiencyBands";
import type { MultiSelectOption } from "./MultiSelectField";
import { FieldLabel, NativeTextControl, createFilterBarShell } from "@delpi/plugin-ui/index";
import { MultiSelectField } from "./MultiSelectField";
import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";

const FilterBarShell = createFilterBarShell({
  prefix: "ef",
  withGrid: true,
  defaultAriaLabel: "Filtros do dashboard",
});

type FilterBarProps = {
  dateStart: string;
  dateEnd: string;
  ops: string[];
  finishedProducts: string[];
  operations: string[];
  employees: string[];
  workCenters: string[];
  shifts: EficienciaFabrilShift[];
  efficiencyBands: EficienciaFabrilEfficiencyBand[];
  opOptions: MultiSelectOption[];
  finishedProductOptions: MultiSelectOption[];
  operationOptions: MultiSelectOption[];
  employeeOptions: MultiSelectOption[];
  workCenterOptions: MultiSelectOption[];
  shiftOptions: MultiSelectOption[];
  efficiencyBandOptions: MultiSelectOption[];
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onOpsChange: (value: string[]) => void;
  onFinishedProductsChange: (value: string[]) => void;
  onOperationsChange: (value: string[]) => void;
  onEmployeesChange: (value: string[]) => void;
  onWorkCentersChange: (value: string[]) => void;
  onShiftsChange: (value: EficienciaFabrilShift[]) => void;
  onEfficiencyBandsChange: (value: EficienciaFabrilEfficiencyBand[]) => void;
  disabled?: boolean;
};

export function FilterBar({
  dateStart,
  dateEnd,
  ops,
  finishedProducts,
  operations,
  employees,
  workCenters,
  shifts,
  efficiencyBands,
  opOptions,
  finishedProductOptions,
  operationOptions,
  employeeOptions,
  workCenterOptions,
  shiftOptions,
  efficiencyBandOptions,
  onDateStartChange,
  onDateEndChange,
  onOpsChange,
  onFinishedProductsChange,
  onOperationsChange,
  onEmployeesChange,
  onWorkCentersChange,
  onShiftsChange,
  onEfficiencyBandsChange,
  disabled = false,
}: FilterBarProps) {
  const operationFilterEnabled = finishedProducts.length > 0;

  return (
    <FilterBarShell ariaLabel="Filtros do dashboard">
        <label className="ef-field">
          <FieldLabel label="Data início" hint={EF_HELP_TOOLTIPS.filters.dateStart}  className="ef-field__label" />
          <NativeTextControl
            type="date"
            value={dateStart}
            disabled={disabled}
            onChange={onDateStartChange}
          />
        </label>

        <label className="ef-field">
          <FieldLabel label="Data fim" hint={EF_HELP_TOOLTIPS.filters.dateEnd}  className="ef-field__label" />
          <NativeTextControl
            type="date"
            value={dateEnd}
            disabled={disabled}
            onChange={onDateEndChange}
          />
        </label>

        <MultiSelectField
          label="Operador (nome)"
          labelHint={EF_HELP_TOOLTIPS.filters.operator}
          emptyLabel="Todos"
          searchable
          options={employeeOptions}
          selectedValues={employees}
          onChange={onEmployeesChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="OP"
          labelHint={EF_HELP_TOOLTIPS.filters.op}
          emptyLabel="Todas"
          searchable
          options={opOptions}
          selectedValues={ops}
          onChange={onOpsChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="PA (produto acabado)"
          labelHint={EF_HELP_TOOLTIPS.filters.finishedProduct}
          emptyLabel="Todos"
          searchable
          options={finishedProductOptions}
          selectedValues={finishedProducts}
          onChange={onFinishedProductsChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="Operação"
          labelHint={EF_HELP_TOOLTIPS.filters.operation}
          emptyLabel={operationFilterEnabled ? "Todas" : "Selecione um PA"}
          searchable={operationFilterEnabled}
          options={operationOptions}
          selectedValues={operations}
          onChange={onOperationsChange}
          disabled={disabled || !operationFilterEnabled}
        />

        <MultiSelectField
          label="Centro de trabalho"
          labelHint={EF_HELP_TOOLTIPS.filters.workCenter}
          emptyLabel="Todos"
          searchable
          options={workCenterOptions}
          selectedValues={workCenters}
          onChange={onWorkCentersChange}
          disabled={disabled}
        />

        <MultiSelectField
          label="Turno"
          labelHint={EF_HELP_TOOLTIPS.filters.shift}
          emptyLabel="Todos"
          options={shiftOptions}
          selectedValues={shifts}
          onChange={(values) => onShiftsChange(values as EficienciaFabrilShift[])}
          disabled={disabled}
        />

        <MultiSelectField
          label="Faixa de eficiência"
          labelHint={EF_HELP_TOOLTIPS.filters.efficiencyBands}
          emptyLabel="Todas"
          options={efficiencyBandOptions}
          selectedValues={efficiencyBands}
          onChange={(values) =>
            onEfficiencyBandsChange(values as EficienciaFabrilEfficiencyBand[])
          }
          disabled={disabled}
        />
    </FilterBarShell>
  );
}
