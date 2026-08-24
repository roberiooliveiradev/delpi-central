import { createDashboardLoadingActivityCard, ExcelExportButton } from "@delpi/plugin-ui/index";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DeliveryMapOpProgressBar } from "../components/DeliveryMapOpProgressBar";
import { DeliveryMapPublicLinkButton } from "../components/DeliveryMapPublicLinkButton";
import { usePpcConfirm } from "../components/PpcConfirmDialogProvider";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { buildDeliveryMapExportFileName } from "../utils/deliveryMapExportFileName";
import { helpTooltips } from "../content/helpTooltips";
import { useDeliveryMap, useDeliveryMapOverrideSaver } from "../hooks/useDeliveryMap";
import {
  deliveryMapProgressAriaLabel,
  useDeliveryMapProgress,
} from "../hooks/useDeliveryMapProgress";
import type { DeliveryMapRow, DeliveryMapOpProgress, PpcBranch } from "../types";
import { formatIsoDayMonth } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";
import { downloadDeliveryMapExcel } from "../utils/deliveryMapExcel";
import { isDeliveryMapRowReported } from "../utils/deliveryMapRowReported";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.deliveryMap.loading,
  },
});

type DeliveryMapPageProps = {
  branch: PpcBranch;
  search: string | null;
};

function syncSearchUrl(branch: PpcBranch, nextSearch: string) {
  navigatePpc(
    buildPpcHref({
      subpluginId: "delivery-map",
      branch,
      deliveryMapSearch: nextSearch || null,
    }),
  );
}

function rowClassName(
  row: DeliveryMapRow,
  progressByOrder: Record<string, DeliveryMapOpProgress>,
): string {
  const parts = ["ppc-delivery-map__row"];
  if (row.mp_ok) parts.push("ppc-delivery-map__row--mp-ok");
  if (isDeliveryMapRowReported(progressByOrder[row.production_order])) {
    parts.push("ppc-delivery-map__row--reported");
  }
  return parts.join(" ");
}

export function DeliveryMapPage({ branch, search }: DeliveryMapPageProps) {
  const confirm = usePpcConfirm();
  const [searchDraft, setSearchDraft] = useState(search ?? "");
  const activeSearch = search ?? "";
  const { data, loading, refreshing, saving, error, refreshFromTotvs, saveOverrides, applyPayload } =
    useDeliveryMap(branch, activeSearch);
  const { queue: queueOverride } = useDeliveryMapOverrideSaver(saveOverrides);
  const progressByOrder = useDeliveryMapProgress(branch, data);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);

  const dm = copy.deliveryMap;

  useEffect(() => {
    setSearchDraft(activeSearch);
  }, [activeSearch]);

  const toggleSection = useCallback((key: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const handleRefresh = useCallback(async () => {
    const accepted = await confirm({
      title: dm.refreshConfirmTitle,
      message: dm.refreshConfirmBody,
      confirmLabel: dm.refreshConfirmAction,
    });
    if (!accepted) return;
    await refreshFromTotvs();
  }, [confirm, dm.refreshConfirmAction, dm.refreshConfirmBody, dm.refreshConfirmTitle, refreshFromTotvs]);

  const periodLabel = useMemo(() => {
    if (!data?.snapshot.refreshed_at) return null;
    return dm.frozenAt(formatRefreshedAt(data.snapshot.refreshed_at));
  }, [data?.snapshot.refreshed_at, dm]);

  const stats = useMemo(() => {
    if (!data) return null;
    return <span className="ppc-header__stat">{dm.orderCount(data.summary.order_count)}</span>;
  }, [data, dm]);

  const handleExportExcel = useCallback(async () => {
    if (!data) return;
    setExporting(true);
    try {
      await downloadDeliveryMapExcel(data, buildDeliveryMapExportFileName(branch), progressByOrder);
    } finally {
      setExporting(false);
    }
  }, [branch, data, dm, progressByOrder]);

  const patchRowLocally = useCallback(
    (
      productionOrder: string,
      patch: Partial<Pick<DeliveryMapRow, "mp_ok" | "work_center">>,
    ) => {
      applyPayload((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          sections: prev.sections.map((section) => ({
            ...section,
            rows: section.rows.map((row) =>
              row.production_order === productionOrder ? { ...row, ...patch } : row,
            ),
          })),
        };
      });
    },
    [applyPayload],
  );

  const handleMpOkChange = useCallback(
    (row: DeliveryMapRow, checked: boolean) => {
      patchRowLocally(row.production_order, { mp_ok: checked });
      queueOverride({ production_order: row.production_order, mp_ok: checked });
    },
    [patchRowLocally, queueOverride],
  );

  const handleFeedbackChange = useCallback(
    (row: DeliveryMapRow, value: string) => {
      patchRowLocally(row.production_order, { work_center: value });
      queueOverride({ production_order: row.production_order, work_center: value });
    },
    [patchRowLocally, queueOverride],
  );

  return (
    <div className="ppc-page-stack ppc-page-stack--delivery-map">
      <PpcWorkspaceHeader
        title={dm.title}
        subtitle={dm.subtitle}
        period={periodLabel}
        titleHint={helpTooltips.deliveryMap}
        stats={stats}
        branch={branch}
        subpluginId="delivery-map"
        onRefresh={handleRefresh}
        refreshBusy={refreshing}
      />

      <div className="ppc-delivery-map__toolbar">
        <DeliveryMapPublicLinkButton branch={branch} search={activeSearch} />
        <label className="ppc-delivery-map__search">
          <span className="ppc-sr-only">{dm.searchAria}</span>
          <input
            type="search"
            value={searchDraft}
            placeholder={dm.searchPlaceholder}
            onChange={(event) => setSearchDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                syncSearchUrl(branch, searchDraft.trim());
              }
            }}
          />
        </label>
        <button
          type="button"
          className="ppc-btn ppc-btn--secondary"
          onClick={() => syncSearchUrl(branch, searchDraft.trim())}
        >
          {dm.searchAction}
        </button>
        <ExcelExportButton
          className="ppc-delivery-map__export"
          buttonClassName="ppc-btn ppc-btn--secondary"
          label={dm.exportLabel}
          onExport={handleExportExcel}
          disabled={!data || data.summary.order_count === 0}
          exporting={exporting}
        />
      </div>

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {loading && !data ? <LoadingCard title={dm.loading} description={dm.loadingHint} /> : null}

      {data ? (
        <div className="ppc-delivery-map" aria-busy={refreshing}>
          {data.sections.length === 0 ? (
            <p className="ppc-delivery-map__empty">{dm.empty}</p>
          ) : (
            data.sections.map((section) => {
              const isCollapsed = collapsed.has(section.section_key);
              return (
                <section key={section.section_key} className="ppc-delivery-map__section">
                  <button
                    type="button"
                    className="ppc-delivery-map__section-head"
                    aria-expanded={!isCollapsed}
                    onClick={() => toggleSection(section.section_key)}
                  >
                    {isCollapsed ? (
                      <ChevronRight size={16} aria-hidden />
                    ) : (
                      <ChevronDown size={16} aria-hidden />
                    )}
                    <span className="ppc-delivery-map__section-title">{section.label}</span>
                    <span className="ppc-delivery-map__section-count">
                      {dm.sectionCount(section.row_count)}
                    </span>
                  </button>

                  {!isCollapsed ? (
                    <div className="ppc-delivery-map__table-wrap">
                      <table className="ppc-delivery-map__table">
                        <thead>
                          <tr>
                            {dm.columns.map((column) => (
                              <th key={column.key} scope="col">
                                {column.label}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {section.rows.map((row) => (
                            <tr
                              key={row.production_order}
                              className={rowClassName(row, progressByOrder)}
                            >
                              <td className="ppc-delivery-map__cell-op">
                                <span className="ppc-delivery-map__op-line">
                                  <span className="ppc-delivery-map__op-code">{row.production_order}</span>
                                  <DeliveryMapOpProgressBar
                                    progress={progressByOrder[row.production_order]}
                                    ariaLabel={deliveryMapProgressAriaLabel}
                                  />
                                </span>
                              </td>
                              <td>{row.product_code}</td>
                              <td
                                className={
                                  row.is_delayed ? "ppc-delivery-map__cell-due--late" : undefined
                                }
                              >
                                {row.due_date ? formatIsoDayMonth(row.due_date) : "—"}
                              </td>
                              <td className="ppc-delivery-map__cell-num">
                                {formatOpQuantity(row.planned_qty)}
                              </td>
                              <td className="ppc-delivery-map__cell-num">
                                {formatOpQuantity(row.pending_qty)}
                              </td>
                              <td className="ppc-delivery-map__cell-mp">
                                <input
                                  type="checkbox"
                                  checked={row.mp_ok}
                                  disabled={saving}
                                  aria-label={dm.mpOkAria(row.production_order)}
                                  onChange={(event) => handleMpOkChange(row, event.target.checked)}
                                />
                              </td>
                              <td className="ppc-delivery-map__cell-ct">
                                <input
                                  type="text"
                                  className="ppc-delivery-map__ct-input"
                                  value={row.work_center}
                                  placeholder=""
                                  disabled={saving}
                                  aria-label={dm.feedbackAria(row.production_order)}
                                  onChange={(event) => handleFeedbackChange(row, event.target.value)}
                                />
                              </td>
                              <td className="ppc-delivery-map__cell-obs">
                                {row.observation ?? "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </section>
              );
            })
          )}
        </div>
      ) : null}
    </div>
  );
}
