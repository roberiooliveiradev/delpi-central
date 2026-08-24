import {
  ExcelExportButton,
  SectionHintLabel,
  createDashboardFiltersKit,
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  createDashboardStatusBadge,
} from "@delpi/plugin-ui/index";
import { AlertTriangle, CalendarClock, Layers, PackageSearch } from "lucide-react";
import { useMemo, useState } from "react";

import { copy } from "../content/copy";
import { useFinishedProductShortages } from "../hooks/useFinishedProductShortages";
import type {
  FinishedProductShortageMaterial,
  FinishedProductShortagePayload,
  FinishedProductShortageSet,
  MaterialsSetStatus,
  PpcBranch,
} from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import {
  asMaterialsSetStatus,
  canQueryFinishedProductShortages,
  countSetMaterialsByStatus,
  deliveryMapOrderHref,
  filterSetMaterials,
  machineLoadLocateHref,
  safetyStockHref,
  uniqueMaterialAvailability,
} from "../utils/finishedProductShortageQuery";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { downloadFinishedProductShortageExcel } from "../utils/materialsExcel";
import { navigatePpc } from "../utils/routeParser";
import { FinishedProductShortageLedgerModal } from "./FinishedProductShortageLedgerModal";

const KpiCard = createDashboardKpiCard({ prefix: "ppc", labels: copy.kpi });
const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });
const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "ppc",
  labels: { filtersAriaLabel: copy.materials.paShortage.searchAria },
});

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.materials.paShortage.loading,
  },
});

type FinishedProductShortagePanelProps = {
  branch: PpcBranch;
  productQuery: string;
  draft: string;
  status: MaterialsSetStatus;
  didactic?: FinishedProductShortagePayload["didactic"];
  onDraftChange: (value: string) => void;
  onSubmit: (code: string) => void;
  onStatusChange: (status: MaterialsSetStatus) => void;
};

function setBadge(status: FinishedProductShortageSet["status"]) {
  if (status === "shortage") {
    return { label: copy.materials.paShortage.statusShortage, variant: "danger" as const };
  }
  if (status === "no_commitment") {
    return { label: copy.materials.paShortage.statusNoCommitment, variant: "warning" as const };
  }
  return { label: copy.materials.paShortage.statusOk, variant: "success" as const };
}

function formatQty(value: number | null | undefined, unit?: string): string {
  if (value == null) return "—";
  return `${formatOpQuantity(value)}${unit ? ` ${unit}` : ""}`;
}

function materialStatusLabel(status: FinishedProductShortageMaterial["status"]): string {
  const texts = copy.materials.paShortage;
  if (status === "shortage") return texts.materialShortage;
  if (status === "no_commitment") return texts.materialNoCommitment;
  return texts.materialOk;
}

export function FinishedProductShortagePanel({
  branch,
  productQuery,
  draft,
  status,
  didactic,
  onDraftChange,
  onSubmit,
}: FinishedProductShortagePanelProps) {
  const texts = copy.materials.paShortage;
  const { data, loading, error, canFetch } = useFinishedProductShortages(
    branch,
    productQuery,
    "all",
  );
  const [selected, setSelected] = useState<{
    material: FinishedProductShortageMaterial;
    motherOrder: string;
  } | null>(null);

  const steps = didactic?.steps ?? data?.didactic.steps ?? texts.steps;
  const ledger = useMemo(() => {
    if (!selected || !data) return [];
    const row = data.materials.find((item) => item.product_code === selected.material.product_code);
    return row?.ledger ?? [];
  }, [data, selected]);
  const availability = uniqueMaterialAvailability(data?.sets ?? []);
  const visibleSets = useMemo(() => {
    const sets = data?.sets ?? [];
    if (status === "all") return sets;
    return sets.filter((set) => set.status === status);
  }, [data?.sets, status]);

  const handleSubmit = () => {
    const code = draft.trim();
    if (!canQueryFinishedProductShortages(code)) return;
    onSubmit(code);
  };

  const showStory = !canFetch;

  return (
    <section className="ppc-pa-shortage" aria-label={texts.title}>
      {showStory ? (
        <div className="ppc-pa-shortage__story">
          <SectionHintLabel label={texts.howTitle} hint={texts.emptyIdle} />
          <ol className="ppc-pa-shortage__steps">
            {steps.map((step) => (
              <li key={step.step}>
                <strong>
                  {step.step}. {step.title}
                </strong>
                <span>{step.body}</span>
              </li>
            ))}
          </ol>
        </div>
      ) : null}

      <form
        className="ppc-pa-shortage__form"
        onSubmit={(event) => {
          event.preventDefault();
          handleSubmit();
        }}
      >
        <FiltersRow
          trailing={
            <button type="submit" className="ppc-pa-shortage__submit">
              {texts.submit}
            </button>
          }
        >
          <FilterInputField
            label={texts.searchLabel}
            type="search"
            value={draft}
            onChange={onDraftChange}
            placeholder={texts.searchPlaceholder}
          />
        </FiltersRow>
      </form>
      {showStory ? <p className="ppc-pa-shortage__hint">{texts.exampleHint}</p> : null}

      {!canFetch && draft.trim() && !canQueryFinishedProductShortages(draft) ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {texts.invalidCode}
        </div>
      ) : null}

      {loading ? <LoadingCard title={texts.loading} description={texts.loadingHint} /> : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {!canFetch && !loading ? <p className="ppc-state">{texts.emptyIdle}</p> : null}

      {data && data.state !== "ok" ? (
        <div className="ppc-state" role="status">
          {data.message}
        </div>
      ) : null}

      {data && data.state === "ok" ? (
        <>
          <header className="ppc-pa-shortage__result-head">
            <h2 className="ppc-pa-shortage__product">
              {data.product.product_code}
              {data.product.product_description ? ` · ${data.product.product_description}` : ""}
            </h2>
            <ExcelExportButton
              label={texts.exportLabel}
              onExport={() =>
                downloadFinishedProductShortageExcel(
                  visibleSets,
                  texts.exportFileName(branch, data.product.product_code),
                )
              }
              disabled={visibleSets.length === 0}
            />
          </header>

          <div className="ppc-demand-kpi-grid ppc-pa-shortage__kpis" aria-label={texts.title}>
            <KpiCard
              className="ppc-board-card"
              title={texts.kpiSets}
              icon={<Layers size={20} strokeWidth={1.75} />}
              value={String(data.summary.open_set_count)}
            />
            <KpiCard
              className="ppc-board-card"
              title={texts.kpiAtRisk}
              icon={<AlertTriangle size={20} strokeWidth={1.75} />}
              value={String(data.summary.at_risk_set_count)}
            />
            <KpiCard
              className="ppc-board-card"
              title={texts.kpiShortMp}
              icon={<PackageSearch size={20} strokeWidth={1.75} />}
              value={String(data.summary.short_mp_count)}
            />
            <KpiCard
              className="ppc-board-card ppc-pa-shortage-kpi--critical"
              title={texts.kpiFirst}
              icon={<CalendarClock size={20} strokeWidth={1.75} />}
              value={
                data.summary.first_shortage_date
                  ? formatIsoDate(data.summary.first_shortage_date)
                  : "—"
              }
            />
            <article className="ppc-board-card ppc-pa-shortage-availability" aria-label={texts.kpiAvailability}>
              <p>{texts.availabilityCount(availability.ok, availability.total)}</p>
              <div
                className="ppc-pa-shortage-availability__bar"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={availability.percent}
              >
                <span style={{ width: `${availability.percent}%` }} />
              </div>
              <strong>{texts.availabilityPercent(availability.percent)}</strong>
            </article>
          </div>

          <ul className="ppc-pa-shortage__sets">
            {visibleSets.map((set) => (
              <SetCard
                key={set.production_order}
                branch={branch}
                set={set}
                initialTab={status}
                onOpenMaterial={(material) =>
                  setSelected({ material, motherOrder: set.production_order })
                }
              />
            ))}
          </ul>
        </>
      ) : null}

      <FinishedProductShortageLedgerModal
        material={selected?.material ?? null}
        motherOrder={selected?.motherOrder ?? ""}
        ledger={ledger}
        onClose={() => setSelected(null)}
      />
    </section>
  );
}

function SetCard({
  branch,
  set,
  initialTab,
  onOpenMaterial,
}: {
  branch: PpcBranch;
  set: FinishedProductShortageSet;
  initialTab: MaterialsSetStatus;
  onOpenMaterial: (material: FinishedProductShortageMaterial) => void;
}) {
  const texts = copy.materials.paShortage;
  const badge = setBadge(set.status);
  const counts = countSetMaterialsByStatus(set.materials);
  const [tab, setTab] = useState<MaterialsSetStatus>(
    initialTab === "all" ? "all" : asMaterialsSetStatus(initialTab),
  );
  const rows = filterSetMaterials(set.materials, tab);
  const firstExtract =
    filterSetMaterials(set.materials, "shortage")[0] ?? set.materials[0];
  const tabs: Array<{ id: MaterialsSetStatus; label: string; count: number }> = [
    { id: "all", label: texts.chipAll, count: counts.all },
    { id: "shortage", label: texts.chipShortage, count: counts.shortage },
    { id: "no_commitment", label: texts.chipNoCommitment, count: counts.no_commitment },
    { id: "ok", label: texts.chipOk, count: counts.ok },
  ];

  return (
    <li className="ppc-pa-shortage-set" data-status={set.status}>
      <header className="ppc-pa-shortage-set__head">
        <div className="ppc-pa-shortage-set__identity">
          <strong>
            {texts.opPrefix} {set.production_order}
          </strong>
          <StatusBadge label={badge.label} variant={badge.variant} />
        </div>
        <dl className="ppc-pa-shortage-set__meta">
          <div>
            <dt>{texts.start}</dt>
            <dd>{formatIsoDate(set.planned_start_date)}</dd>
          </div>
          {set.due_date ? (
            <div>
              <dt>{texts.delivery}</dt>
              <dd>{formatIsoDate(set.due_date)}</dd>
            </div>
          ) : null}
          <div>
            <dt>{texts.statusRisk}</dt>
            <dd data-status={set.status}>
              <span className="ppc-pa-shortage-set__risk-dot" aria-hidden="true" />
              {badge.label}
            </dd>
          </div>
        </dl>
      </header>

      <div className="ppc-pa-shortage-set__tabs" role="tablist" aria-label={texts.chipsAria}>
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            className="ppc-pa-shortage-set__tab"
            data-status={item.id}
            data-active={tab === item.id ? "true" : undefined}
            onClick={() => setTab(item.id)}
          >
            <span className="ppc-pa-shortage-set__tab-dot" aria-hidden="true" />
            {item.label} {item.count}
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="ppc-state">{texts.emptyTab}</p>
      ) : (
        <div className="ppc-pa-shortage-table-wrap">
          <table className="ppc-pa-shortage-table">
            <thead>
              <tr>
                <th>{texts.columns.code}</th>
                <th>{texts.columns.material}</th>
                <th>{texts.columns.needed}</th>
                <th>{texts.columns.available}</th>
                <th>{texts.columns.deficit}</th>
                <th>{texts.columns.rupture}</th>
                <th>{texts.columns.status}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((material) => (
                <tr
                  key={material.product_code}
                  data-status={material.status}
                  onClick={() => onOpenMaterial(material)}
                >
                  <td className="ppc-pa-shortage-table__code">{material.product_code}</td>
                  <td>
                    <span className="ppc-pa-shortage-table__name">
                      {material.product_description || "—"}
                    </span>
                  </td>
                  <td>{formatQty(material.needed_quantity, material.unit)}</td>
                  <td>{formatQty(material.available_stock, material.unit)}</td>
                  <td className="ppc-pa-shortage-table__deficit">
                    {material.status === "shortage"
                      ? formatQty(material.shortage_quantity, material.unit)
                      : "—"}
                  </td>
                  <td>
                    {material.status === "shortage" ? formatIsoDate(material.shortage_date) : "—"}
                  </td>
                  <td>
                    <span className={`ppc-pill ppc-pill--${material.status === "shortage" ? "critical" : material.status === "ok" ? "ok" : "attention"}`}>
                      {materialStatusLabel(material.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="ppc-pa-shortage-set__actions">
        <button
          type="button"
          onClick={() => {
            if (firstExtract) onOpenMaterial(firstExtract);
          }}
          disabled={!firstExtract}
        >
          {texts.openExtract}
        </button>
        <button
          type="button"
          onClick={() => navigatePpc(machineLoadLocateHref(branch, set.production_order))}
        >
          {texts.machineLoad}
        </button>
        <button
          type="button"
          onClick={() => navigatePpc(deliveryMapOrderHref(branch, set.production_order))}
        >
          {texts.deliveryMap}
        </button>
        {set.materials[0] ? (
          <a href={safetyStockHref(set.materials[0].product_code)}>{texts.safetyStock}</a>
        ) : null}
      </div>
    </li>
  );
}
