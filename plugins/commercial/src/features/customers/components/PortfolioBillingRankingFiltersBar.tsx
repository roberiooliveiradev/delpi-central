import type { ReactNode } from "react";

import {
  CommercialFilterBarShell,
  CommercialSectionHintLabel,
  CommercialSegmentToggle,
  CommercialSelectField,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  BILLING_SERIES_PRESET_OPTIONS,
  type BillingSeriesPeriodPreset,
} from "../utils/billingSeriesPeriod";

export const RANKING_LIMIT_OPTIONS = [10, 15, 20, 50] as const;
export type RankingLimit = (typeof RANKING_LIMIT_OPTIONS)[number];
export type RankingOrder = "growth" | "decline";
export type RankingGroupBy = "customer" | "seller";
export type RankingPeriodPreset = Exclude<BillingSeriesPeriodPreset, "custom">;

export type PortfolioBillingRankingFilters = {
  groupBy: RankingGroupBy;
  order: RankingOrder;
  limit: RankingLimit;
  periodPreset: RankingPeriodPreset;
};

const RANKING_PERIOD_OPTIONS = BILLING_SERIES_PRESET_OPTIONS.filter(
  (option): option is { id: RankingPeriodPreset; label: string } =>
    option.id !== "custom",
);

type PortfolioBillingRankingFiltersBarProps = {
  filters: PortfolioBillingRankingFilters;
  onChange: (next: Partial<PortfolioBillingRankingFilters>) => void;
  canUseTeamScope: boolean;
  sellerFilter?: ReactNode;
};

export function PortfolioBillingRankingFiltersBar({
  filters,
  onChange,
  canUseTeamScope,
  sellerFilter = null,
}: PortfolioBillingRankingFiltersBarProps) {
  const effectiveGroupBy =
    filters.groupBy === "seller" && canUseTeamScope ? "seller" : "customer";

  return (
    <CommercialFilterBarShell
      embedded
      ariaLabel={CM_HELP.customers.billingRanking}
      className="cm-customers-page__filter-bar cm-customers-page__filter-bar--ranking"
    >
      <div className="cm-customers-page__ranking-period">
        <CommercialSectionHintLabel
          label="Período"
          hint={CM_HELP.customers.billingSeriesPeriod}
        />
        <CommercialSegmentToggle
          ariaLabel={CM_HELP.customers.billingSeriesPeriod}
          idPrefix="customers-ranking-period"
          value={filters.periodPreset}
          onChange={(value) => {
            const next = RANKING_PERIOD_OPTIONS.find((option) => option.id === value);
            if (next) onChange({ periodPreset: next.id });
          }}
          options={RANKING_PERIOD_OPTIONS.map((option) => ({
            value: option.id,
            label: option.label,
          }))}
        />
      </div>
      {canUseTeamScope ? (
        <CommercialSegmentToggle
          ariaLabel="Agrupar ranking"
          idPrefix="customers-ranking-group"
          value={effectiveGroupBy}
          onChange={(value) =>
            onChange({ groupBy: value === "seller" ? "seller" : "customer" })
          }
          options={[
            { value: "customer", label: "Cliente" },
            { value: "seller", label: "Vendedor" },
          ]}
        />
      ) : null}
      <CommercialSegmentToggle
        ariaLabel="Foco do ranking"
        idPrefix="customers-ranking-order"
        value={filters.order}
        onChange={(value) =>
          onChange({ order: value === "decline" ? "decline" : "growth" })
        }
        options={[
          { value: "growth", label: "Maiores altas" },
          { value: "decline", label: "Maiores quedas" },
        ]}
      />
      <CommercialSelectField
        label="Top N"
        value={String(filters.limit)}
        onChange={(value) => {
          const parsed = Number(value);
          if (RANKING_LIMIT_OPTIONS.includes(parsed as RankingLimit)) {
            onChange({ limit: parsed as RankingLimit });
          }
        }}
        options={RANKING_LIMIT_OPTIONS.map((n) => ({
          value: String(n),
          label: String(n),
        }))}
      />
      {sellerFilter}
    </CommercialFilterBarShell>
  );
}
