import {
  createDashboardKpiCard,
  createDashboardStatusBadge,
} from "@delpi/plugin-ui/index";
import { AlertTriangle, Clock3, PackageCheck, PackageSearch } from "lucide-react";
import { useMemo, useState } from "react";

import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { copy } from "../content/copy";
import type {
  LineFeederCollectQuery,
} from "../hooks/useLineFeederMaterialsPreview";
import type {
  LineFeederMaterialItem,
  LineFeederMaterialsPreviewPayload,
} from "../types";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import {
  matchesMaterialsFilter,
  materialBadgeVariant,
  materialStatusLabel,
  type MaterialsListFilter,
} from "../utils/lineFeederMaterialsStatus";

const KpiCard = createDashboardKpiCard({ prefix: "ppc", labels: copy.kpi });
const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

type Props = {
  data: LineFeederMaterialsPreviewPayload;
  query: LineFeederCollectQuery;
};

function qty(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined) return "—";
  return `${formatOpQuantity(value)} ${unit}`.trim();
}

/** Primeiro posto que demanda o material na prévia (só o código). */
function firstWorkCenterCode(workCenters: string[] | undefined): string {
  const code = workCenters?.find((item) => item.trim())?.trim();
  return code ?? "";
}

function hasOrderLevelOrigin(item: LineFeederMaterialItem): boolean {
  return (item.origins ?? []).some((origin) =>
    origin.operation_id.startsWith("order-level:"),
  );
}

function materialWorkCenterLabel(item: LineFeederMaterialItem): string {
  const first = firstWorkCenterCode(item.work_centers);
  if (hasOrderLevelOrigin(item)) {
    return first ? `${first} + sem CT` : copy.lineFeeder.orderLevelWorkCenter;
  }
  return first || copy.lineFeeder.firstWorkCenterEmpty;
}

export function LineFeederMaterialsPanel({ data, query }: Props) {
  const texts = copy.lineFeeder;
  const [filter, setFilter] = useState<MaterialsListFilter>("to_collect");
  const [expanded, setExpanded] = useState<string | null>(null);

  const safe = data.operational_list_safe === true;
  const materials = data.materials ?? [];

  const filtered = useMemo(() => {
    const rows = materials.filter((row) => matchesMaterialsFilter(row.status, filter));
    return [...rows].sort((a, b) => {
      const aCollect = a.to_collect_qty ?? -1;
      const bCollect = b.to_collect_qty ?? -1;
      if (bCollect !== aCollect) return bCollect - aCollect;
      return a.product_code.localeCompare(b.product_code);
    });
  }, [materials, filter]);

  const toCollectCodes =
    data.summary.to_pick_count + data.summary.at_risk_count + data.summary.unknown_count;

  const columns: DataTableColumn<LineFeederMaterialItem>[] = [
    {
      key: "product_code",
      header: texts.columns.product,
      render: (row) => (
        <span className="ppc-feeder__product">
          <span className="ppc-feeder__product-code">{row.product_code}</span>
          {row.description ? (
            <span className="ppc-feeder__product-name">{row.description}</span>
          ) : null}
        </span>
      ),
    },
    {
      key: "work_center",
      header: texts.columns.workCenter,
      render: (row) => materialWorkCenterLabel(row),
    },
    {
      key: "unit",
      header: texts.columns.unit,
      render: (row) => row.unit || "—",
    },
    {
      key: "required_qty",
      header: texts.columns.required,
      align: "right",
      render: (row) => qty(row.required_qty, row.unit),
    },
    {
      key: "factory_available_qty",
      header: texts.columns.factory,
      align: "right",
      render: (row) => qty(row.factory_available_qty, row.unit),
    },
    {
      key: "to_collect_qty",
      header: texts.columns.toCollect,
      align: "right",
      render: (row) => (
        <span className="ppc-feeder-materials__collect">
          {qty(row.to_collect_qty, row.unit)}
        </span>
      ),
    },
    {
      key: "source_available_qty",
      header: texts.columns.source,
      align: "right",
      render: (row) => qty(row.source_available_qty, row.unit),
    },
    {
      key: "pickup_location",
      header: texts.columns.pickupLocation,
      render: (row) =>
        row.pickup_location?.trim()
          ? row.pickup_location
          : texts.pickupLocationEmpty,
    },
    {
      key: "status",
      header: texts.columns.status,
      render: (row) => (
        <StatusBadge
          label={materialStatusLabel(row.status)}
          variant={materialBadgeVariant(row.status)}
        />
      ),
    },
  ];

  if (!safe) {
    const diagnostics = data.diagnostics ?? [];
    const horizonMessages = (data.horizon?.work_centers ?? [])
      .map((center) => center.diagnostic_message?.trim())
      .filter((message): message is string => Boolean(message));
    const hasRichDiag = diagnostics.length > 0 || horizonMessages.length > 0;
    return (
      <div className="ppc-board">
        <div className="ppc-state ppc-state--error" role="alert">
          <strong>{texts.materialsPreview.incompleteTitle}</strong>
          <p>{texts.materialsPreview.incompleteMessage}</p>
          <p>{texts.materialsPreview.unsafeListHidden}</p>
          <p>{texts.materialsPreview.keepSelectionHint}</p>
          {hasRichDiag || data.stop_reasons?.length || data.demand_warnings?.length ? (
            <details className="ppc-feeder-materials__diag" open={hasRichDiag}>
              <summary>{texts.materialsPreview.incompleteDiagnostics}</summary>
              <ul>
                {diagnostics.map((item, index) => (
                  <li key={`${item.work_center}-${item.stop_reason}-${index}`}>
                    {item.message?.trim()
                      ? item.message
                      : texts.materialsPreview.stopReasonFallback(
                          String(item.stop_reason || item.code || "horizon_incomplete"),
                        )}
                  </li>
                ))}
                {!diagnostics.length
                  ? horizonMessages.map((message) => (
                      <li key={message}>{message}</li>
                    ))
                  : null}
                {(data.stop_reasons ?? []).map((reason) => (
                  <li key={`stop-${reason}`}>
                    {texts.materialsPreview.stopReasonFallback(reason)}
                  </li>
                ))}
                {(data.demand_warnings ?? []).map((warning, index) => (
                  <li key={`${warning.code}-${index}`}>
                    {warning.code}
                    {warning.detail ? ` — ${String(warning.detail)}` : ""}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      </div>
    );
  }

  const noMaterials = materials.length === 0;
  const onlyCovered =
    materials.length > 0 &&
    data.summary.to_pick_count === 0 &&
    data.summary.at_risk_count === 0 &&
    data.summary.unknown_count === 0;
  const noCommitments = (data.demand_warnings ?? []).some(
    (warning) => warning.code === "no_commitments",
  );

  return (
    <div className="ppc-board">
      {data.summary.unknown_count > 0 ? (
        <div className="ppc-state ppc-state--error" role="status">
          {texts.stockUnavailable}
        </div>
      ) : null}

      <div className="ppc-demand-kpi-grid">
        <KpiCard
          className="ppc-board-card"
          title={texts.kpiToCollect}
          titleHint={texts.kpiToCollectHint}
          value={String(toCollectCodes)}
          icon={<PackageSearch size={22} strokeWidth={1.75} />}
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
          value={String(data.horizon?.covered_operation_count ?? 0)}
          subtitle={`${query.hoursPerWorkCenter} h / CT`}
          icon={<Clock3 size={22} strokeWidth={1.75} />}
        />
      </div>

      {noMaterials && noCommitments ? (
        <div className="ppc-state" role="status">
          {texts.emptyNoCommitments}
        </div>
      ) : null}

      {onlyCovered ? (
        <div className="ppc-state" role="status">
          {texts.emptyCollect}
        </div>
      ) : null}

      {materials.some(hasOrderLevelOrigin) ? (
        <div className="ppc-state" role="status">
          {texts.orderLevelWarning}
        </div>
      ) : null}

      <div
        className="ppc-feeder-materials__filters"
        role="toolbar"
        aria-label={texts.filterAria}
      >
        {(
          [
            ["to_collect", texts.filterToCollect],
            ["at_risk", texts.filterAtRisk],
            ["all", texts.filterAll],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={
              filter === value
                ? "ppc-feeder-collect__chip ppc-feeder-collect__chip--active"
                : "ppc-feeder-collect__chip"
            }
            aria-pressed={filter === value}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>

      <DataTableSection<LineFeederMaterialItem>
        title={texts.tableTitle}
        columns={columns}
        rows={filtered}
        rowKey={(row) => `${row.product_code}|${row.unit}`}
        loading={false}
        emptyMessage={
          filtered.length === 0 && materials.length > 0
            ? texts.emptyFiltered
            : texts.emptyCollect
        }
        searchPlaceholder={texts.searchPlaceholder}
        columnPreferencesKey="production-control:line-feeder:materials:columns:v2"
        viewLayoutPreferencesKey="production-control:line-feeder:materials:layout:v1"
        viewLayoutMobileMaxWidthPx={1280}
        renderCard={(row) => (
          <article className="ppc-feeder-materials__card">
            <header>
              <strong>{row.product_code}</strong>
              {row.description ? <span>{row.description}</span> : null}
            </header>
            <p className="ppc-feeder-materials__ct">
              {texts.columns.workCenter}:{" "}
              {materialWorkCenterLabel(row)}
            </p>
            <p>
              Necessário: {qty(row.required_qty, row.unit)}
              {" · "}
              Na fábrica: {qty(row.factory_available_qty, row.unit)}
            </p>
            <p className="ppc-feeder-materials__collect">
              Coletar: {qty(row.to_collect_qty, row.unit)}
            </p>
            <StatusBadge
              label={materialStatusLabel(row.status)}
              variant={materialBadgeVariant(row.status)}
            />
          </article>
        )}
        onRowClick={(row) =>
          setExpanded((current) =>
            current === row.product_code ? null : row.product_code,
          )
        }
      />

      {expanded ? (
        <OriginsDetail
          item={materials.find((row) => row.product_code === expanded) ?? null}
          onClose={() => setExpanded(null)}
        />
      ) : null}
    </div>
  );
}

function OriginsDetail({
  item,
  onClose,
}: {
  item: LineFeederMaterialItem | null;
  onClose: () => void;
}) {
  const texts = copy.lineFeeder;
  if (!item) return null;
  return (
    <section className="ppc-feeder-materials__origins" aria-label={texts.originsTitle}>
      <header className="ppc-feeder-materials__origins-head">
        <h3>
          {texts.originsTitle}: {item.product_code}
        </h3>
        <button type="button" className="ppc-icon-btn" onClick={onClose}>
          Fechar
        </button>
      </header>
      {(item.origins ?? []).length === 0 ? (
        <p className="ppc-feeder-collect__hint">{texts.originsEmpty}</p>
      ) : (
        <ul>
          {item.origins.map((origin) => (
            <li key={`${origin.operation_id}-${origin.sequence_position}`}>
              {origin.operation_id.startsWith("order-level:")
                ? `OP ${origin.production_order} · ${texts.orderLevelOrigin}`
                : texts.originRow(
                    origin.work_center,
                    origin.production_order,
                    (origin.pa_product_code ?? "").trim(),
                  )}
              {" — "}
              {qty(origin.required_qty, item.unit)}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
