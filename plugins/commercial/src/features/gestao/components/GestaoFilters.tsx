import {
  CommercialDateField,
  CommercialMultiSelectField,
  CommercialSelectField,
  cmFiltersKit,
} from "../../../app/commercialUi";
import { GESTAO_CONTENT } from "../../../content/analyticsContent";
import { GESTAO_BRANCH_OPTIONS } from "../utils/gestaoBranchFilters";
import type { GestaoFilterUrlState } from "../utils/gestaoFilterUrl";

type GestaoFiltersProps = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  branches: string[];
  customerSegment: GestaoFilterUrlState["customerSegment"];
  onDateStart: (value: string) => void;
  onDateEnd: (value: string) => void;
  onCompetence: (value: string) => void;
  onBranches: (value: string[]) => void;
  onCustomerSegment: (value: GestaoFilterUrlState["customerSegment"]) => void;
};

export function GestaoFilters({
  dateStart,
  dateEnd,
  competence,
  branches,
  customerSegment,
  onDateStart,
  onDateEnd,
  onCompetence,
  onBranches,
  onCustomerSegment,
}: GestaoFiltersProps) {
  const { FiltersRow } = cmFiltersKit;

  return (
    <FiltersRow variant="extended">
      <CommercialDateField
        label={GESTAO_CONTENT.filters.start}
        value={dateStart}
        onChange={onDateStart}
      />
      <CommercialDateField
        label={GESTAO_CONTENT.filters.end}
        value={dateEnd}
        onChange={onDateEnd}
      />
      <CommercialSelectField
        label={GESTAO_CONTENT.filters.competence}
        value={competence}
        onChange={onCompetence}
        options={buildCompetenceOptions()}
        allowEmpty
        emptyLabel="Livre"
      />
      <CommercialMultiSelectField
        label={GESTAO_CONTENT.filters.branch}
        selectedValues={branches}
        onChange={onBranches}
        options={GESTAO_BRANCH_OPTIONS}
      />
      <CommercialSelectField
        label={GESTAO_CONTENT.filters.segment}
        value={customerSegment}
        onChange={(value) =>
          onCustomerSegment(value === "weg" || value === "new_business" ? value : "")
        }
        options={[
          { value: "weg", label: GESTAO_CONTENT.filters.segmentWeg },
          { value: "new_business", label: GESTAO_CONTENT.filters.segmentNewBusiness },
        ]}
        allowEmpty
        emptyLabel={GESTAO_CONTENT.filters.segmentAll}
      />
    </FiltersRow>
  );
}

function buildCompetenceOptions(): Array<{ value: string; label: string }> {
  const now = new Date();
  const options: Array<{ value: string; label: string }> = [];
  for (let i = 0; i < 18; i += 1) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    const label = date.toLocaleDateString("pt-BR", { month: "short", year: "numeric" });
    options.push({ value, label });
  }
  return options;
}
