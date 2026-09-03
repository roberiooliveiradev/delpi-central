import type { ReactNode } from "react";

import {
  CommercialClearFiltersButton,
  CommercialFilterBarShell,
  CommercialScopeChipBar,
  CommercialSectionHintLabel,
  CommercialSelectField,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  BILLING_SERIES_PRESET_OPTIONS,
  DEFAULT_BILLING_SERIES_PRESET,
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

export const DEFAULT_RANKING_FILTERS: PortfolioBillingRankingFilters = {
  groupBy: "customer",
  order: "growth",
  limit: 20,
  periodPreset: DEFAULT_BILLING_SERIES_PRESET,
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

  const hasActiveFilters =
    effectiveGroupBy !== DEFAULT_RANKING_FILTERS.groupBy ||
    filters.order !== DEFAULT_RANKING_FILTERS.order ||
    filters.limit !== DEFAULT_RANKING_FILTERS.limit ||
    filters.periodPreset !== DEFAULT_RANKING_FILTERS.periodPreset;

  const periodChips = RANKING_PERIOD_OPTIONS.map((option) => ({
    id: option.id,
    label: option.label,
    active: filters.periodPreset === option.id,
    onSelect: () => onChange({ periodPreset: option.id }),
  }));

  const groupChips = [
    {
      id: "customer",
      label: "Cliente",
      active: effectiveGroupBy === "customer",
      onSelect: () => onChange({ groupBy: "customer" }),
    },
    ...(canUseTeamScope
      ? [
          {
            id: "seller",
            label: "Vendedor",
            active: effectiveGroupBy === "seller",
            onSelect: () => onChange({ groupBy: "seller" }),
          },
        ]
      : []),
  ];

  const orderChips = [
    {
      id: "growth",
      label: "Maiores altas",
      active: filters.order === "growth",
      onSelect: () => onChange({ order: "growth" }),
    },
    {
      id: "decline",
      label: "Maiores quedas",
      active: filters.order === "decline",
      onSelect: () => onChange({ order: "decline" }),
    },
  ];

  return (
    <>
      <div className="cm-customers-page__chip-row">
        <CommercialScopeChipBar
          label={
            <CommercialSectionHintLabel
              label="Período"
              hint={CM_HELP.customers.billingSeriesPeriod}
            />
          }
          aria-label={CM_HELP.customers.billingSeriesPeriod}
          chips={periodChips}
        />
        {canUseTeamScope ? (
          <CommercialScopeChipBar
            label={
              <CommercialSectionHintLabel
                label="Agrupar"
                hint={CM_HELP.customers.rankingGroup}
              />
            }
            aria-label={CM_HELP.customers.rankingGroup}
            chips={groupChips}
          />
        ) : null}
        <CommercialScopeChipBar
          label={
            <CommercialSectionHintLabel
              label="Foco"
              hint={CM_HELP.customers.rankingOrder}
            />
          }
          aria-label={CM_HELP.customers.rankingOrder}
          chips={orderChips}
        />
      </div>
      <CommercialFilterBarShell
        embedded
        ariaLabel={CM_HELP.customers.billingRanking}
        className="cm-customers-page__filter-bar"
      >
        <CommercialSelectField
          label="Top N"
          hint={CM_HELP.customers.rankingLimit}
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
        {hasActiveFilters ? (
          <div className="cm-customers-page__filter-actions">
            <CommercialClearFiltersButton
              onClick={() => onChange({ ...DEFAULT_RANKING_FILTERS })}
            />
          </div>
        ) : null}
      </CommercialFilterBarShell>
    </>
  );
}
