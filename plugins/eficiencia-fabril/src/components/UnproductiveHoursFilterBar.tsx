import { FieldLabel, NativeTextControl, createFilterBarShell } from "@delpi/plugin-ui/index";

import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { UnproductiveHoursFilterFormState } from "../types/unproductiveHours";

const FilterBarShell = createFilterBarShell({
  prefix: "ef",
  withGrid: true,
  defaultAriaLabel: "Filtros de horas improdutivas",
});

type UnproductiveHoursFilterBarProps = {
  dateStart: string;
  dateEnd: string;
  filters: UnproductiveHoursFilterFormState;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onFiltersChange: (next: UnproductiveHoursFilterFormState) => void;
  disabled?: boolean;
};

export function UnproductiveHoursFilterBar({
  dateStart,
  dateEnd,
  filters,
  onDateStartChange,
  onDateEndChange,
  onFiltersChange,
  disabled = false,
}: UnproductiveHoursFilterBarProps) {
  return (
    <FilterBarShell ariaLabel="Filtros de horas improdutivas">
      <label className="ef-field">
        <FieldLabel
          label="Data início"
          hint={EF_HELP_TOOLTIPS.filters.dateStart}
          className="ef-field__label"
        />
          <NativeTextControl
            type="date"
            value={dateStart}
            disabled={disabled}
            onChange={onDateStartChange}
          />
        </label>
      <label className="ef-field">
        <FieldLabel
          label="Data fim"
          hint={EF_HELP_TOOLTIPS.filters.dateEnd}
          className="ef-field__label"
        />
        <NativeTextControl
          type="date"
          value={dateEnd}
          disabled={disabled}
          onChange={onDateEndChange}
        />
      </label>
      <label className="ef-field">
        <FieldLabel
          label="Motivo"
          hint={EF_HELP_TOOLTIPS.unproductiveHours.filters.stopReason}
          className="ef-field__label"
        />
        <NativeTextControl
          type="text"
          value={filters.stopReason}
          disabled={disabled}
          placeholder="Ex.: RT, OT, MT"
          onChange={(value) => onFiltersChange({ ...filters, stopReason: value })}
        />
      </label>
      <label className="ef-field">
        <FieldLabel
          label="Operador (código)"
          hint={EF_HELP_TOOLTIPS.unproductiveHours.filters.operatorCode}
          className="ef-field__label"
        />
        <NativeTextControl
          type="text"
          value={filters.operatorCode}
          disabled={disabled}
          placeholder="Código do operador"
          onChange={(value) => onFiltersChange({ ...filters, operatorCode: value })}
        />
      </label>
      <label className="ef-field">
        <FieldLabel
          label="Recurso"
          hint={EF_HELP_TOOLTIPS.unproductiveHours.filters.resource}
          className="ef-field__label"
        />
        <NativeTextControl
          type="text"
          value={filters.resource}
          disabled={disabled}
          placeholder="Código do recurso"
          onChange={(value) => onFiltersChange({ ...filters, resource: value })}
        />
      </label>
      <label className="ef-field">
        <FieldLabel
          label="Centro de custo"
          hint={EF_HELP_TOOLTIPS.unproductiveHours.filters.costCenter}
          className="ef-field__label"
        />
        <NativeTextControl
          type="text"
          value={filters.costCenter}
          disabled={disabled}
          placeholder="Centro de custo"
          onChange={(value) => onFiltersChange({ ...filters, costCenter: value })}
        />
      </label>
    </FilterBarShell>
  );
}
