import { useCallback, useEffect, useState } from "react";
import { Filter } from "lucide-react";

import {
  matchPeriodPreset,
  PERIOD_PRESET_OPTIONS,
  resolvePeriodPreset,
  type PeriodPresetId,
} from "../../app/periodPreset";
import {
  buildSuppliesUnitOptions,
  canonicalizeUiBranches,
  resolveRequestedBranches,
  SUPPLIES_UNIT_FILTER_LABEL,
} from "../../app/suppliesUnits";
import { useCommittedTextFilter } from "../../app/useCommittedTextFilter";
import {
  listPurchaseRequestCostCenters,
  listPurchaseRequestRequesters,
  type PurchaseRequestCostCenterFacet,
  type PurchaseRequestRequesterFacet,
} from "./api";
import {
  SuppliesClearFiltersButton,
  SuppliesDateField,
  SuppliesFilterBarShell,
  SuppliesSectionHintLabel,
  SuppliesMultiSelectField,
  SuppliesSegmentToggle,
  SuppliesTextField,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
import { hasActivePurchaseRequestsFilters } from "./hasActiveFilters";
import { labelOverallStage } from "./query";
import type { OverallStage, PurchaseRequestsQuery } from "./types";
import { OVERALL_STAGE_VALUES } from "./types";

type PurchaseRequestsFiltersProps = {
  query: PurchaseRequestsQuery;
  units: readonly string[];
  onPatch: (patch: Partial<PurchaseRequestsQuery>) => void;
  onClear: () => void;
};

export function PurchaseRequestsFilters({
  query,
  units,
  onPatch,
  onClear,
}: PurchaseRequestsFiltersProps) {
  const { FiltersRow } = spFiltersKit;
  const unitOptions = buildSuppliesUnitOptions(units);
  const hasActiveFilters = hasActivePurchaseRequestsFilters(query);
  const stageOptions = OVERALL_STAGE_VALUES.map((stage) => ({
    value: stage,
    label: labelOverallStage(stage),
  }));
  const period = matchPeriodPreset(query.date_from, query.date_to);

  const commitRequestNumber = useCallback(
    (value: string) => onPatch({ request_number: value, page: 1 }),
    [onPatch],
  );
  const commitProduct = useCallback(
    (value: string) => onPatch({ product_code: value, page: 1 }),
    [onPatch],
  );

  const requestNumber = useCommittedTextFilter(query.request_number, commitRequestNumber);
  const product = useCommittedTextFilter(query.product_code, commitProduct);

  // Facets follow the authorized universe (branches + period), not the
  // value being filtered — a filter must not narrow its own options.
  const facetBranches = resolveRequestedBranches(query.branches, units);
  const facetScopeKey = `${facetBranches.join(",")}|${query.date_from}|${query.date_to}`;
  const [requesterOptions, setRequesterOptions] = useState<
    { value: string; label: string }[]
  >([]);
  const [costCenterOptions, setCostCenterOptions] = useState<
    { value: string; label: string }[]
  >([]);

  useEffect(() => {
    const controller = new AbortController();
    const scope = {
      branches: facetBranches,
      date_from: query.date_from,
      date_to: query.date_to,
    };
    listPurchaseRequestRequesters(scope, controller.signal)
      .then((items: PurchaseRequestRequesterFacet[]) => {
        setRequesterOptions(
          items
            .map((item) => {
              const value = (item.protheus_user_id || "").trim();
              if (!value) return null;
              const label =
                (item.display_name || "").trim() ||
                (item.name || "").trim() ||
                (item.code || "").trim() ||
                value;
              return { value, label };
            })
            .filter((item): item is { value: string; label: string } => item !== null),
        );
      })
      .catch(() => setRequesterOptions([]));
    listPurchaseRequestCostCenters(scope, controller.signal)
      .then((items: PurchaseRequestCostCenterFacet[]) => {
        const byCode = new Map<string, string>();
        for (const item of items) {
          const code = (item.code || "").trim();
          if (!code || byCode.has(code)) continue;
          const description = (item.description || "").trim();
          byCode.set(code, description ? `${code} — ${description}` : code);
        }
        setCostCenterOptions(
          [...byCode.entries()].map(([value, label]) => ({ value, label })),
        );
      })
      .catch(() => setCostCenterOptions([]));
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facetScopeKey]);

  const flushTextFilters = () => {
    requestNumber.flush();
    product.flush();
  };

  const onPeriod = (value: PeriodPresetId) => {
    if (value === "custom") return;
    const range = resolvePeriodPreset(value);
    if (!range) return;
    onPatch({ date_from: range.from, date_to: range.to, page: 1 });
  };

  return (
    <form
      className="sp-list-filters sp-purchase-requests__filters"
      onSubmit={(event) => {
        event.preventDefault();
        flushTextFilters();
      }}
    >
      <SuppliesFilterBarShell
        embedded
        ariaLabel={C.filtersAriaLabel}
        leading={
          <div className="sp-filter-bar__period-block">
            <div className="sp-filter-bar__header">
              <div className="sp-filter-bar__title">
                <Filter size={18} aria-hidden="true" />
                <h2>
                  <SuppliesSectionHintLabel
                    label={C.filtersTitle}
                    hint={SP_HELP.purchaseRequestsFilters}
                  />
                </h2>
              </div>
              {hasActiveFilters ? (
                <div className="sp-filter-bar__header-actions">
                  <SuppliesClearFiltersButton
                    density="compact"
                    label={C.clearFilters}
                    onClick={onClear}
                  />
                </div>
              ) : null}
            </div>
            <div className="sp-purchase-requests__period-presets">
              <SuppliesSectionHintLabel
                label={C.periodLabel}
                hint={SP_HELP.purchaseRequestsPeriod}
              />
              <SuppliesSegmentToggle
                ariaLabel={C.periodLabel}
                idPrefix="purchase-requests-period-preset"
                size="sm"
                value={period}
                onChange={(value) => onPeriod(value as PeriodPresetId)}
                options={PERIOD_PRESET_OPTIONS}
              />
            </div>
          </div>
        }
      >
        {null}
      </SuppliesFilterBarShell>
      <FiltersRow variant="extended">
        <SuppliesDateField
          label={C.dateFromLabel}
          value={query.date_from}
          onChange={(value) => onPatch({ date_from: value, page: 1 })}
          hint={SP_HELP.purchaseRequestsPeriod}
        />
        <SuppliesDateField
          label={C.dateToLabel}
          value={query.date_to}
          onChange={(value) => onPatch({ date_to: value, page: 1 })}
          hint={SP_HELP.purchaseRequestsPeriod}
        />
        <SuppliesMultiSelectField
          label={SUPPLIES_UNIT_FILTER_LABEL}
          hint={SP_HELP.purchaseRequestsBranch}
          selectedValues={query.branches}
          onChange={(values) =>
            onPatch({
              branches: canonicalizeUiBranches(values, units),
              page: 1,
            })
          }
          options={unitOptions}
          emptyLabel="Todas"
          searchable
        />
        <SuppliesTextField
          label={C.requestNumberLabel}
          value={requestNumber.draft}
          onChange={requestNumber.setDraft}
          hint={SP_HELP.purchaseRequestsNumber}
        />
        <SuppliesTextField
          label={C.productLabel}
          value={product.draft}
          onChange={product.setDraft}
          hint={SP_HELP.purchaseRequestsProduct}
        />
        <SuppliesMultiSelectField
          label={C.requesterLabel}
          hint={SP_HELP.purchaseRequestsRequester}
          selectedValues={query.requester_ids}
          onChange={(values) =>
            onPatch({ requester_ids: values, page: 1 })
          }
          options={requesterOptions}
          emptyLabel={C.requesterAll}
          searchable
        />
        <SuppliesMultiSelectField
          label={C.costCenterLabel}
          hint={SP_HELP.purchaseRequestsCostCenter}
          selectedValues={query.cost_centers}
          onChange={(values) =>
            onPatch({ cost_centers: values, page: 1 })
          }
          options={costCenterOptions}
          emptyLabel={C.costCenterAll}
          searchable
        />
        <SuppliesMultiSelectField
          label={C.stageLabel}
          hint={SP_HELP.purchaseRequestsStage}
          selectedValues={query.overall_stages}
          onChange={(values) => {
            onPatch({
              overall_stages: values as OverallStage[],
              page: 1,
            });
          }}
          options={stageOptions}
          emptyLabel={C.stageAll}
          searchable={false}
        />
      </FiltersRow>
    </form>
  );
}
