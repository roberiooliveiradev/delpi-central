import {
  CommercialDateField,
  CommercialMultiSelectField,
  CommercialSelectField,
  cmFiltersKit,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { SellerScopeFilter } from "../../customers/components/SellerScopeFilter";
import { ANALYTICS_BRANCH_OPTIONS } from "../utils/analyticsBranchFilters";
import type { AnalyticsFilterUrlState } from "../utils/analyticsFilterUrl";
import type { SellerPortfolio } from "../../../types/portfolio";

type AnalyticsFiltersProps = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  branches: string[];
  customerSegment: AnalyticsFilterUrlState["customerSegment"];
  sellerIds?: string[];
  canFilterPortfolios?: boolean;
  canUseTeamScope?: boolean;
  filterablePortfolios?: SellerPortfolio[];
  onDateStart: (value: string) => void;
  onDateEnd: (value: string) => void;
  onCompetence: (value: string) => void;
  onBranches: (value: string[]) => void;
  onCustomerSegment: (value: AnalyticsFilterUrlState["customerSegment"]) => void;
  onSellerIds?: (value: string[]) => void;
};

export function AnalyticsFilters({
  dateStart,
  dateEnd,
  competence,
  branches,
  customerSegment,
  sellerIds = [],
  canFilterPortfolios = false,
  canUseTeamScope = false,
  filterablePortfolios = [],
  onDateStart,
  onDateEnd,
  onCompetence,
  onBranches,
  onCustomerSegment,
  onSellerIds,
}: AnalyticsFiltersProps) {
  const { FiltersRow } = cmFiltersKit;

  return (
    <FiltersRow variant="extended">
      <CommercialDateField
        label={ANALYTICS_CONTENT.filters.start}
        value={dateStart}
        onChange={onDateStart}
        hint={CM_HELP.analytics.filterDateStart}
      />
      <CommercialDateField
        label={ANALYTICS_CONTENT.filters.end}
        value={dateEnd}
        onChange={onDateEnd}
        hint={CM_HELP.analytics.filterDateEnd}
      />
      <CommercialDateField
        type="month"
        label={ANALYTICS_CONTENT.filters.competence}
        value={competence}
        onChange={onCompetence}
        hint={CM_HELP.analytics.filterCompetence}
      />
      <CommercialMultiSelectField
        label={ANALYTICS_CONTENT.filters.branch}
        selectedValues={branches}
        onChange={onBranches}
        options={ANALYTICS_BRANCH_OPTIONS}
        emptyLabel="Todas"
        searchable
        hint={CM_HELP.analytics.filterBranch}
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
        hint={CM_HELP.analytics.filterSegment}
      />
      {canFilterPortfolios && onSellerIds ? (
        <SellerScopeFilter
          multiple
          sellers={filterablePortfolios}
          selectedValues={sellerIds}
          onChange={onSellerIds}
          teamScope={canUseTeamScope}
          hint={CM_HELP.analytics.portfolioFilter}
        />
      ) : null}
    </FiltersRow>
  );
}
