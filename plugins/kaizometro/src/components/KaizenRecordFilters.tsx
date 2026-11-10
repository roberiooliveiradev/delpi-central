import { KAIZEN_DATE_FIELDS, KAIZEN_STATUSES, SAVINGS_TYPES } from "../constants/kaizen";
import { KAIZEN_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FilterInputField, FiltersRow, MultiSelectField } from "./ui";
import { KZ_GHOST_BTN } from "./ui/ghostChrome";

type KaizenRecordFiltersProps = {
  branches: string[];
  statuses: string[];
  savingsTypes: string[];
  dateFields: string[];
  ideaMonth: string;
  dateStart: string;
  dateEnd: string;
  title: string;
  branchOptions: Array<{ value: string; label: string }>;
  allowAllBranches?: boolean;
  onBranchesChange: (value: string[]) => void;
  onStatusesChange: (value: string[]) => void;
  onSavingsTypesChange: (value: string[]) => void;
  onDateFieldsChange: (value: string[]) => void;
  onIdeaMonthChange: (value: string) => void;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onTitleChange: (value: string) => void;
  onClear: () => void;
};

export function KaizenRecordFilters({
  branches,
  statuses,
  savingsTypes,
  dateFields,
  ideaMonth,
  dateStart,
  dateEnd,
  title,
  branchOptions,
  allowAllBranches = true,
  onBranchesChange,
  onStatusesChange,
  onSavingsTypesChange,
  onDateFieldsChange,
  onIdeaMonthChange,
  onDateStartChange,
  onDateEndChange,
  onTitleChange,
  onClear,
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
        id="kz-filter-idea-month"
        label="Mês das ideias"
        hint="Filtra pela data de recebimento da ideia. Substitui o período e a coluna de data atuais."
        type="month"
        value={ideaMonth}
        onChange={onIdeaMonthChange}
      />
      <MultiSelectField
        label="Coluna de data"
        hint="Em qual coluna de data o período será aplicado. Vazio = todas."
        options={[...KAIZEN_DATE_FIELDS]}
        selectedValues={dateFields}
        onChange={onDateFieldsChange}
        emptyLabel="Todas"
      />
      <FilterInputField
        id="kz-filter-date-start"
        label="Data inicial"
        hint="Início do período aplicado à(s) coluna(s) de data selecionada(s)."
        type="date"
        value={dateStart}
        onChange={onDateStartChange}
      />
      <FilterInputField
        id="kz-filter-date-end"
        label="Data final"
        hint="Fim do período aplicado à(s) coluna(s) de data selecionada(s)."
        type="date"
        value={dateEnd}
        onChange={onDateEndChange}
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
      <button type="button" className={KZ_GHOST_BTN} onClick={onClear}>
        Limpar filtros
      </button>
    </FiltersRow>
  );
}
