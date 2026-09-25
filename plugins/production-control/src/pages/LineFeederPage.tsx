import {
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  createDashboardStatusBadge,
} from "@delpi/plugin-ui/index";
import { AlertTriangle, ClipboardList, PackageCheck, Truck } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DataTableSection } from "../components/dataTableUi";
import {
  closeLineFeederPickPlan,
  createLineFeederPickPlan,
  fetchLineFeederPickPlan,
  fetchLineFeederPickPlans,
  fetchLineFeederProductDetail,
  patchLineFeederPickItem,
} from "../api/ppcApi";
import { LineFeederPickPlanPanel } from "../components/LineFeederPickPlanPanel";
import { LineFeederProductDetailModal } from "../components/LineFeederProductDetailModal";
import { LineFeederRequirementCard } from "../components/LineFeederRequirementCard";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { defaultLineFeederFilters, useLineFeeder } from "../hooks/useLineFeeder";
import type {
  LineFeederItemStatus,
  LineFeederPickItem,
  LineFeederPickPlan,
  LineFeederProductDetail,
  LineFeederRequirement,
  LineFeederStatusMeta,
  PpcBranch,
} from "../types";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import {
  formatScheduleTime,
  requirementBadgeVariant,
} from "../utils/lineFeederStatus";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const KpiCard = createDashboardKpiCard({ prefix: "ppc", labels: copy.kpi });
const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.lineFeeder.loading,
  },
});

type LineFeederPageProps = {
  branch: PpcBranch;
  cutoffDate: string | null;
  cutoffTime: string | null;
  workCenter: string | null;
  status: string | null;
  planId: string | null;
};

function optionalQty(value: number | null): string {
  return value === null ? "—" : formatOpQuantity(value);
}

export function LineFeederPage({
  branch,
  cutoffDate,
  cutoffTime,
  workCenter,
  status,
  planId,
}: LineFeederPageProps) {
  const texts = copy.lineFeeder;
  const defaults = useMemo(() => defaultLineFeederFilters(), []);
  const [filters, setFilters] = useState({
    cutoffDate: cutoffDate ?? defaults.cutoffDate,
    cutoffTime: cutoffTime ?? defaults.cutoffTime,
    workCenter: workCenter ?? "",
    status: status ?? "",
  });
  const { data, loading, refreshing, error, reload } = useLineFeeder(branch, filters);

  const [plans, setPlans] = useState<LineFeederPickPlan[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(planId);
  const [planItems, setPlanItems] = useState<LineFeederPickItem[]>([]);
  const [planItemStatuses, setPlanItemStatuses] = useState<
    Record<string, LineFeederStatusMeta>
  >({});
  const [creating, setCreating] = useState(false);
  const [closing, setClosing] = useState(false);
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);
  const [selectedProductCode, setSelectedProductCode] = useState<string | null>(null);
  const [productDetail, setProductDetail] = useState<LineFeederProductDetail | null>(null);
  const [productDetailLoading, setProductDetailLoading] = useState(false);
  const [productDetailError, setProductDetailError] = useState<string | null>(null);

  // A URL é a fonte de verdade do recorte: F5 e link compartilhado abrem igual.
  useEffect(() => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "line-feeder",
        branch,
        cutoffDate: filters.cutoffDate || null,
        cutoffTime: filters.cutoffTime || null,
        workCenter: filters.workCenter || null,
        lineFeederStatus: filters.status || null,
        planId: selectedPlanId,
      }),
    );
  }, [branch, filters, selectedPlanId]);

  const loadPlans = useCallback(async () => {
    try {
      const payload = await fetchLineFeederPickPlans({ branch });
      setPlans(payload.items);
      setPlanItemStatuses(payload.item_statuses ?? {});
      setSelectedPlanId((current) => {
        if (current && payload.items.some((plan) => plan.id === current)) return current;
        return payload.items[0]?.id ?? null;
      });
    } catch (err: unknown) {
      setPlanError(err instanceof Error ? err.message : texts.pickPlan.loadError);
    }
  }, [branch, texts.pickPlan.loadError]);

  useEffect(() => {
    setPlans([]);
    setPlanItems([]);
    void loadPlans();
  }, [loadPlans]);

  useEffect(() => {
    if (!selectedPlanId) {
      setPlanItems([]);
      return;
    }
    const controller = new AbortController();
    fetchLineFeederPickPlan({ branch, planId: selectedPlanId, signal: controller.signal })
      .then((payload) => {
        setPlanItems(payload.items);
        setPlanItemStatuses(payload.item_statuses ?? {});
        setPlans((current) =>
          current.map((plan) => (plan.id === payload.plan.id ? payload.plan : plan)),
        );
        setPlanError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setPlanError(err instanceof Error ? err.message : texts.pickPlan.loadError);
      });
    return () => controller.abort();
  }, [branch, selectedPlanId, texts.pickPlan.loadError]);

  useEffect(() => {
    if (!selectedProductCode || !filters.cutoffDate) {
      setProductDetail(null);
      setProductDetailError(null);
      setProductDetailLoading(false);
      return;
    }
    const controller = new AbortController();
    setProductDetailLoading(true);
    setProductDetailError(null);
    fetchLineFeederProductDetail({
      branch,
      productCode: selectedProductCode,
      cutoffDate: filters.cutoffDate,
      cutoffTime: filters.cutoffTime,
      signal: controller.signal,
    })
      .then((payload) => {
        setProductDetail(payload);
        setProductDetailLoading(false);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setProductDetail(null);
        setProductDetailError(err instanceof Error ? err.message : texts.detail.loadError);
        setProductDetailLoading(false);
      });
    return () => controller.abort();
  }, [branch, filters.cutoffDate, filters.cutoffTime, selectedProductCode, texts.detail.loadError]);

  const handleCreatePlan = async () => {
    setCreating(true);
    setPlanError(null);
    try {
      const payload = await createLineFeederPickPlan({
        branch,
        cutoffDate: filters.cutoffDate,
        cutoffTime: filters.cutoffTime || null,
        workCenter: filters.workCenter || null,
      });
      setPlans((current) => [payload.plan, ...current]);
      setPlanItems(payload.items);
      setPlanItemStatuses(payload.item_statuses ?? {});
      setSelectedPlanId(payload.plan.id);
    } catch (err: unknown) {
      setPlanError(err instanceof Error ? err.message : texts.pickPlan.createError);
    } finally {
      setCreating(false);
    }
  };

  const handleItemStatusChange = async (
    item: LineFeederPickItem,
    nextStatus: LineFeederItemStatus,
  ) => {
    if (!selectedPlanId) return;
    setBusyItemId(item.id);
    setPlanError(null);
    try {
      const payload = await patchLineFeederPickItem({
        branch,
        planId: selectedPlanId,
        itemId: item.id,
        status: nextStatus,
      });
      setPlanItems((current) =>
        current.map((row) => (row.id === payload.item.id ? payload.item : row)),
      );
      setPlans((current) =>
        current.map((plan) =>
          plan.id === selectedPlanId
            ? {
                ...plan,
                delivered_count:
                  plan.delivered_count +
                  (nextStatus === "delivered" ? 1 : 0) -
                  (item.status === "delivered" ? 1 : 0),
              }
            : plan,
        ),
      );
    } catch (err: unknown) {
      setPlanError(err instanceof Error ? err.message : texts.pickPlan.updateError);
    } finally {
      setBusyItemId(null);
    }
  };

  const handleClosePlan = async (id: string) => {
    setClosing(true);
    setPlanError(null);
    try {
      const payload = await closeLineFeederPickPlan({ branch, planId: id });
      setPlans((current) =>
        current.map((plan) => (plan.id === payload.plan.id ? payload.plan : plan)),
      );
    } catch (err: unknown) {
      setPlanError(err instanceof Error ? err.message : texts.pickPlan.closeError);
    } finally {
      setClosing(false);
    }
  };

  const statuses = data?.statuses ?? {};
  const rows = data?.items ?? [];
  const selectedPlan = plans.find((plan) => plan.id === selectedPlanId) ?? null;

  const columns = [
    {
      key: "inventory_blocked",
      header: texts.columns.inventoryBlock,
      align: "center" as const,
      className: "ppc-feeder__inv-col",
      render: (row: LineFeederRequirement) => {
        const blocked = Boolean(row.inventory_blocked);
        return (
          <span
            className={
              blocked
                ? "ppc-feeder__inv-dot ppc-feeder__inv-dot--blocked"
                : "ppc-feeder__inv-dot ppc-feeder__inv-dot--ok"
            }
            title={blocked ? texts.inventoryBlocked : texts.inventoryFree}
            aria-label={blocked ? texts.inventoryBlocked : texts.inventoryFree}
          />
        );
      },
    },
    {
      key: "work_center",
      header: texts.columns.workCenter,
      render: (row: LineFeederRequirement) => row.work_center,
    },
    {
      key: "product_code",
      header: texts.columns.product,
      render: (row: LineFeederRequirement) => (
        <span className="ppc-feeder__product">
          <span className="ppc-feeder__product-code">{row.product_code}</span>
          {row.description ? (
            <span className="ppc-feeder__product-name">{row.description}</span>
          ) : null}
        </span>
      ),
    },
    {
      key: "pickup_location",
      header: texts.columns.pickupLocation,
      render: (row: LineFeederRequirement) =>
        row.pickup_location?.trim()
          ? row.pickup_location
          : copy.lineFeeder.pickPlan.pickupLocationEmpty,
    },
    {
      key: "to_deliver_qty",
      header: texts.columns.toDeliver,
      align: "right" as const,
      render: (row: LineFeederRequirement) => optionalQty(row.to_deliver_qty),
    },
    {
      key: "status",
      header: texts.columns.status,
      render: (row: LineFeederRequirement) => (
        <StatusBadge
          label={statuses[row.status]?.label ?? row.status}
          variant={requirementBadgeVariant(row.status)}
        />
      ),
    },
    {
      key: "first_scheduled_at",
      header: texts.columns.firstScheduled,
      render: (row: LineFeederRequirement) => formatScheduleTime(row.first_scheduled_at),
    },
  ];

  return (
    <div className="ppc-page-stack ppc-page-stack--demand">
      <PpcWorkspaceHeader
        title={texts.title}
        subtitle={texts.subtitle}
        titleHint={helpTooltips.lineFeeder}
        branch={branch}
        subpluginId="line-feeder"
        cutoffDate={filters.cutoffDate || null}
        cutoffTime={filters.cutoffTime || null}
        workCenter={filters.workCenter || null}
        lineFeederStatus={filters.status || null}
        planId={selectedPlanId}
        onRefresh={reload}
        refreshBusy={refreshing}
      />

      <div className="ppc-filters ppc-feeder__filters">
        <fieldset className="ppc-feeder__cutoff">
          <legend className="ppc-field__label">{texts.cutoffLegend}</legend>
          <label className="ppc-field">
            <span className="ppc-field__label">{texts.cutoffDate}</span>
            <input
              type="date"
              value={filters.cutoffDate}
              onChange={(event) =>
                setFilters((current) => ({ ...current, cutoffDate: event.target.value }))
              }
            />
          </label>
          <label className="ppc-field">
            <span className="ppc-field__label">{texts.cutoffTime}</span>
            <input
              type="time"
              value={filters.cutoffTime}
              onChange={(event) =>
                setFilters((current) => ({ ...current, cutoffTime: event.target.value }))
              }
            />
          </label>
          <p className="ppc-feeder__cutoff-hint">{texts.cutoffHint}</p>
        </fieldset>

        <label className="ppc-field">
          <span className="ppc-field__label">{texts.workCenterLabel}</span>
          <select
            value={filters.workCenter}
            onChange={(event) =>
              setFilters((current) => ({ ...current, workCenter: event.target.value }))
            }
          >
            <option value="">{texts.workCenterAll}</option>
            {(data?.work_centers ?? []).map((center) => (
              <option key={center.work_center} value={center.work_center}>
                {center.work_center_name
                  ? `${center.work_center} · ${center.work_center_name}`
                  : center.work_center}
              </option>
            ))}
          </select>
        </label>

        <label className="ppc-field">
          <span className="ppc-field__label">{texts.statusLabel}</span>
          <select
            value={filters.status}
            onChange={(event) =>
              setFilters((current) => ({ ...current, status: event.target.value }))
            }
          >
            <option value="">{texts.statusAll}</option>
            {Object.entries(statuses).map(([key, meta]) => (
              <option key={key} value={key}>
                {meta.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="ppc-icon-btn ppc-feeder__create"
          onClick={handleCreatePlan}
          disabled={creating || loading || !data || data.summary.to_deliver_qty <= 0}
          title={texts.pickPlan.createHint}
        >
          <ClipboardList size={16} strokeWidth={1.75} aria-hidden />
          <span>{creating ? texts.pickPlan.creating : texts.pickPlan.create}</span>
        </button>
      </div>

      {loading ? <LoadingCard title={texts.loading} description={texts.loadingHint} /> : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || texts.loadError}
        </div>
      ) : null}

      {data ? (
        <div className="ppc-board">
          {!data.stock.available ? (
            <div className="ppc-state ppc-state--error" role="status">
              {data.stock.message ?? texts.stockUnavailable}
            </div>
          ) : null}
          {data.stock.truncated_orders ? (
            <div className="ppc-state" role="status">
              {texts.truncatedOrders}
            </div>
          ) : null}

          <div className="ppc-demand-kpi-grid">
            <KpiCard
              className="ppc-board-card"
              title={texts.kpiToDeliver}
              titleHint={texts.kpiToDeliverHint}
              value={String(data.summary.to_pick_count + data.summary.at_risk_count)}
              subtitle={formatOpQuantity(data.summary.to_deliver_qty)}
              icon={<Truck size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              className="ppc-board-card"
              title={texts.kpiCovered}
              titleHint={texts.kpiCoveredHint}
              value={String(data.summary.covered_count)}
              icon={<PackageCheck size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              className="ppc-board-card ppc-pa-shortage-kpi--critical"
              title={texts.kpiAtRisk}
              titleHint={texts.kpiAtRiskHint}
              value={String(data.summary.at_risk_count)}
              icon={<AlertTriangle size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              className="ppc-board-card"
              title={texts.kpiOperations}
              titleHint={texts.kpiOperationsHint}
              value={String(data.summary.operation_count ?? 0)}
              subtitle={data.cutoff.time}
              icon={<ClipboardList size={22} strokeWidth={1.75} />}
            />
          </div>

          <DataTableSection<LineFeederRequirement>
            title={texts.tableTitle}
            columns={columns}
            rows={rows}
            rowKey={(row) => `${row.work_center}|${row.product_code}`}
            loading={loading}
            refreshing={refreshing}
            emptyMessage={texts.empty}
            searchPlaceholder={texts.searchPlaceholder}
            columnPreferencesKey="production-control:line-feeder:columns:v5"
            viewLayoutPreferencesKey="production-control:line-feeder:layout:v1"
            viewLayoutMobileMaxWidthPx={1280}
            renderCard={(row) => (
              <LineFeederRequirementCard
                row={row}
                statuses={statuses}
                onOpen={(item) => setSelectedProductCode(item.product_code)}
              />
            )}
            onRowClick={(row) => setSelectedProductCode(row.product_code)}
          />

          <LineFeederPickPlanPanel
            plans={plans}
            selected={selectedPlan}
            items={planItems}
            itemStatuses={planItemStatuses}
            busyItemId={busyItemId}
            closing={closing}
            error={planError}
            onSelect={setSelectedPlanId}
            onItemStatusChange={handleItemStatusChange}
            onClose={handleClosePlan}
          />
        </div>
      ) : null}

      <LineFeederProductDetailModal
        open={Boolean(selectedProductCode)}
        loading={productDetailLoading}
        error={productDetailError}
        detail={productDetail}
        statuses={data?.statuses ?? {}}
        onClose={() => {
          setSelectedProductCode(null);
          setProductDetail(null);
          setProductDetailError(null);
        }}
      />
    </div>
  );
}
