import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent } from "react";
import { BarChart3, Eye, ListFilter, MoreVertical, RefreshCw, Search, User } from "lucide-react";
import {
  fetchPublicMachineLoad,
  type MachineLoadOperation,
  type MachineLoadWorkCenter,
  type PublicMachineLoadPayload,
} from "./api";
import {
  BrandBar,
  CopyValueButton,
  DrawingViewer,
  efficiencyTone,
  formatDate,
  formatDateTime,
  formatHours,
  formatPercent,
  formatQty,
  formatUnit,
  isFinishedOperation,
  operationKey,
  operationPendingQty,
  resolveStatus,
} from "./cockpitShared";
import { OperationDetailPage } from "./OperationDetailPage";
import { usePublicMachineLoadRealtime } from "./usePublicMachineLoadRealtime";
import { useCockpitView } from "./useCockpitView";
import { useWorkCenterPerformance } from "./useWorkCenterPerformance";
import { usePublicWorkCenterDowntimeItems } from "./usePublicWorkCenterDowntimeItems";
import { WorkCenterPerformancePage } from "./WorkCenterPerformancePage";
import type { PublicWorkCenterDowntimeItemsState } from "./usePublicWorkCenterDowntimeItems";
import "./cockpit.css";

function matchesQueueSearch(operation: MachineLoadOperation, term: string): boolean {
  if (!term) return true;
  const op = operation.production_order.toLowerCase();
  const pa = (operation.pa_product_code || "").toLowerCase();
  const product = (operation.product_code || "").toLowerCase();
  return op.includes(term) || pa.includes(term) || product.includes(term);
}

function isRunningOperation(operation: MachineLoadOperation): boolean {
  return resolveStatus(operation).tone === "running";
}

const LIVE_STATUS_POLL_MS = 15_000;
const STORAGE_PREFIX = "delpi.pcp.cockpit.work-center";
const HIDE_FINISHED_PREFIX = "delpi.pcp.cockpit.hide-finished";

type Props = {
  token: string;
  branch: string;
  initial: PublicMachineLoadPayload;
};

type VisualTarget = {
  paCode: string | null;
  productCode: string | null;
  has3dModel: boolean;
};

type QueueEntry = {
  operation: MachineLoadOperation;
  position: number;
};

function storageKey(branch: string): string {
  return `${STORAGE_PREFIX}.${branch}`;
}

function hideFinishedStorageKey(branch: string, workCenter: string): string {
  return `${HIDE_FINISHED_PREFIX}.${branch}.${workCenter}`;
}

function readStoredWorkCenter(branch: string): string | null {
  try {
    return window.localStorage.getItem(storageKey(branch));
  } catch {
    return null;
  }
}

function storeWorkCenter(branch: string, workCenter: string | null): void {
  try {
    if (workCenter) window.localStorage.setItem(storageKey(branch), workCenter);
    else window.localStorage.removeItem(storageKey(branch));
  } catch {
    /* modo privado sem storage: a escolha vale só para esta sessão */
  }
}

function readHideFinished(branch: string, workCenter: string): boolean {
  try {
    return window.localStorage.getItem(hideFinishedStorageKey(branch, workCenter)) === "1";
  } catch {
    return false;
  }
}

function storeHideFinished(branch: string, workCenter: string, hide: boolean): void {
  try {
    const key = hideFinishedStorageKey(branch, workCenter);
    if (hide) window.localStorage.setItem(key, "1");
    else window.localStorage.removeItem(key);
  } catch {
    /* modo privado: só vale na sessão */
  }
}

function resolveVisualMeta(operation: MachineLoadOperation) {
  const paCode = operation.pa_product_code?.trim() || "";
  const productCode = operation.product_code?.trim() || "";
  const has3dModel = Boolean(operation.has_3d_model && productCode);
  const canOpenVisual = Boolean(paCode) || has3dModel;
  const visualLabel =
    paCode && has3dModel ? "Ver desenho / 3D" : has3dModel ? "Ver 3D" : "Ver desenho";
  const displayProductCode = paCode || operation.product_code;
  return { paCode, productCode, has3dModel, canOpenVisual, visualLabel, displayProductCode };
}

export function OperatorCockpit({ token, branch, initial }: Props) {
  const [payload, setPayload] = useState<PublicMachineLoadPayload>(initial);
  const [workCenter, setWorkCenter] = useState<string | null>(() => {
    const stored = readStoredWorkCenter(branch);
    const exists = initial.work_centers.some((item) => item.work_center === stored);
    return stored && exists ? stored : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date>(() => new Date());
  const [visualTarget, setVisualTarget] = useState<VisualTarget | null>(null);
  const [downtimeOpen, setDowntimeOpen] = useState(false);
  const [queueQuery, setQueueQuery] = useState("");
  const [hideFinished, setHideFinished] = useState(false);
  const workCenterRef = useRef(workCenter);
  workCenterRef.current = workCenter;
  const reloadGenerationRef = useRef(0);
  const { view, openQueue, openOperation, openPerformance } = useCockpitView();

  useEffect(() => {
    setDowntimeOpen(false);
  }, [workCenter]);

  useEffect(() => {
    if (!workCenter) {
      setHideFinished(false);
      return;
    }
    setHideFinished(readHideFinished(branch, workCenter));
  }, [branch, workCenter]);

  const reload = useCallback(
    async (center: string | null, options?: { quiet?: boolean }) => {
      const quiet = options?.quiet === true;
      const generation = ++reloadGenerationRef.current;
      if (!quiet) setLoading(true);
      try {
        const next = await fetchPublicMachineLoad(token, branch, center);
        if (generation !== reloadGenerationRef.current) return;
        setPayload(next);
        setUpdatedAt(new Date());
        setError(null);
      } catch (err) {
        if (generation !== reloadGenerationRef.current) return;
        setError(err instanceof Error ? err.message : "Não foi possível atualizar a fila.");
      } finally {
        if (!quiet && generation === reloadGenerationRef.current) setLoading(false);
      }
    },
    [token, branch],
  );

  useEffect(() => {
    if (!workCenter || payload.selected.work_center === workCenter) return;
    void reload(workCenter);
  }, [workCenter, payload.selected.work_center, reload]);

  const connected = usePublicMachineLoadRealtime({
    token,
    branch,
    onChanged: useCallback(() => {
      // Sequência/refresh do PCP: atualiza sem flicker de loading.
      void reload(workCenterRef.current, { quiet: true });
    }, [reload]),
  });

  // Status ao vivo (em produção / já apontada) vem do enrich no GET — o WS não cobre apontamentos.
  useEffect(() => {
    const refreshLiveStatus = () => {
      if (document.visibilityState === "hidden") return;
      void reload(workCenterRef.current, { quiet: true });
    };

    const timer = window.setInterval(refreshLiveStatus, LIVE_STATUS_POLL_MS);
    const onVisibility = () => {
      if (document.visibilityState === "visible") refreshLiveStatus();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [reload]);

  const performance = useWorkCenterPerformance(token, branch, workCenter);
  const downtimeItems = usePublicWorkCenterDowntimeItems(
    token,
    branch,
    workCenter,
    downtimeOpen,
  );

  const selectWorkCenter = (center: string) => {
    storeWorkCenter(branch, center);
    setQueueQuery("");
    setWorkCenter(center);
  };

  const clearWorkCenter = () => {
    storeWorkCenter(branch, null);
    setQueueQuery("");
    setWorkCenter(null);
    openQueue();
  };

  const toggleHideFinished = () => {
    if (!workCenter) return;
    setHideFinished((current) => {
      const next = !current;
      storeHideFinished(branch, workCenter, next);
      return next;
    });
  };

  const activeCenter = payload.work_centers.find((item) => item.work_center === workCenter);
  const items =
    workCenter && payload.selected.work_center === workCenter ? payload.selected.items : [];

  const finishedCount = useMemo(
    () => items.filter(isFinishedOperation).length,
    [items],
  );

  const visibleItems = useMemo(
    () => (hideFinished ? items.filter((operation) => !isFinishedOperation(operation)) : items),
    [items, hideFinished],
  );

  const activeEntry = useMemo<QueueEntry | null>(() => {
    if (visibleItems.length === 0) return null;
    const runningIndex = visibleItems.findIndex(isRunningOperation);
    const operation = visibleItems[runningIndex >= 0 ? runningIndex : 0]!;
    const position = items.findIndex((item) => operationKey(item) === operationKey(operation)) + 1;
    return { operation, position: Math.max(1, position) };
  }, [visibleItems, items]);

  const upcomingEntries = useMemo(() => {
    const term = queueQuery.trim().toLowerCase();
    const activeKey = activeEntry ? operationKey(activeEntry.operation) : null;
    return visibleItems
      .map((operation) => {
        const position = items.findIndex((item) => operationKey(item) === operationKey(operation)) + 1;
        return { operation, position: Math.max(1, position) };
      })
      .filter(({ operation }) => operationKey(operation) !== activeKey)
      .filter(({ operation }) => matchesQueueSearch(operation, term));
  }, [visibleItems, items, queueQuery, activeEntry]);

  const selectedOperation = useMemo(() => {
    if (view.kind !== "operation") return null;
    const index = items.findIndex(
      (item) =>
        item.production_order === view.productionOrder &&
        item.operation_code === view.operationCode,
    );
    return index >= 0 ? { operation: items[index]!, position: index + 1 } : null;
  }, [view, items]);

  // A fila some quando o PCP reprograma: sem a operação na tela, volta para a lista.
  useEffect(() => {
    if (view.kind !== "operation") return;
    if (loading || items.length === 0) return;
    if (!selectedOperation) openQueue();
  }, [view.kind, loading, items.length, selectedOperation, openQueue]);

  if (!workCenter) {
    return (
      <WorkCenterPicker
        branch={branch}
        workCenters={payload.work_centers}
        onSelect={selectWorkCenter}
      />
    );
  }

  if (view.kind === "performance") {
    return (
      <WorkCenterPerformancePage
        branch={branch}
        workCenter={workCenter}
        workCenterName={activeCenter?.work_center_name || workCenter}
        performance={performance.data}
        loading={performance.loading}
        error={performance.error}
        onBack={openQueue}
      />
    );
  }

  if (view.kind === "operation" && selectedOperation) {
    const index = selectedOperation.position - 1;
    const previous = index > 0 ? items[index - 1] : null;
    const next = index < items.length - 1 ? items[index + 1] : null;

    return (
      <OperationDetailPage
        key={operationKey(selectedOperation.operation)}
        token={token}
        branch={branch}
        operation={selectedOperation.operation}
        position={selectedOperation.position}
        queueSize={items.length}
        onBack={openQueue}
        onPrevious={
          previous
            ? () => openOperation(previous.production_order, previous.operation_code)
            : undefined
        }
        onNext={
          next ? () => openOperation(next.production_order, next.operation_code) : undefined
        }
      />
    );
  }

  const centerName = activeCenter?.work_center_name || workCenter;
  const efficiency = performance.data?.efficiency;
  const downtime = performance.data?.downtime;
  const shiftPct = efficiency?.available ? efficiency.shift_pct : null;
  const shiftProducedQty = efficiency?.available ? efficiency.shift_produced_qty : null;
  const shiftLabel = performance.data?.shift?.label ?? "Turno";
  const effTone = efficiencyTone(shiftPct);

  return (
    <section className="pcp-pub pcp-pub--queue">
      <header className="pcp-pub__masthead">
        <div className="pcp-pub__topbar">
          <div className="pcp-pub__topbar-inner">
            <div className="pcp-pub__topbar-brand">
              <span className="pcp-pub__logo pcp-pub__logo--sm">
                <img src="/p/logoMinhaDelpi.svg" alt="Minha DELPI" draggable={false} />
              </span>
              <div className="pcp-pub__topbar-titles">
                <h1 className="pcp-pub__app-title">Minha produção</h1>
                <span className="pcp-pub__branch-pill">Filial {branch}</span>
              </div>
            </div>
            <div className="pcp-pub__topbar-actions">
              {hideFinished ? (
                <span className="pcp-pub__topbar-chip" title="Ordens já apontadas ocultas neste posto">
                  Fila limpa
                </span>
              ) : null}
              <CockpitActionsMenu
                hideFinished={hideFinished}
                finishedCount={finishedCount}
                onOpenPerformance={openPerformance}
                onClearWorkCenter={clearWorkCenter}
                onToggleHideFinished={toggleHideFinished}
              />
            </div>
          </div>
        </div>

        <div className="pcp-pub__hero">
          <div className="pcp-pub__hero-inner">
            <div className="pcp-pub__hero-center">
              <p className="pcp-pub__hero-label">Centro de trabalho</p>
              <p className="pcp-pub__hero-code">{workCenter}</p>
            </div>
            <div className="pcp-pub__hero-process">
              <h2 className="pcp-pub__hero-name">{centerName}</h2>
              <p className="pcp-pub__hero-eyebrow">Fila de produção</p>
            </div>
            <div className="pcp-pub__hero-metrics" role="group" aria-label="Desempenho do posto">
              <button
                type="button"
                className={`pcp-pub__hero-metric pcp-pub__hero-metric--eff-${effTone}`}
                onClick={openPerformance}
                title={`Eficiência do posto no ${shiftLabel.toLowerCase()}`}
              >
                <span className="pcp-pub__hero-metric-label">{shiftLabel}</span>
                <strong className="pcp-pub__hero-metric-value">{formatPercent(shiftPct)}</strong>
              </button>
              <button
                type="button"
                className="pcp-pub__hero-metric"
                onClick={openPerformance}
                title={`Peças produzidas no ${shiftLabel.toLowerCase()}`}
              >
                <span className="pcp-pub__hero-metric-label">Produzido · turno</span>
                <strong className="pcp-pub__hero-metric-value">
                  {shiftProducedQty == null
                    ? "—"
                    : `${formatQty(shiftProducedQty)} ${formatUnit(null, shiftProducedQty)}`}
                </strong>
              </button>
              <button
                type="button"
                className="pcp-pub__hero-metric"
                onClick={() => setDowntimeOpen(true)}
                title={`Paradas apontadas no ${shiftLabel.toLowerCase()} neste posto — clique para ver motivos`}
              >
                <span className="pcp-pub__hero-metric-label">Paradas · turno</span>
                <strong className="pcp-pub__hero-metric-value">
                  {downtime?.available ? formatHours(downtime.today_hours) : "—"}
                </strong>
              </button>
            </div>
            <div className="pcp-pub__hero-aside">
              <span
                className={`pcp-pub__live ${connected ? "pcp-pub__live--on" : "pcp-pub__live--off"}`}
                title={
                  connected
                    ? "Conectado: sequência do PCP ao vivo; status das OPs a cada 15s."
                    : "Sem socket: status e fila atualizam a cada 15s."
                }
              >
                <span className="pcp-pub__live-dot" aria-hidden="true" />
                {connected ? "Ao vivo" : "Reconectando"}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="pcp-pub__wrap">
        {error ? <p className="pcp-pub__error">{error}</p> : null}

        {items.length === 0 ? (
          <p className="pcp-pub__empty">
            {loading ? "Carregando fila…" : "Nenhuma operação programada para este posto."}
          </p>
        ) : visibleItems.length === 0 ? (
          <p className="pcp-pub__empty">
            Todas as operações deste posto já foram apontadas. Use Ações → Mostrar apontadas para
            vê-las de novo.
          </p>
        ) : (
          <>
            {activeEntry ? (
              <ActiveNowCard
                entry={activeEntry}
                onOpenVisual={setVisualTarget}
                onOpenDetail={() =>
                  openOperation(
                    activeEntry.operation.production_order,
                    activeEntry.operation.operation_code,
                  )
                }
              />
            ) : null}

            <section className="pcp-pub__upcoming" aria-labelledby="pcp-pub-upcoming-title">
              <div className="pcp-pub__upcoming-head">
                <div className="pcp-pub__upcoming-titles">
                  <h3 id="pcp-pub-upcoming-title">Próximas operações</h3>
                  <span className="pcp-pub__upcoming-count">
                    {upcomingEntries.length} na fila
                  </span>
                </div>
                <label className="pcp-pub__search-field pcp-pub__search-field--inline">
                  <Search className="pcp-pub__search-icon" size={18} strokeWidth={2} aria-hidden="true" />
                  <input
                    className="pcp-pub__search"
                    type="search"
                    value={queueQuery}
                    onChange={(event) => setQueueQuery(event.target.value)}
                    placeholder="Buscar OP ou PA"
                    aria-label="Buscar operação por OP ou PA"
                    autoComplete="off"
                    enterKeyHint="search"
                  />
                </label>
              </div>

              {upcomingEntries.length === 0 ? (
                <p className="pcp-pub__empty pcp-pub__empty--soft">
                  {queueQuery.trim()
                    ? `Nenhuma operação encontrada para “${queueQuery.trim()}”.`
                    : "Não há outras operações na fila deste posto."}
                </p>
              ) : (
                <div className="pcp-pub__queue-table-wrap">
                  <table className="pcp-pub__queue-table">
                    <thead>
                      <tr>
                        <th scope="col">Seq</th>
                        <th scope="col">OP / Produto</th>
                        <th scope="col">Operação</th>
                        <th scope="col">Pendente</th>
                        <th scope="col">Programada</th>
                        <th scope="col">Entrega</th>
                        <th scope="col">Consulta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {upcomingEntries.map((entry, index) => (
                        <UpcomingRow
                          key={operationKey(entry.operation)}
                          entry={entry}
                          isNext={index === 0}
                          onOpenDetail={() =>
                            openOperation(
                              entry.operation.production_order,
                              entry.operation.operation_code,
                            )
                          }
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}

        <footer className="pcp-pub__footer">
          <span>
            Atualizado às{" "}
            {updatedAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
          </span>
          {payload.snapshot.refreshed_at ? (
            <span>Fila publicada em {formatDateTime(payload.snapshot.refreshed_at)}</span>
          ) : null}
        </footer>
      </div>

      {visualTarget ? (
        <DrawingViewer
          token={token}
          branch={branch}
          paCode={visualTarget.paCode}
          productCode={visualTarget.productCode}
          has3dModel={visualTarget.has3dModel}
          onClose={() => setVisualTarget(null)}
        />
      ) : null}

      {downtimeOpen ? (
        <DowntimeItemsModal
          shiftLabel={shiftLabel}
          hours={downtime?.available ? downtime.today_hours : null}
          state={downtimeItems}
          onClose={() => setDowntimeOpen(false)}
        />
      ) : null}
    </section>
  );
}

type PickerProps = {
  branch: string;
  workCenters: MachineLoadWorkCenter[];
  onSelect: (workCenter: string) => void;
};

function CockpitActionsMenu({
  hideFinished,
  finishedCount,
  onOpenPerformance,
  onClearWorkCenter,
  onToggleHideFinished,
}: {
  hideFinished: boolean;
  finishedCount: number;
  onOpenPerformance: () => void;
  onClearWorkCenter: () => void;
  onToggleHideFinished: () => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const run = (action: () => void) => {
    setOpen(false);
    action();
  };

  return (
    <div className="pcp-pub__actions-menu" ref={rootRef}>
      <button
        type="button"
        className={`pcp-pub__actions-trigger ${open ? "is-open" : ""}`}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Ações da fila"
        title="Ações"
        onClick={() => setOpen((value) => !value)}
      >
        <MoreVertical size={20} strokeWidth={2.2} aria-hidden="true" />
      </button>
      {open ? (
        <div className="pcp-pub__actions-panel" role="menu" aria-label="Ações da fila">
          <button
            type="button"
            role="menuitem"
            className="pcp-pub__actions-item"
            onClick={() => run(onOpenPerformance)}
          >
            <BarChart3 size={18} strokeWidth={2} aria-hidden="true" />
            Ver desempenho
          </button>
          <button
            type="button"
            role="menuitem"
            className="pcp-pub__actions-item"
            onClick={() => run(onClearWorkCenter)}
          >
            <RefreshCw size={18} strokeWidth={2} aria-hidden="true" />
            Trocar posto
          </button>
          <button
            type="button"
            role="menuitem"
            className={`pcp-pub__actions-item ${hideFinished ? "is-active" : ""}`}
            onClick={() => run(onToggleHideFinished)}
            title={
              hideFinished
                ? "Volta a exibir as operações já apontadas nesta fila."
                : "Esconde as operações já apontadas. A preferência fica salva neste aparelho."
            }
          >
            <ListFilter size={18} strokeWidth={2} aria-hidden="true" />
            {hideFinished
              ? finishedCount > 0
                ? `Mostrar apontadas (${finishedCount})`
                : "Mostrar apontadas"
              : finishedCount > 0
                ? `Limpar fila (${finishedCount})`
                : "Limpar fila"}
          </button>
        </div>
      ) : null}
    </div>
  );
}

function WorkCenterPicker({ branch, workCenters, onSelect }: PickerProps) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return workCenters;
    return workCenters.filter(
      (item) =>
        item.work_center.toLowerCase().includes(term) ||
        item.work_center_name.toLowerCase().includes(term),
    );
  }, [workCenters, query]);

  return (
    <section className="pcp-pub pcp-pub--picker">
      <BrandBar
        eyebrow={`Fila de produção · Filial ${branch}`}
        title="Escolha o seu posto de trabalho"
        stats={
          <span className="pcp-pub__chip">
            {workCenters.length} {workCenters.length === 1 ? "posto" : "postos"}
          </span>
        }
      />

      <div className="pcp-pub__wrap">
        <p className="pcp-pub__notice">
          A escolha fica salva neste aparelho; você pode trocar depois pelo cabeçalho.
        </p>

        {workCenters.length > 8 ? (
          <input
            className="pcp-pub__search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar posto ou máquina…"
            aria-label="Buscar posto de trabalho"
          />
        ) : null}

        {filtered.length === 0 ? (
          <p className="pcp-pub__empty">Nenhum posto encontrado.</p>
        ) : (
          <div className="pcp-pub__centers">
            {filtered.map((item) => (
              <button
                key={item.work_center}
                type="button"
                className="pcp-pub__center"
                onClick={() => onSelect(item.work_center)}
              >
                <span className="pcp-pub__center-code">{item.work_center}</span>
                <span className="pcp-pub__center-name">{item.work_center_name}</span>
                <span className="pcp-pub__center-meta">
                  {item.operation_count} {item.operation_count === 1 ? "operação" : "operações"}
                  {item.in_production_count ? ` · ${item.in_production_count} em produção` : ""}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function ActiveNowCard({
  entry,
  onOpenVisual,
  onOpenDetail,
}: {
  entry: QueueEntry;
  onOpenVisual: (target: VisualTarget) => void;
  onOpenDetail: () => void;
}) {
  const { operation, position } = entry;
  const status = resolveStatus(operation);
  const pendingQty = operationPendingQty(operation);
  const { paCode, productCode, has3dModel, canOpenVisual, visualLabel, displayProductCode } =
    resolveVisualMeta(operation);

  const openFromCard = (event: MouseEvent<HTMLElement>) => {
    if ((event.target as HTMLElement).closest("button")) return;
    onOpenDetail();
  };

  const scheduled =
    operation.scheduled_start_time
      ? `${formatDate(operation.scheduled_date)} ${operation.scheduled_start_time}`
      : formatDate(operation.scheduled_date);

  return (
    <section className="pcp-pub__now" aria-labelledby="pcp-pub-now-title">
      <div className="pcp-pub__now-head">
        <h3 id="pcp-pub-now-title">Agora nesta bancada</h3>
        <span className={`pcp-pub__badge pcp-pub__badge--${status.tone}`}>
          {status.tone === "running" ? (
            <span className="pcp-pub__badge-dot" aria-hidden="true" />
          ) : null}
          {status.label}
        </span>
      </div>

      <article
        className={`pcp-pub__now-card pcp-pub__now-card--${status.tone}`}
        onClick={openFromCard}
      >
        <div className="pcp-pub__now-main">
          <span className="pcp-pub__now-seq" aria-label={`Ordem ${position}`}>
            Ordem {String(position).padStart(2, "0")}
          </span>

          <div className="pcp-pub__now-identity">
            <div className="pcp-pub__now-order">
              <strong>{operation.production_order}</strong>
              <CopyValueButton value={operation.production_order} label="Copiar OP" />
            </div>
            <p className="pcp-pub__now-product">
              <strong className={paCode ? "pcp-pub__product-code--pa" : undefined}>
                {displayProductCode}
              </strong>{" "}
              {operation.product_description}
            </p>
          </div>

          <div className="pcp-pub__now-qty" aria-label="Quantidade pendente">
            <span className="pcp-pub__now-qty-label">Quantidade pendente</span>
            <strong className="pcp-pub__now-qty-value">
              {formatQty(pendingQty)} {formatUnit(operation.unit, pendingQty)}
            </strong>
          </div>
        </div>

        <dl className="pcp-pub__now-facts">
          <div>
            <dt>Operação</dt>
            <dd>
              {operation.operation_code} · {operation.operation_description}
            </dd>
          </div>
          <div>
            <dt>Ferramenta</dt>
            <dd>{operation.tool || "—"}</dd>
          </div>
          <div>
            <dt>Programada</dt>
            <dd>{scheduled}</dd>
          </div>
          <div>
            <dt>Entrega</dt>
            <dd>{formatDate(operation.pa_due_date)}</dd>
          </div>
        </dl>

        <div className="pcp-pub__now-foot">
          <div className="pcp-pub__now-operator">
            <span className="pcp-pub__now-operator-avatar" aria-hidden="true">
              <User size={18} strokeWidth={2} />
            </span>
            <div>
              <p className="pcp-pub__now-operator-name">
                {operation.active_operator_name?.trim() || "Sem operador apontado"}
              </p>
              <p className="pcp-pub__now-operator-note">
                {status.operatorNote ||
                  (status.tone === "running" ? "Em produção neste posto" : "Próxima da fila")}
              </p>
            </div>
          </div>

          <div className="pcp-pub__now-actions">
            <button type="button" className="pcp-pub__btn pcp-pub__btn--ghost" onClick={onOpenDetail}>
              Detalhes da OP
            </button>
            {canOpenVisual ? (
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--primary"
                onClick={() =>
                  onOpenVisual({
                    paCode: paCode || null,
                    productCode: productCode || null,
                    has3dModel,
                  })
                }
              >
                <Eye size={18} strokeWidth={2} aria-hidden="true" />
                {visualLabel}
              </button>
            ) : null}
          </div>
        </div>
      </article>
    </section>
  );
}

function UpcomingRow({
  entry,
  isNext,
  onOpenDetail,
}: {
  entry: QueueEntry;
  isNext: boolean;
  onOpenDetail: () => void;
}) {
  const { operation, position } = entry;
  const status = resolveStatus(operation);
  const pendingQty = operationPendingQty(operation);
  const { paCode, displayProductCode } = resolveVisualMeta(operation);
  const seqLabel = String(position).padStart(2, "0");

  return (
    <tr
      className={[
        "pcp-pub__queue-row",
        isNext ? "pcp-pub__queue-row--next" : "",
        status.tone === "done" ? "pcp-pub__queue-row--done" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <td className="pcp-pub__queue-seq">
        <span className="pcp-pub__queue-seq-num">{seqLabel}</span>
        {isNext ? <span className="pcp-pub__queue-seq-tag">Próxima</span> : null}
      </td>
      <td>
        <div className="pcp-pub__queue-op">
          <strong>{operation.production_order}</strong>
          <span>
            <span className={paCode ? "pcp-pub__product-code--pa" : undefined}>
              {displayProductCode}
            </span>{" "}
            {operation.product_description}
          </span>
        </div>
      </td>
      <td>
        <div className="pcp-pub__queue-op-meta">
          <span>
            {operation.operation_code} · {operation.operation_description}
          </span>
          {operation.tool ? <span>Ferramenta {operation.tool}</span> : null}
        </div>
      </td>
      <td className="pcp-pub__num">
        {formatQty(pendingQty)} {formatUnit(operation.unit, pendingQty)}
      </td>
      <td className="pcp-pub__num">
        <div className="pcp-pub__queue-op-meta">
          <span>{formatDate(operation.scheduled_date)}</span>
          {operation.scheduled_start_time ? <span>{operation.scheduled_start_time}</span> : null}
        </div>
      </td>
      <td className="pcp-pub__num">{formatDate(operation.pa_due_date)}</td>
      <td>
        <button type="button" className="pcp-pub__link-btn" onClick={onOpenDetail}>
          Detalhes
        </button>
      </td>
    </tr>
  );
}

function DowntimeItemsModal({
  shiftLabel,
  hours,
  state,
  onClose,
}: {
  shiftLabel: string;
  hours: number | null;
  state: PublicWorkCenterDowntimeItemsState;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const { data, loading, error } = state;
  const items = data?.items ?? [];
  const count = data?.summary.appointment_count ?? items.length;
  const totalHours = data?.summary.total_hours ?? hours;

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-downtime-title"
    >
      <button type="button" className="pcp-pub-modal__backdrop" aria-label="Fechar" onClick={onClose} />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--downtime">
        <header className="pcp-pub-modal__head">
          <h2 id="pcp-pub-downtime-title">Paradas · {shiftLabel.toLowerCase()}</h2>
          <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
            Fechar
          </button>
        </header>

        <p className="pcp-pub-modal__lede">Apontamentos de hoje neste posto, só no turno atual.</p>

        <dl className="pcp-pub__facts pcp-pub__facts--num">
          <div className="pcp-pub__fact">
            <dt>Registros</dt>
            <dd>{loading ? "…" : count}</dd>
          </div>
          <div className="pcp-pub__fact">
            <dt>Total</dt>
            <dd>{loading ? "…" : formatHours(totalHours)}</dd>
          </div>
        </dl>

        {loading ? (
          <p className="pcp-pub-modal__empty">Carregando paradas…</p>
        ) : error ? (
          <p className="pcp-pub-modal__empty">{error}</p>
        ) : items.length > 0 ? (
          <div className="pcp-pub-modal__table-wrap">
            <table className="pcp-pub-modal__table">
              <thead>
                <tr>
                  <th scope="col">Motivo</th>
                  <th scope="col">Horas</th>
                  <th scope="col">Observação</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row, index) => {
                  const reason =
                    row.stop_reason_description?.trim() ||
                    row.stop_reason?.trim() ||
                    "Sem motivo";
                  const reasonCode = row.stop_reason?.trim();
                  return (
                    <tr
                      key={`${row.reference_date}-${row.production_order}-${row.stop_reason}-${index}`}
                    >
                      <td>
                        <div className="pcp-pub-modal__reason">
                          <span className="pcp-pub-modal__reason-label">{reason}</span>
                          {reasonCode && reasonCode !== reason ? (
                            <span className="pcp-pub-modal__reason-code">{reasonCode}</span>
                          ) : null}
                        </div>
                      </td>
                      <td className="pcp-pub__num">{formatHours(row.hours)}</td>
                      <td className="pcp-pub-modal__observation">
                        {row.observation?.trim() || "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="pcp-pub-modal__empty">Nenhuma parada apontada neste turno hoje.</p>
        )}
      </div>
    </div>
  );
}
