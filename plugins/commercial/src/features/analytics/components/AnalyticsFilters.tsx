import {
  CommercialDateField,
  CommercialMultiSelectField,
  CommercialSelectField,
  cmFiltersKit,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { SellerScopeFilter, ANALYTICS_PORTFOLIO_FILTER_EMPTY_LABEL } from "../../customers/components/SellerScopeFilter";
import { ANALYTICS_BRANCH_OPTIONS } from "../utils/analyticsBranchFilters";
import type { PeriodPresetId } from "../utils/periodPreset";
import type { AnalyticsFilterUrlState } from "../utils/analyticsFilterUrl";
import type { SellerPortfolio } from "../../../types/portfolio";

type AnalyticsFiltersProps = {
  dateStart: string;
  dateEnd: string;
  competence: string;
  periodPreset?: PeriodPresetId;
  branches: string[];
  customerSegment: AnalyticsFilterUrlState["customerSegment"];
  sellerIds?: string[];
  canFilterPortfolios?: boolean;
  canUseTeamScope?: boolean;
  filterablePortfolios?: SellerPortfolio[];
  onDateStart: (value: string) => void;
  onDateEnd: (value: string) => void;
  onCompetence: (value: string) => void;
  onPeriodPreset?: (value: PeriodPresetId) => void;
  onBranches: (value: string[]) => void;
  onCustomerSegment: (value: AnalyticsFilterUrlState["customerSegment"]) => void;
  onSellerIds?: (value: string[]) => void;
};

export function AnalyticsFilters({
  dateStart,
  dateEnd,
  competence,
  periodPreset = "custom",
  branches,
  customerSegment,
  sellerIds = [],
  canFilterPortfolios = false,
  canUseTeamScope = false,
  filterablePortfolios = [],
  onDateStart,
  onDateEnd,
  onCompetence,
  onPeriodPreset,
  onBranches,
  onCustomerSegment,
  onSellerIds,
}: AnalyticsFiltersProps) {
  const { FiltersRow } = cmFiltersKit;

  return (
    <FiltersRow variant="extended">
      {onPeriodPreset ? (
        <CommercialSelectField
          label={ANALYTICS_CONTENT.filters.periodPreset}
          value={periodPreset === "custom" ? "" : periodPreset}
          onChange={(value) => {
            if (value === "mtd" || value === "ytd") {
              onPeriodPreset(value);
              return;
            }
            onPeriodPreset("custom");
          }}
          options={[
            { value: "mtd", label: ANALYTICS_CONTENT.filters.periodPresetMtd },
            { value: "ytd", label: ANALYTICS_CONTENT.filters.periodPresetYtd },
          ]}
          allowEmpty
          emptyLabel={ANALYTICS_CONTENT.filters.periodPresetCustom}
          hint={CM_HELP.analytics.filterPeriodPreset}
        />
      ) : null}
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
        className="cm-analytics-unit-filter"
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
          emptyLabel={ANALYTICS_PORTFOLIO_FILTER_EMPTY_LABEL}
          hint={CM_HELP.analytics.portfolioFilter}
        />
      ) : null}
    </FiltersRow>
  );
}
