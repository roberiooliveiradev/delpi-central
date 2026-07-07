import { BRANCHES, KAIZEN_STATUSES, SAVINGS_TYPES } from "../constants/kaizen";
import { KAIZEN_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FilterInputField, FilterSelectField, FiltersRow } from "./ui/FiltersKit";

type KaizenRecordFiltersProps = {
  branch: string;
  status: string;
  savingsType: string;
  title: string;
  onBranchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onSavingsTypeChange: (value: string) => void;
  onTitleChange: (value: string) => void;
};

const BRANCH_OPTIONS = BRANCHES.map((item) => ({ value: item.code, label: item.label }));

export function KaizenRecordFilters({
  branch,
  status,
  savingsType,
  title,
  onBranchChange,
  onStatusChange,
  onSavingsTypeChange,
  onTitleChange,
}: KaizenRecordFiltersProps) {
  return (
    <FiltersRow ariaLabel="Filtros de kaizen">
      <FilterSelectField
        id="kz-filter-branch"
        label="Unidade"
        hint={KAIZEN_HELP_TOOLTIPS.fields.branch}
        value={branch}
        onChange={onBranchChange}
        options={BRANCH_OPTIONS}
        placeholderOption="Todas"
      />
      <FilterSelectField
        id="kz-filter-status"
        label="Status"
        hint={KAIZEN_HELP_TOOLTIPS.fields.status}
        value={status}
        onChange={onStatusChange}
        options={KAIZEN_STATUSES}
        placeholderOption="Todos"
      />
      <FilterSelectField
        id="kz-filter-savings-type"
        label="Tipo de economia"
        hint={KAIZEN_HELP_TOOLTIPS.fields.savingsType}
        value={savingsType}
        onChange={onSavingsTypeChange}
        options={SAVINGS_TYPES}
        placeholderOption="Todos"
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
