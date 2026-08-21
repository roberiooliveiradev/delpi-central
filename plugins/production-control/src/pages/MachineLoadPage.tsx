import { useCallback, useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import {
  createDashboardLoadingActivityCard,
  DataTable,
  dataTableBemClasses,
  UnderlineNav,
  underlineNavBemClasses,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import { ArrowDownNarrowWide, CalendarOff, Eye, EyeOff, GripVertical } from "lucide-react";

import { MachineLoadLocateModal } from "../components/MachineLoadLocateModal";
import { MachineLoadLocatePanel } from "../components/MachineLoadLocatePanel";
import { MachineLoadRowContextMenu } from "../components/MachineLoadRowContextMenu";
import { MachineLoadStatusCell } from "../components/MachineLoadStatusCell";
import { MachineLoadTransferModal, type MachineLoadTransferMode } from "../components/MachineLoadTransferModal";
import { MachineLoadWithdrawnModal } from "../components/MachineLoadWithdrawnModal";
import { OperatorCockpitLinkButton } from "../components/OperatorCockpitLinkButton";
import { usePpcConfirm } from "../components/PpcConfirmDialogProvider";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import {
  fetchMachineLoadLocate,
  optimizeMachineLoadDeliverySequence,
  patchMachineLoadSequence,
  prioritizeMachineLoadConjunto,
  restoreMachineLoadConjunto,
  transferMachineLoadConjunto,
  transferMachineLoadOperation,
  withdrawMachineLoadConjunto,
} from "../api/ppcApi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useMachineLoad } from "../hooks/useMachineLoad";
import { useMachineLoadRowReorder } from "../hooks/useMachineLoadRowReorder";
import {
  applyKeyOrder,
  keysFromOperations,
  useMachineLoadSequenceHistory,
} from "../hooks/useMachineLoadSequenceHistory";
import type {
  MachineLoadLocatePayload,
  MachineLoadLocateStop,
  MachineLoadOperation,
  MachineLoadPayload,
  PpcBranch,
} from "../types";
import { formatIsoDate, formatIsoDayMonth } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";
import { machineLoadLocateRowKey } from "../utils/machineLoadLocate";
import {
  filterActiveMachineLoadOperations,
  isMachineLoadFinishedOperation,
  machineLoadRowModifierClass,
} from "../utils/machineLoadStatus";
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
  locateQuery?: string | null;
};

const HIGHLIGHT_MS = 3200;

const HIDE_FINISHED_STORAGE_KEY = "ppc-machine-load-hide-finished";

function readHideFinishedPreference(): boolean {
  try {
    return sessionStorage.getItem(HIDE_FINISHED_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function MachineLoadPage({
  branch,
  workCenter,
  startDate,
  endDate,
  locateQuery = null,
}: MachineLoadPageProps) {
  const confirm = usePpcConfirm();
  const { data, loading, switchingCenter, refreshing, error, refreshFromTotvs, applyPayload } =
    useMachineLoad({
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
  const [locateDraft, setLocateDraft] = useState(locateQuery ?? "");
  const [locateLoading, setLocateLoading] = useState(false);
  const [locateError, setLocateError] = useState<string | null>(null);
  const [locateResult, setLocateResult] = useState<MachineLoadLocatePayload | null>(null);
  const [highlightKey, setHighlightKey] = useState<string | null>(null);
  const locateAutoKeyRef = useRef<string | null>(null);
  const [rowMenu, setRowMenu] = useState<{
    operation: MachineLoadOperation;
    position: FixedPanelPoint;
  } | null>(null);
  const [conjuntoModalOpen, setConjuntoModalOpen] = useState(false);
  const [conjuntoModalOrder, setConjuntoModalOrder] = useState<string | null>(null);
  const [conjuntoModalPa, setConjuntoModalPa] = useState<string | null>(null);
  const [conjuntoModalLoading, setConjuntoModalLoading] = useState(false);
  const [conjuntoModalError, setConjuntoModalError] = useState<string | null>(null);
  const [conjuntoModalResult, setConjuntoModalResult] = useState<MachineLoadLocatePayload | null>(null);
  const [withdrawnModalOpen, setWithdrawnModalOpen] = useState(false);
  const [transferOperation, setTransferOperation] = useState<MachineLoadOperation | null>(null);
  const [transferMode, setTransferMode] = useState<MachineLoadTransferMode>("operation");
  const [hideFinished, setHideFinished] = useState(readHideFinishedPreference);

  // Sem recorte na URL, «De» mostra a entrega mais antiga que sobrou na fila.
  useEffect(() => {
    setDraftStart(startDate ?? period?.oldest_due_date ?? period?.start_date ?? "");
    setDraftEnd(endDate ?? period?.end_date ?? "");
  }, [startDate, endDate, period?.oldest_due_date, period?.start_date, period?.end_date]);

  const selectedCenter = data?.selected.work_center ?? null;
  const workCenters = data?.work_centers ?? [];
  const withdrawnEntries = data?.withdrawn?.items ?? [];
  const missingDueDates = data?.summary.missing_due_date_count ?? 0;
  // O horizonte da fila é o que foi puxado do TOTVS, não o recorte da tela.
  const periodHint = useMemo(() => {
    const pulledEnd = period?.pulled_end ?? period?.end_date;
    if (!pulledEnd) return null;
    const pulledStart = period?.pulled_start;
    return pulledStart
      ? copy.machineLoad.periodHint(formatIsoDate(pulledStart), formatIsoDate(pulledEnd))
      : copy.machineLoad.periodHintOpenStart(formatIsoDate(pulledEnd));
  }, [period?.pulled_start, period?.pulled_end, period?.end_date]);

  useEffect(() => {
    setRows(data?.selected.items ?? []);
  }, [data]);

  const finishedCount = useMemo(
    () => rows.filter((item) => isMachineLoadFinishedOperation(item)).length,
    [rows],
  );
  const displayRows = useMemo(
    () => (hideFinished ? filterActiveMachineLoadOperations(rows) : rows),
    [hideFinished, rows],
  );

  const toggleHideFinished = useCallback(() => {
    setHideFinished((prev) => {
      const next = !prev;
      try {
        sessionStorage.setItem(HIDE_FINISHED_STORAGE_KEY, next ? "1" : "0");
      } catch {
        /* ignore quota / private mode */
      }
      return next;
    });
  }, []);

  const runLocate = useCallback(
    async (rawQuery: string) => {
      const query = rawQuery.trim();
      if (!query) {
        setLocateError(copy.machineLoad.locate.emptyQuery);
        setLocateResult(null);
        return;
      }
      setLocateLoading(true);
      setLocateError(null);
      try {
        const payload = await fetchMachineLoadLocate({ branch, query });
        setLocateResult(payload);
        setLocateDraft(query);
        navigatePpc(
          buildPpcHref({
            subpluginId: "machine-load",
            branch,
            workCenter: workCenter ?? selectedCenter,
            startDate,
            endDate,
            locateQuery: query,
          }),
        );
      } catch (err: unknown) {
        setLocateResult(null);
        setLocateError(
          err instanceof Error ? err.message : copy.machineLoad.loadError,
        );
      } finally {
        setLocateLoading(false);
      }
    },
    [branch, endDate, selectedCenter, startDate, workCenter],
  );

  const clearLocate = useCallback(() => {
    setLocateResult(null);
    setLocateError(null);
    setLocateDraft("");
    locateAutoKeyRef.current = null;
    navigatePpc(
      buildPpcHref({
        subpluginId: "machine-load",
        branch,
        workCenter: workCenter ?? selectedCenter,
        startDate,
        endDate,
        locateQuery: null,
      }),
    );
  }, [branch, endDate, selectedCenter, startDate, workCenter]);

  useEffect(() => {
    const query = locateQuery?.trim() || "";
    if (!query) return;
    const key = `${branch}|${startDate ?? ""}|${endDate ?? ""}|${query}`;
    if (locateAutoKeyRef.current === key) return;
    locateAutoKeyRef.current = key;
    setLocateDraft(query);
    void runLocate(query);
  }, [branch, endDate, locateQuery, runLocate, startDate]);

  useEffect(() => {
    if (!highlightKey) return;
    const timer = window.setTimeout(() => setHighlightKey(null), HIGHLIGHT_MS);
    const row = document.querySelector<HTMLElement>(`[data-ppc-locate-key="${highlightKey}"]`);
    row?.scrollIntoView({ behavior: "smooth", block: "center" });
    return () => window.clearTimeout(timer);
  }, [highlightKey, rows]);

  const goToStop = useCallback(
    (stop: MachineLoadLocateStop) => {
      const key = machineLoadLocateRowKey(stop);
      setHighlightKey(key);
      navigatePpc(
        buildPpcHref({
          subpluginId: "machine-load",
          branch,
          workCenter: stop.work_center,
          startDate,
          endDate,
          locateQuery: (locateResult?.query ?? locateDraft.trim()) || null,
        }),
      );
    },
    [branch, endDate, locateDraft, locateResult?.query, startDate],
  );

  const closeRowMenu = useCallback(() => setRowMenu(null), []);

  const openConjuntoTraceModal = useCallback(
    async (conjuntoKey: string, paCode?: string | null) => {
      const key = conjuntoKey.trim();
      if (!key) return;
      setConjuntoModalOrder(key);
      setConjuntoModalPa(paCode?.trim() || null);
      setConjuntoModalOpen(true);
      setConjuntoModalLoading(true);
      setConjuntoModalError(null);
      setConjuntoModalResult(null);
      try {
        const payload = await fetchMachineLoadLocate({ branch, query: key });
        setConjuntoModalResult(payload);
      } catch (err: unknown) {
        setConjuntoModalResult(null);
        setConjuntoModalError(err instanceof Error ? err.message : copy.machineLoad.loadError);
      } finally {
        setConjuntoModalLoading(false);
      }
    },
    [branch],
  );

  const closeConjuntoModal = useCallback(() => {
    setConjuntoModalOpen(false);
    setConjuntoModalOrder(null);
    setConjuntoModalPa(null);
    setConjuntoModalError(null);
    setConjuntoModalResult(null);
    setConjuntoModalLoading(false);
  }, []);

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
    [applyPayload, branch, data?.selected.items, history, selectedCenter],
  );

  const prioritizeConjunto = useCallback(
    async (conjuntoKey: string) => {
      const key = conjuntoKey.trim();
      if (!key || sequenceBusy) return;
      const accepted = await confirm({
        title: copy.machineLoad.rowActions.prioritizeConfirmTitle(key),
        message: copy.machineLoad.rowActions.prioritizeConfirmMessage,
        confirmLabel: copy.machineLoad.rowActions.prioritizeConfirmAction,
        cancelLabel: copy.machineLoad.rowActions.prioritizeCancel,
        variant: "default",
      });
      if (!accepted) return;
      setSequenceBusy(true);
      setSequenceNotice(null);
      try {
        const payload = await prioritizeMachineLoadConjunto({
          branch,
          orderNumber: key,
          workCenter: selectedCenter,
        });
        applyPayload(payload);
        // A priorização mexe em vários CTs; o histórico só cobre o CT ativo.
        history.reset();
        setSequenceNotice(payload.prioritization.message);
      } catch (err: unknown) {
        setSequenceNotice(
          err instanceof Error ? err.message : copy.machineLoad.rowActions.prioritizeError,
        );
      } finally {
        setSequenceBusy(false);
      }
    },
    [applyPayload, branch, confirm, history, selectedCenter, sequenceBusy],
  );

  const optimizeDeliverySequence = useCallback(async () => {
    if (sequenceBusy) return;
    const accepted = await confirm({
      title: copy.machineLoad.optimizeDelivery.confirmTitle,
      message: copy.machineLoad.optimizeDelivery.confirmMessage,
      confirmLabel: copy.machineLoad.optimizeDelivery.confirmAction,
      cancelLabel: copy.machineLoad.optimizeDelivery.cancel,
      variant: "default",
    });
    if (!accepted) return;
    setSequenceBusy(true);
    setSequenceNotice(null);
    try {
      const payload = await optimizeMachineLoadDeliverySequence({
        branch,
        workCenter: selectedCenter,
      });
      applyPayload(payload);
      // A otimização atravessa todos os CTs; o histórico só cobre o CT ativo.
      history.reset();
      setSequenceNotice(payload.optimization.message);
    } catch (err: unknown) {
      setSequenceNotice(
        err instanceof Error ? err.message : copy.machineLoad.optimizeDelivery.error,
      );
    } finally {
      setSequenceBusy(false);
    }
  }, [applyPayload, branch, confirm, history, selectedCenter, sequenceBusy]);

  const withdrawConjunto = useCallback(
    async (conjuntoKey: string) => {
      const key = conjuntoKey.trim();
      if (!key || sequenceBusy) return;
      const accepted = await confirm({
        title: copy.machineLoad.rowActions.withdrawConfirmTitle(key),
        message: copy.machineLoad.rowActions.withdrawConfirmMessage,
        confirmLabel: copy.machineLoad.rowActions.withdrawConfirmAction,
        cancelLabel: copy.machineLoad.rowActions.withdrawCancel,
        variant: "danger",
      });
      if (!accepted) return;
      setSequenceBusy(true);
      setSequenceNotice(null);
      try {
        const payload = await withdrawMachineLoadConjunto({
          branch,
          orderNumber: key,
          workCenter: selectedCenter,
        });
        applyPayload(payload);
        // A retirada some com operações de vários CTs; o histórico só cobre o CT ativo.
        history.reset();
        setSequenceNotice(payload.withdrawal.message);
      } catch (err: unknown) {
        setSequenceNotice(
          err instanceof Error ? err.message : copy.machineLoad.rowActions.withdrawError,
        );
      } finally {
        setSequenceBusy(false);
      }
    },
    [applyPayload, branch, confirm, history, selectedCenter, sequenceBusy],
  );

  const restoreConjunto = useCallback(
    async (conjuntoKey: string) => {
      const key = conjuntoKey.trim();
      if (!key || sequenceBusy) return;
      setSequenceBusy(true);
      setSequenceNotice(null);
      try {
        const payload = await restoreMachineLoadConjunto({
          branch,
          orderNumber: key,
          workCenter: selectedCenter,
        });
        applyPayload(payload);
        history.reset();
        setSequenceNotice(payload.withdrawal.message);
        if ((payload.withdrawn?.items.length ?? 0) === 0) setWithdrawnModalOpen(false);
      } catch (err: unknown) {
        setSequenceNotice(
          err instanceof Error ? err.message : copy.machineLoad.rowActions.restoreError,
        );
      } finally {
        setSequenceBusy(false);
      }
    },
    [applyPayload, branch, history, selectedCenter, sequenceBusy],
  );

  const sendOperationToWorkCenter = useCallback(
    async (operation: MachineLoadOperation, targetWorkCenter: string) => {
      const target = targetWorkCenter.trim();
      if (!target || sequenceBusy) return;
      setSequenceBusy(true);
      setSequenceNotice(null);
      try {
        const payload = await transferMachineLoadOperation({
          branch,
          productionOrder: operation.production_order,
          operationCode: operation.operation_code,
          targetWorkCenter: target,
          workCenter: selectedCenter,
        });
        applyPayload(payload);
        // A operação muda de fila; o histórico de Ctrl+Z é do CT ativo.
        history.reset();
        setSequenceNotice(payload.transfer.message);
        setTransferOperation(null);
      } catch (err: unknown) {
        setSequenceNotice(
          err instanceof Error ? err.message : copy.machineLoad.rowActions.transferError,
        );
      } finally {
        setSequenceBusy(false);
      }
    },
    [applyPayload, branch, history, selectedCenter, sequenceBusy],
  );

  const sendConjuntoToWorkCenter = useCallback(
    async (operation: MachineLoadOperation, targetWorkCenter: string) => {
      const target = targetWorkCenter.trim();
      const source = (operation.work_center || selectedCenter || "").trim();
      if (!target || !source || sequenceBusy) return;
      setSequenceBusy(true);
      setSequenceNotice(null);
      try {
        const payload = await transferMachineLoadConjunto({
          branch,
          orderNumber: operation.production_order,
          sourceWorkCenter: source,
          targetWorkCenter: target,
          workCenter: selectedCenter,
        });
        applyPayload(payload);
        history.reset();
        setSequenceNotice(payload.transfer.message);
        setTransferOperation(null);
      } catch (err: unknown) {
        setSequenceNotice(
          err instanceof Error ? err.message : copy.machineLoad.rowActions.transferError,
        );
      } finally {
        setSequenceBusy(false);
      }
    },
    [applyPayload, branch, history, selectedCenter, sequenceBusy],
  );

  const onReorder = useCallback(
    (nextRows: MachineLoadOperation[]) => {
      if (sequenceBusy || hideFinished) return;
      void persistOrder(nextRows, {
        previousKeys: keysFromOperations(rows),
        pushUndo: true,
      });
    },
    [hideFinished, persistOrder, rows, sequenceBusy],
  );

  const reorder = useMachineLoadRowReorder(displayRows, onReorder);

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
    [applyPayload, branch, data?.selected.items, rows, selectedCenter, sequenceBusy],
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
          const rowIndex = displayRows.findIndex(
            (item) =>
              item.production_order === row.production_order &&
              item.operation_code === row.operation_code,
          );
          return (
            <button
              type="button"
              className="ppc-load__drag-handle"
              aria-label={copy.machineLoad.dragHandle}
              title={
                hideFinished
                  ? copy.machineLoad.hideFinished.reorderDisabled
                  : copy.machineLoad.dragHandle
              }
              disabled={hideFinished || sequenceBusy}
              {...(hideFinished ? {} : reorder.handleProps(Math.max(0, rowIndex)))}
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
        render: (row: MachineLoadOperation) => (
          <span className="ppc-load__order">
            {row.production_order || "—"}
            {row.transferred_from ? (
              <span
                className="ppc-load__transferred"
                title={copy.machineLoad.transfer.originBadgeTitle(row.transferred_from)}
              >
                {copy.machineLoad.transfer.originBadge(row.transferred_from)}
              </span>
            ) : null}
          </span>
        ),
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
    [displayRows, hideFinished, reorder, sequenceBusy],
  );

  const goTo = (next: {
    workCenter?: string | null;
    startDate?: string | null;
    endDate?: string | null;
    locateQuery?: string | null;
  }) => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "machine-load",
        branch,
        workCenter: next.workCenter !== undefined ? next.workCenter : selectedCenter,
        startDate: next.startDate !== undefined ? next.startDate : startDate,
        endDate: next.endDate !== undefined ? next.endDate : endDate,
        locateQuery:
          next.locateQuery !== undefined
            ? next.locateQuery
            : (locateResult?.query ?? locateDraft.trim()) || null,
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
        badge={selectedCenter}
        stats={
          data ? (
            <>
              <span className="ppc-header__chip">{copy.machineLoad.summary(
                data.summary.work_center_count,
                data.summary.operation_count,
              )}</span>
              {data.summary.in_production_count > 0 ? (
                <span className="ppc-header__chip ppc-header__chip--running">
                  {copy.machineLoad.inProductionSummary(data.summary.in_production_count)}
                </span>
              ) : null}
            </>
          ) : null
        }
        branch={branch}
        subpluginId="machine-load"
        workCenter={selectedCenter}
        startDate={startDate}
        endDate={endDate}
        onRefresh={onRefreshClick}
        refreshBusy={refreshing}
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
        {periodHint ? <span className="ppc-period__hint">{periodHint}</span> : null}
        {missingDueDates > 0 ? (
          <span className="ppc-period__warning" role="status">
            {copy.machineLoad.periodMissingDueDate(missingDueDates)}
          </span>
        ) : null}
      </form>

      <MachineLoadLocatePanel
        draftQuery={locateDraft}
        onDraftQueryChange={setLocateDraft}
        onSearch={runLocate}
        onClear={clearLocate}
        loading={locateLoading}
        error={locateError}
        result={locateResult}
        onGoToStop={goToStop}
      />

      <div className="ppc-period ppc-period--meta">
        <OperatorCockpitLinkButton branch={branch} />
        <button
          type="button"
          className="ppc-period__optimize"
          onClick={optimizeDeliverySequence}
          disabled={sequenceBusy || !data || data.summary.operation_count === 0}
          title={copy.machineLoad.optimizeDelivery.hint}
        >
          <ArrowDownNarrowWide size={15} strokeWidth={1.75} aria-hidden />
          {sequenceBusy
            ? copy.machineLoad.optimizeDelivery.busy
            : copy.machineLoad.optimizeDelivery.label}
        </button>
        {withdrawnEntries.length > 0 ? (
          <button
            type="button"
            className="ppc-period__withdrawn"
            onClick={() => setWithdrawnModalOpen(true)}
          >
            <CalendarOff size={15} strokeWidth={1.75} aria-hidden />
            {copy.machineLoad.withdrawn.openButton(withdrawnEntries.length)}
          </button>
        ) : null}
        {finishedCount > 0 || hideFinished ? (
          <button
            type="button"
            className={
              hideFinished
                ? "ppc-period__hide-finished ppc-period__hide-finished--active"
                : "ppc-period__hide-finished"
            }
            onClick={toggleHideFinished}
            title={
              hideFinished
                ? copy.machineLoad.hideFinished.hintHide
                : copy.machineLoad.hideFinished.hintShow
            }
            aria-pressed={hideFinished}
          >
            {hideFinished ? (
              <Eye size={15} strokeWidth={1.75} aria-hidden />
            ) : (
              <EyeOff size={15} strokeWidth={1.75} aria-hidden />
            )}
            {hideFinished
              ? copy.machineLoad.hideFinished.showingHidden(finishedCount)
              : copy.machineLoad.hideFinished.withCount(finishedCount)}
          </button>
        ) : null}
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
      </div>

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
            layout="wrap"
            density="compact"
            classNames={navClassNames}
            aria-label={copy.machineLoad.tabsAria}
          />
          <div
            className="ppc-load__panel"
            id="ppc-load-panel"
            role="tabpanel"
            aria-busy={switchingCenter || undefined}
            aria-labelledby={selectedCenter ? `ppc-load-tab-${selectedCenter}` : undefined}
          >
            {activeCenter?.work_center_name ? (
              <p className="ppc-load__center-name">{activeCenter.work_center_name}</p>
            ) : null}
            {displayRows.length > 1 && !hideFinished ? (
              <p className="ppc-load__sequence-hint">{copy.machineLoad.sequenceHint}</p>
            ) : null}
            {hideFinished ? (
              <p className="ppc-load__sequence-hint">{copy.machineLoad.hideFinished.reorderDisabled}</p>
            ) : null}
            <DataTable
              columns={columns}
              rows={displayRows}
              rowKey={(row) => `${row.production_order}-${row.operation_code}`}
              getRowClassName={(row, index) =>
                [
                  machineLoadRowModifierClass(row),
                  reorder.rowClassName(index),
                  highlightKey === machineLoadLocateRowKey(row)
                    ? "ppc-load__row--locate-hit"
                    : null,
                ]
                  .filter(Boolean)
                  .join(" ") || undefined
              }
              getRowProps={(row, index) => ({
                ...(hideFinished ? {} : reorder.rowDropProps(index)),
                "data-ppc-locate-key": machineLoadLocateRowKey(row),
                onContextMenu: (event: MouseEvent) => {
                  event.preventDefault();
                  setRowMenu({
                    operation: row,
                    position: { x: event.clientX, y: event.clientY },
                  });
                },
              })}
              emptyMessage={
                hideFinished && rows.length > 0
                  ? copy.machineLoad.hideFinished.empty
                  : copy.machineLoad.emptyOperations
              }
              loading={loading}
              classNames={tableClassNames}
              labels={tableLabels}
              layout="section"
            />
          </div>
        </section>
      ) : null}

      <MachineLoadRowContextMenu
        open={Boolean(rowMenu)}
        position={rowMenu?.position ?? null}
        operation={rowMenu?.operation ?? null}
        onClose={closeRowMenu}
        onTraceConjunto={(conjuntoKey) => {
          const pa = rowMenu?.operation?.pa_product_code?.trim() || null;
          void openConjuntoTraceModal(conjuntoKey, pa);
        }}
        onPrioritizeConjunto={(conjuntoKey) => void prioritizeConjunto(conjuntoKey)}
        onWithdrawConjunto={(conjuntoKey) => void withdrawConjunto(conjuntoKey)}
        onTransferConjunto={(operation) => {
          setTransferMode("conjunto");
          setTransferOperation(operation);
        }}
        onTransferOperation={(operation) => {
          setTransferMode("operation");
          setTransferOperation(operation);
        }}
        prioritizeDisabled={sequenceBusy}
        withdrawDisabled={sequenceBusy}
        transferDisabled={sequenceBusy}
      />

      <MachineLoadTransferModal
        open={Boolean(transferOperation)}
        mode={transferMode}
        operation={transferOperation}
        workCenters={workCenters}
        busy={sequenceBusy}
        onClose={() => setTransferOperation(null)}
        onConfirm={(target) => {
          if (!transferOperation) return;
          if (transferMode === "conjunto") {
            void sendConjuntoToWorkCenter(transferOperation, target);
            return;
          }
          void sendOperationToWorkCenter(transferOperation, target);
        }}
      />

      <MachineLoadWithdrawnModal
        open={withdrawnModalOpen}
        entries={withdrawnEntries}
        busy={sequenceBusy}
        onClose={() => setWithdrawnModalOpen(false)}
        onRestore={(orderNumber) => void restoreConjunto(orderNumber)}
      />

      <MachineLoadLocateModal
        open={conjuntoModalOpen}
        productionOrder={conjuntoModalOrder}
        paCode={conjuntoModalPa}
        loading={conjuntoModalLoading}
        error={conjuntoModalError}
        result={conjuntoModalResult}
        onClose={closeConjuntoModal}
        onGoToStop={goToStop}
      />
    </div>
  );
}
