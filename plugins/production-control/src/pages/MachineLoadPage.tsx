import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createDashboardLoadingActivityCard,
  DataTable,
  dataTableBemClasses,
  UnderlineNav,
  underlineNavBemClasses,
} from "@delpi/plugin-ui/index";
import { GripVertical } from "lucide-react";

import { MachineLoadStatusCell } from "../components/MachineLoadStatusCell";
import { OperatorCockpitLinkButton } from "../components/OperatorCockpitLinkButton";
import { usePpcConfirm } from "../components/PpcConfirmDialogProvider";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { patchMachineLoadSequence } from "../api/ppcApi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useMachineLoad } from "../hooks/useMachineLoad";
import { useMachineLoadRowReorder } from "../hooks/useMachineLoadRowReorder";
import {
  applyKeyOrder,
  keysFromOperations,
  useMachineLoadSequenceHistory,
} from "../hooks/useMachineLoadSequenceHistory";
import type { MachineLoadOperation, MachineLoadPayload, PpcBranch } from "../types";
import { formatIsoDate, formatIsoDayMonth } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";
import { machineLoadRowModifierClass } from "../utils/machineLoadStatus";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const tableClassNames = dataTableBemClasses("ppc");
const navClassNames = underlineNavBemClasses("ppc");

const tableLabels = {
  emptyMessage: copy.machineLoad.emptyOperations,
  loadingMessage: copy.table.loading,
  sortByAriaLabel: copy.table.sort,
  headerHelpAriaLabel: copy.table.help,
};

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.machineLoad.loading,
  },
});

type MachineLoadPageProps = {
  branch: PpcBranch;
  workCenter: string | null;
  startDate: string | null;
  endDate: string | null;
};

export function MachineLoadPage({ branch, workCenter, startDate, endDate }: MachineLoadPageProps) {
  const confirm = usePpcConfirm();
  const { data, loading, refreshing, error, refreshFromTotvs, applyPayload } = useMachineLoad({
    branch,
    workCenter,
    startDate,
    endDate,
  });

  const period = data?.period;
  const [draftStart, setDraftStart] = useState(startDate ?? "");
  const [draftEnd, setDraftEnd] = useState(endDate ?? "");
  const [rows, setRows] = useState<MachineLoadOperation[]>([]);
  const [sequenceBusy, setSequenceBusy] = useState(false);
  const [sequenceNotice, setSequenceNotice] = useState<string | null>(null);

  useEffect(() => {
    setDraftStart(startDate ?? period?.start_date ?? "");
    setDraftEnd(endDate ?? period?.end_date ?? "");
  }, [startDate, endDate, period?.start_date, period?.end_date]);

  const selectedCenter = data?.selected.work_center ?? null;
  const workCenters = data?.work_centers ?? [];

  useEffect(() => {
    setRows(data?.selected.items ?? []);
  }, [data]);

  const scopeKey = [
    branch,
    startDate ?? period?.start_date ?? "",
    endDate ?? period?.end_date ?? "",
    selectedCenter ?? "",
  ].join("|");

  const history = useMachineLoadSequenceHistory(scopeKey);

  const persistOrder = useCallback(
    async (
      nextRows: MachineLoadOperation[],
      options: { previousKeys: ReturnType<typeof keysFromOperations>; pushUndo: boolean },
    ) => {
      if (!selectedCenter) return;
      const orderedKeys = keysFromOperations(nextRows);
      setRows(nextRows);
      setSequenceBusy(true);
      setSequenceNotice(null);
      try {
        const payload = await patchMachineLoadSequence({
          branch,
          workCenter: selectedCenter,
          startDate,
          endDate,
          orderedKeys,
        });
        applyPayload(payload);
        if (options.pushUndo) history.pushUndo(options.previousKeys);
        setSequenceNotice(copy.machineLoad.sequenceSaved);
      } catch (err: unknown) {
        setRows(data?.selected.items ?? []);
        setSequenceNotice(
          err instanceof Error ? err.message : copy.machineLoad.sequenceError,
        );
      } finally {
        setSequenceBusy(false);
      }
    },
    [
      applyPayload,
      branch,
      data?.selected.items,
      endDate,
      history,
      selectedCenter,
      startDate,
    ],
  );

  const onReorder = useCallback(
    (nextRows: MachineLoadOperation[]) => {
      if (sequenceBusy) return;
      void persistOrder(nextRows, {
        previousKeys: keysFromOperations(rows),
        pushUndo: true,
      });
    },
    [persistOrder, rows, sequenceBusy],
  );

  const reorder = useMachineLoadRowReorder(rows, onReorder);

  const applyRemoteKeys = useCallback(
    async (
      keys: ReturnType<typeof keysFromOperations>,
      sideEffects: (currentKeys: ReturnType<typeof keysFromOperations>) => void,
    ) => {
      if (!selectedCenter || sequenceBusy) return;
      const currentKeys = keysFromOperations(rows);
      sideEffects(currentKeys);
      const nextRows = applyKeyOrder(rows, keys);
      setRows(nextRows);
      setSequenceBusy(true);
      setSequenceNotice(null);
      try {
        const payload: MachineLoadPayload = await patchMachineLoadSequence({
          branch,
          workCenter: selectedCenter,
          startDate,
          endDate,
          orderedKeys: keys,
        });
        applyPayload(payload);
        setSequenceNotice(copy.machineLoad.sequenceSaved);
      } catch (err: unknown) {
        setRows(data?.selected.items ?? []);
        setSequenceNotice(
          err instanceof Error ? err.message : copy.machineLoad.sequenceError,
        );
      } finally {
        setSequenceBusy(false);
      }
    },
    [
      applyPayload,
      branch,
      data?.selected.items,
      endDate,
      rows,
      selectedCenter,
      sequenceBusy,
      startDate,
    ],
  );

  useEffect(() => {
    return history.bindKeyboard({
      onUndo: () => {
        if (sequenceBusy) return;
        const restored = history.undo();
        if (!restored) return;
        void applyRemoteKeys(restored, (current) => history.rememberForRedo(current));
      },
      onRedo: () => {
        if (sequenceBusy) return;
        const restored = history.redo();
        if (!restored) return;
        void applyRemoteKeys(restored, (current) => history.rememberForUndoAfterRedo(current));
      },
    });
  }, [applyRemoteKeys, history, sequenceBusy]);

  const columns = useMemo(
    () => [
      {
        key: "drag",
        header: "",
        interactive: true,
        render: (row: MachineLoadOperation) => {
          const rowIndex = rows.findIndex(
            (item) =>
              item.production_order === row.production_order &&
              item.operation_code === row.operation_code,
          );
          return (
            <button
              type="button"
              className="ppc-load__drag-handle"
              aria-label={copy.machineLoad.dragHandle}
              title={copy.machineLoad.dragHandle}
              {...reorder.handleProps(Math.max(0, rowIndex))}
            >
              <GripVertical size={16} strokeWidth={1.75} aria-hidden />
            </button>
          );
        },
      },
      {
        key: "production_status",
        header: copy.machineLoad.columns.status,
        render: (row: MachineLoadOperation) => <MachineLoadStatusCell operation={row} />,
      },
      {
        key: "schedule",
        header: copy.machineLoad.columns.schedule,
        render: (row: MachineLoadOperation) => (
          <span className="ppc-load__schedule">
            <strong>{formatIsoDayMonth(row.scheduled_date)}</strong>
            <span>{row.scheduled_start_time ?? "—"}</span>
          </span>
        ),
      },
      {
        key: "production_order",
        header: copy.machineLoad.columns.productionOrder,
        render: (row: MachineLoadOperation) => row.production_order || "—",
      },
      {
        key: "product",
        header: copy.machineLoad.columns.product,
        render: (row: MachineLoadOperation) => (
          <span className="ppc-load__product">
            <strong>{row.product_description || "—"}</strong>
            <span>{row.product_code || "—"}</span>
          </span>
        ),
      },
      {
        key: "quantity",
        header: copy.machineLoad.columns.quantity,
        align: "right" as const,
        render: (row: MachineLoadOperation) => formatOpQuantity(row.planned_qty),
      },
      {
        key: "tool",
        header: copy.machineLoad.columns.tool,
        render: (row: MachineLoadOperation) =>
          row.is_manual_operation ? copy.machineLoad.manualTool : row.tool || "—",
      },
      {
        key: "operation",
        header: copy.machineLoad.columns.operation,
        render: (row: MachineLoadOperation) => row.operation_description || "—",
      },
      {
        key: "pa_product_code",
        header: copy.machineLoad.columns.paCode,
        render: (row: MachineLoadOperation) => row.pa_product_code || "—",
      },
      {
        key: "pa_due_date",
        header: copy.machineLoad.columns.paDueDate,
        render: (row: MachineLoadOperation) => formatIsoDate(row.pa_due_date),
      },
    ],
    [reorder, rows],
  );

  const goTo = (next: {
    workCenter?: string | null;
    startDate?: string | null;
    endDate?: string | null;
  }) => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "machine-load",
        branch,
        workCenter: next.workCenter !== undefined ? next.workCenter : selectedCenter,
        startDate: next.startDate !== undefined ? next.startDate : startDate,
        endDate: next.endDate !== undefined ? next.endDate : endDate,
      }),
    );
  };

  const onRefreshClick = async () => {
    const accepted = await confirm({
      title: copy.machineLoad.refreshConfirmTitle,
      message: copy.machineLoad.refreshConfirmMessage,
      confirmLabel: copy.machineLoad.refreshConfirmAction,
      cancelLabel: copy.machineLoad.refreshCancel,
      variant: "default",
    });
    if (!accepted) return;
    try {
      await refreshFromTotvs();
    } catch {
      // erro já cai no estado da página
    }
  };

  const tabs = workCenters.map((center) => ({
    id: center.work_center,
    label: center.in_production_count ? (
      <span className="ppc-load__tab-label">
        <span
          className="ppc-load__pulse"
          role="img"
          aria-label={copy.machineLoad.status.inProductionTabAria(
            center.work_center,
            center.in_production_count,
          )}
        />
        {center.work_center}
      </span>
    ) : (
      center.work_center
    ),
    count: center.operation_count,
    title: center.work_center_name
      ? `${center.work_center} — ${center.work_center_name}`
      : center.work_center,
    controlId: "ppc-load-panel",
    tabId: `ppc-load-tab-${center.work_center}`,
    onSelect: () => goTo({ workCenter: center.work_center }),
  }));

  const activeCenter = workCenters.find((center) => center.work_center === selectedCenter);

  return (
    <div className="ppc-page-stack">
      <PpcWorkspaceHeader
        title={copy.machineLoad.title}
        subtitle={copy.machineLoad.subtitle}
        titleHint={helpTooltips.machineLoad}
        branch={branch}
        subpluginId="machine-load"
        workCenter={selectedCenter}
        startDate={startDate}
        endDate={endDate}
        onRefresh={onRefreshClick}
      />

      <form
        className="ppc-period"
        onSubmit={(event) => {
          event.preventDefault();
          goTo({ startDate: draftStart || null, endDate: draftEnd || null });
        }}
      >
        <span className="ppc-period__label">{copy.machineLoad.periodLabel}</span>
        <label className="ppc-period__field">
          <span>{copy.machineLoad.periodFrom}</span>
          <input
            type="date"
            value={draftStart}
            onChange={(event) => setDraftStart(event.target.value)}
          />
        </label>
        <label className="ppc-period__field">
          <span>{copy.machineLoad.periodTo}</span>
          <input
            type="date"
            value={draftEnd}
            onChange={(event) => setDraftEnd(event.target.value)}
          />
        </label>
        <button type="submit" className="ppc-period__apply">
          {copy.machineLoad.periodApply}
        </button>
        {startDate || endDate ? (
          <button
            type="button"
            className="ppc-period__reset"
            onClick={() => goTo({ startDate: null, endDate: null })}
          >
            {copy.machineLoad.periodReset}
          </button>
        ) : null}
        <OperatorCockpitLinkButton branch={branch} />
        {data ? (
          <span className="ppc-period__summary">
            {copy.machineLoad.summary(
              data.summary.work_center_count,
              data.summary.operation_count,
            )}
            {data.summary.in_production_count ? (
              <span className="ppc-period__running">
                <span className="ppc-load__pulse" aria-hidden="true" />
                {copy.machineLoad.inProductionSummary(data.summary.in_production_count)}
              </span>
            ) : null}
            {data.snapshot?.refreshed_at ? (
              <span className="ppc-period__frozen">
                {copy.machineLoad.refreshedAt(formatRefreshedAt(data.snapshot.refreshed_at))}
              </span>
            ) : null}
            {data.snapshot?.sequence_updated_at ? (
              <span className="ppc-period__sequence">
                {copy.machineLoad.sequenceUpdatedAt(
                  formatRefreshedAt(data.snapshot.sequence_updated_at),
                )}
              </span>
            ) : null}
          </span>
        ) : null}
      </form>

      {loading && !data ? (
        <LoadingCard title={copy.machineLoad.loading} description={copy.machineLoad.loadingHint} />
      ) : null}

      {refreshing ? (
        <div className="ppc-state" role="status">
          {copy.machineLoad.refreshBusy}
        </div>
      ) : null}

      {sequenceBusy ? (
        <div className="ppc-state" role="status">
          {copy.machineLoad.sequenceSaving}
        </div>
      ) : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {sequenceNotice && !error && !sequenceBusy ? (
        <div className="ppc-state" role="status">
          {sequenceNotice}
        </div>
      ) : null}

      {data && workCenters.length === 0 && !loading ? (
        <div className="ppc-state">
          <strong>{copy.machineLoad.emptyCenters}</strong>
          <p>{copy.machineLoad.emptyCentersHint}</p>
        </div>
      ) : null}

      {data && workCenters.length > 0 ? (
        <section className="ppc-load">
          <UnderlineNav
            items={tabs}
            activeId={selectedCenter ?? ""}
            mode="tabs"
            classNames={navClassNames}
            aria-label={copy.machineLoad.tabsAria}
          />
          <div
            className="ppc-load__panel"
            id="ppc-load-panel"
            role="tabpanel"
            aria-labelledby={selectedCenter ? `ppc-load-tab-${selectedCenter}` : undefined}
          >
            {activeCenter?.work_center_name ? (
              <p className="ppc-load__center-name">{activeCenter.work_center_name}</p>
            ) : null}
            {rows.length > 1 ? (
              <p className="ppc-load__sequence-hint">{copy.machineLoad.sequenceHint}</p>
            ) : null}
            <DataTable
              columns={columns}
              rows={rows}
              rowKey={(row) => `${row.production_order}-${row.operation_code}`}
              getRowClassName={(row, index) =>
                [machineLoadRowModifierClass(row), reorder.rowClassName(index)]
                  .filter(Boolean)
                  .join(" ") || undefined
              }
              getRowProps={(_row, index) => reorder.rowDropProps(index)}
              emptyMessage={copy.machineLoad.emptyOperations}
              loading={loading}
              classNames={tableClassNames}
              labels={tableLabels}
              layout="section"
            />
          </div>
        </section>
      ) : null}
    </div>
  );
}
