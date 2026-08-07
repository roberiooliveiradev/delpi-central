import {
  CommercialDateField,
  CommercialMultiSelectField,
  CommercialSelectField,
  cmFiltersKit,
} from "../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { ANALYTICS_BRANCH_OPTIONS } from "../utils/analyticsBranchFilters";
import type { AnalyticsFilterUrlState } from "../utils/analyticsFilterUrl";

type AnalyticsFiltersProps = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  branches: string[];
  customerSegment: AnalyticsFilterUrlState["customerSegment"];
  onDateStart: (value: string) => void;
  onDateEnd: (value: string) => void;
  onCompetence: (value: string) => void;
  onBranches: (value: string[]) => void;
  onCustomerSegment: (value: AnalyticsFilterUrlState["customerSegment"]) => void;
};

export function AnalyticsFilters({
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
}: AnalyticsFiltersProps) {
  const { FiltersRow } = cmFiltersKit;

  return (
    <FiltersRow variant="extended">
      <CommercialDateField
        label={ANALYTICS_CONTENT.filters.start}
        value={dateStart}
        onChange={onDateStart}
      />
      <CommercialDateField
        label={ANALYTICS_CONTENT.filters.end}
        value={dateEnd}
        onChange={onDateEnd}
      />
      <CommercialSelectField
        label={ANALYTICS_CONTENT.filters.competence}
        value={competence}
        onChange={onCompetence}
        options={buildCompetenceOptions()}
        allowEmpty
        emptyLabel="Livre"
      />
      <CommercialMultiSelectField
        label={ANALYTICS_CONTENT.filters.branch}
        selectedValues={branches}
        onChange={onBranches}
        options={ANALYTICS_BRANCH_OPTIONS}
      />
      <CommercialSelectField
        label={ANALYTICS_CONTENT.filters.segment}
        value={customerSegment}
        onChange={(value) =>
          onCustomerSegment(value === "weg" || value === "new_business" ? value : "")
        }
        options={[
          { value: "weg", label: ANALYTICS_CONTENT.filters.segmentWeg },
          { value: "new_business", label: ANALYTICS_CONTENT.filters.segmentNewBusiness },
        ]}
        allowEmpty
        emptyLabel={ANALYTICS_CONTENT.filters.segmentAll}
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
