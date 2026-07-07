import { COMMERCIAL_BRANCH_OPTIONS } from "../constants/filterOptions";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "@delpi/plugin-ui";
import { MultiSelectField } from "./MultiSelectField";
import { FilterInputField, FiltersRow } from "./dashboardFiltersUi";
import type { CommercialFilterUrlState } from "../utils/filterUrl";
import { OPERATIONAL_UNIT_FIELD_LABEL } from "../utils/operationalUnitLabels";

type CommercialFiltersProps = {
  competence: string;
  dateStart: string;
  dateEnd: string;
  branches: string[];
  customerSegment: CommercialFilterUrlState["customerSegment"];
  onCompetenceChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchesChange: (values: string[]) => void;
  onCustomerSegmentChange: (
    value: CommercialFilterUrlState["customerSegment"]
  ) => void;
  className?: string;
};

export function CommercialFilters({
  competence,
  dateStart,
  dateEnd,
  branches,
  customerSegment,
  onCompetenceChange,
  onDateStartChange,
  onDateEndChange,
  onBranchesChange,
  onCustomerSegmentChange,
  className = "",
}: CommercialFiltersProps) {
  return (
    <FiltersRow className={className}>
      <FilterInputField
        id="dc-competence"
        label="Competência"
        hint={COMMERCIAL_HELP_TOOLTIPS.filters.competence}
        type="month"
        value={competence}
        onChange={onCompetenceChange}
      />
      <FilterInputField
        id="dc-date-start"
        label="Data inicial"
        hint={COMMERCIAL_HELP_TOOLTIPS.filters.dateStart}
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="dc-date-end"
        label="Data final"
        hint={COMMERCIAL_HELP_TOOLTIPS.filters.dateEnd}
        type="date"
        value={dateEnd}
        onChange={onDateEndChange}
      />
      <MultiSelectField
        label={`${OPERATIONAL_UNIT_FIELD_LABEL} (indicadores)`}
        labelHint={COMMERCIAL_HELP_TOOLTIPS.filters.branch}
        options={COMMERCIAL_BRANCH_OPTIONS}
        selectedValues={branches}
        onChange={onBranchesChange}
        emptyLabel="Todas"
        searchable
      />
      <label className="dc-filter-box dc-field">
        <FieldLabel
          label="Clientes"
          hint={COMMERCIAL_HELP_TOOLTIPS.filters.customerSegment}
          className="dc-field__label"
        />
        <select
          id="dc-customer-segment"
          value={customerSegment}
          onChange={(e) =>
            onCustomerSegmentChange(
              e.target.value as CommercialFilterUrlState["customerSegment"]
            )
          }
        >
          <option value="">Todos</option>
          <option value="weg">WEG</option>
          <option value="new_business">Novos negócios</option>
        </select>
      </label>
    </FiltersRow>
  );
}
