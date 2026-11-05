import { KAIZEN_STATUSES, SAVINGS_TYPES } from "../constants/kaizen";
import { KAIZEN_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FilterInputField, FiltersRow, MultiSelectField } from "./ui";

type KaizenRecordFiltersProps = {
  branches: string[];
  statuses: string[];
  savingsTypes: string[];
  title: string;
  branchOptions: Array<{ value: string; label: string }>;
  allowAllBranches?: boolean;
  onBranchesChange: (value: string[]) => void;
  onStatusesChange: (value: string[]) => void;
  onSavingsTypesChange: (value: string[]) => void;
  onTitleChange: (value: string) => void;
};

export function KaizenRecordFilters({
  branches,
  statuses,
  savingsTypes,
  title,
  branchOptions,
  allowAllBranches = true,
  onBranchesChange,
  onStatusesChange,
  onSavingsTypesChange,
  onTitleChange,
}: KaizenRecordFiltersProps) {
  const showUnitFilter = allowAllBranches && branchOptions.length > 1;

  return (
    <FiltersRow ariaLabel="Filtros de kaizen">
      {showUnitFilter ? (
        <MultiSelectField
          label="Unidade"
          labelHint={KAIZEN_HELP_TOOLTIPS.fields.branch}
          options={branchOptions}
          selectedValues={branches}
          onChange={onBranchesChange}
          emptyLabel="Todas"
        />
      ) : null}
      <MultiSelectField
        label="Status"
        labelHint={KAIZEN_HELP_TOOLTIPS.fields.status}
        options={[...KAIZEN_STATUSES]}
        selectedValues={statuses}
        onChange={onStatusesChange}
        emptyLabel="Todos"
      />
      <MultiSelectField
        label="Tipo de economia"
        labelHint={KAIZEN_HELP_TOOLTIPS.fields.savingsType}
        options={[...SAVINGS_TYPES]}
        selectedValues={savingsTypes}
        onChange={onSavingsTypesChange}
        emptyLabel="Todos"
      />
      <FilterInputField
        id="kz-filter-title"
        label="Título"
        hint="Filtra os cadastros cujo título contém o texto informado."
        type="text"
        value={title}
        placeholder="Buscar por título"
        onChange={onTitleChange}
      />
    </FiltersRow>
  );
}
