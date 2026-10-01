import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent, ReactNode } from "react";
import { BarChart3, Eye, MoreVertical, RefreshCw, Search, User } from "lucide-react";
import {
  fetchActiveProductionRun,
  fetchPublicMachineLoad,
  stopProductionRun,
  type MachineLoadOperation,
  type MachineLoadWorkCenter,
  type ProductionRunSnapshot,
  type PublicMachineLoadPayload,
} from "./api.ts";
import {
  BrandBar,
  CopyValueButton,
  DrawingViewer,
  formatDate,
  formatDateTime,
  formatHours,
  formatQty,
  formatUnit,
  operationKey,
  operationPendingQty,
  resolveStatus,
  WorkCenterShiftMetrics,
  type StatusView,
} from "./cockpitShared";
import { OperationDetailPage } from "./OperationDetailPage";
import {
  OperatorSessionChip,
  OperatorSessionProvider,
} from "./OperatorSessionProvider";
import { ProductionRunControls } from "./ProductionRunControls";
import { useOperatorSession } from "./OperatorSessionContext.ts";
import {
  usePublicMachineLoadRealtime,
  type MachineLoadRealtimeEvent,
} from "./usePublicMachineLoadRealtime.ts";
import { useCockpitView } from "./useCockpitView.ts";
import { useWorkCenterPerformance } from "./useWorkCenterPerformance.ts";
import { usePublicWorkCenterDowntimeItems } from "./usePublicWorkCenterDowntimeItems.ts";
import { WorkCenterPerformancePage } from "./WorkCenterPerformancePage";
import type { PublicWorkCenterDowntimeItemsState } from "./usePublicWorkCenterDowntimeItems.ts";
import "./cockpit.css";

function matchesQueueSearch(operation: MachineLoadOperation, term: string): boolean {
  if (!term) return true;
  const op = operation.production_order.toLowerCase();
  const pa = (operation.pa_product_code || "").toLowerCase();
  const product = (operation.product_code || "").toLowerCase();
  return op.includes(term) || pa.includes(term) || product.includes(term);
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
  const [runUpdatedSignal, setRunUpdatedSignal] = useState(0);
  // Run ativo no contador Pulse deste posto — decide o card "Agora nesta bancada".
  const [counterRun, setCounterRun] = useState<ProductionRunSnapshot | null>(null);
  const [runRealtimeEvent, setRunRealtimeEvent] = useState<MachineLoadRealtimeEvent | null>(null);
  const workCenterRef = useRef(workCenter);
  workCenterRef.current = workCenter;
  const reloadGenerationRef = useRef(0);
  const { view, openQueue, openOperation, openPerformance } = useCockpitView();

  useEffect(() => {
    setDowntimeOpen(false);
  }, [workCenter]);

  // Apaga preferência legada dos aparelhos: a fila já chega pronta do backend.
  useEffect(() => {
    try {
      for (const key of Object.keys(window.localStorage)) {
        if (key.startsWith(HIDE_FINISHED_PREFIX)) window.localStorage.removeItem(key);
      }
    } catch {
      /* storage indisponível: nada a limpar */
    }
  }, []);

  const reload = useCallback(
    async (center: string | null, options?: { quiet?: boolean }) => {
      const quiet = options?.quiet === true;
      const generation = ++reloadGenerationRef.current;
      if (!quiet) setLoading(true);
      try {
        const [next, activeRun] = await Promise.all([
          fetchPublicMachineLoad(token, branch, center),
          center
            ? fetchActiveProductionRun(token, branch, center).catch(() => null)
            : Promise.resolve(null),
        ]);
        if (generation !== reloadGenerationRef.current) return;
        setPayload(next);
        setCounterRun(activeRun);
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
    onChanged: useCallback((event: MachineLoadRealtimeEvent) => {
      if (event.type === "production_run_updated" && event.reason === "pieces_updated") {
        setRunRealtimeEvent(event);
        return;
      }
      if (
        event.type === "production_run_updated" &&
        (event.reason.startsWith("run_") ||
          event.reason.startsWith("automatic_downtime_") ||
          event.reason === "downtime_classified")
      ) {
        setRunRealtimeEvent(event);
        setRunUpdatedSignal((value) => value + 1);
      }
      // Sequência/refresh do PCP: atualiza sem flicker de loading.
      void reload(workCenterRef.current, { quiet: true });
    }, [reload]),
    onDisconnected: useCallback(() => {
      setRunRealtimeEvent(null);
    }, []),
    onReconnected: useCallback(() => {
      setRunRealtimeEvent(null);
      setRunUpdatedSignal((value) => value + 1);
    }, []),
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

  const activeCenter = payload.work_centers.find((item) => item.work_center === workCenter);
  const items = useMemo(
    () =>
      workCenter && payload.selected.work_center === workCenter
        ? payload.selected.items
        : [],
    [workCenter, payload.selected.work_center, payload.selected.items],
  );

  const activeEntry = useMemo<QueueEntry | null>(() => {
    if (items.length === 0) return null;
    // Regra: "Agora nesta bancada" é sempre a operação do run ativo no
    // contador (Pulse/MES). Sem run ativo na fila, cai no topo da fila —
    // cronômetro aberto no TOTVS não disputa o destaque do cockpit.
    const counterOperation = counterRun
      ? items.find(
          (item) =>
            item.production_order === counterRun.productionOrder &&
            item.operation_code === counterRun.operationCode,
        )
      : null;
    const operation = counterOperation ?? items[0]!;
    const position = items.findIndex((item) => operationKey(item) === operationKey(operation)) + 1;
    return { operation, position: Math.max(1, position) };
  }, [items, counterRun]);

  const orphanRun = useMemo(() => {
    if (!counterRun) return null;
    const inQueue = items.some(
      (item) =>
        item.production_order === counterRun.productionOrder &&
        item.operation_code === counterRun.operationCode,
    );
    return inQueue ? null : counterRun;
  }, [counterRun, items]);

  const upcomingEntries = useMemo(() => {
    const term = queueQuery.trim().toLowerCase();
    const activeKey = activeEntry ? operationKey(activeEntry.operation) : null;
    return items
      .map((operation) => {
        const position = items.findIndex((item) => operationKey(item) === operationKey(operation)) + 1;
        return { operation, position: Math.max(1, position) };
      })
      .filter(({ operation }) => operationKey(operation) !== activeKey)
      .filter(({ operation }) => matchesQueueSearch(operation, term));
  }, [items, queueQuery, activeEntry]);

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

  const centerName = activeCenter?.work_center_name || workCenter;
  const efficiency = performance.data?.efficiency;
  const downtime = performance.data?.downtime;
  const shiftPct = efficiency?.available ? efficiency.shift_pct : null;
  const shiftProducedQty = efficiency?.available ? efficiency.shift_produced_qty : null;
  const shiftLabel = performance.data?.shift?.label ?? "Turno";
  const downtimeHours = downtime?.available ? downtime.today_hours : null;
  const downtimeAvailable = Boolean(downtime?.available);
  const shiftMetrics = (
    <WorkCenterShiftMetrics
      shiftLabel={shiftLabel}
      shiftPct={shiftPct}
      shiftProducedQty={shiftProducedQty}
      downtimeHours={downtimeHours}
      downtimeAvailable={downtimeAvailable}
      onOpenPerformance={openPerformance}
      onOpenDowntime={() => setDowntimeOpen(true)}
    />
  );
  const downtimeModal = downtimeOpen ? (
    <DowntimeItemsModal
      shiftLabel={shiftLabel}
      hours={downtimeHours}
      state={downtimeItems}
      onClose={() => setDowntimeOpen(false)}
    />
  ) : null;

  let content: ReactNode;

  if (view.kind === "performance") {
    content = (
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
  } else if (view.kind === "operation" && selectedOperation) {
    const index = selectedOperation.position - 1;
    // selected.items é open-only: o vizinho é simplesmente o adjacente.
    const previous = items[index - 1];
    const next = items[index + 1];

    content = (
      <>
        <OperationDetailPage
          key={operationKey(selectedOperation.operation)}
          token={token}
          branch={branch}
          operation={selectedOperation.operation}
          position={selectedOperation.position}
          queueSize={items.length}
          workCenter={workCenter}
          workCenterName={centerName}
          shiftLabel={shiftLabel}
          shiftPct={shiftPct}
          shiftProducedQty={shiftProducedQty}
          downtimeHours={downtimeHours}
          downtimeAvailable={downtimeAvailable}
          runUpdatedSignal={runUpdatedSignal}
          runRealtimeEvent={runRealtimeEvent}
          realtimeConnected={connected}
          hasActiveRun={Boolean(counterRun)}
          onOpenPerformance={openPerformance}
          onOpenDowntime={() => setDowntimeOpen(true)}
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
        {downtimeModal}
      </>
    );
  } else {
    content = (
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
              <CockpitActionsMenu
                onOpenPerformance={openPerformance}
                onClearWorkCenter={clearWorkCenter}
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
            {shiftMetrics}
            <div className="pcp-pub__hero-aside">
              <OperatorSessionChip hasActiveRun={Boolean(counterRun)} />
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

        {orphanRun ? (
          <OrphanRunCard
            run={orphanRun}
            token={token}
            onStopped={() => void reload(workCenterRef.current, { quiet: true })}
          />
        ) : null}

        {items.length === 0 ? (
          <p className="pcp-pub__empty">
            {loading
              ? "Carregando fila…"
              : "Nenhuma ordem pendente para este posto."}
          </p>
        ) : (
          <>
            {activeEntry && workCenter ? (
              <ActiveNowCard
                entry={activeEntry}
                token={token}
                branch={branch}
                workCenter={workCenter}
                counterActive={Boolean(
                  counterRun &&
                    counterRun.productionOrder === activeEntry.operation.production_order &&
                    counterRun.operationCode === activeEntry.operation.operation_code,
                )}
                runUpdatedSignal={runUpdatedSignal}
                runRealtimeEvent={runRealtimeEvent}
                realtimeConnected={connected}
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
                        <th scope="col">PA</th>
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

      {downtimeModal}
      </section>
    );
  }

  return (
    <OperatorSessionProvider token={token} branch={branch} workCenter={workCenter}>
      {content}
    </OperatorSessionProvider>
  );
}

type PickerProps = {
  branch: string;
  workCenters: MachineLoadWorkCenter[];
  onSelect: (workCenter: string) => void;
};

function CockpitActionsMenu({
  onOpenPerformance,
  onClearWorkCenter,
}: {
  onOpenPerformance: () => void;
  onClearWorkCenter: () => void;
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
  token,
  branch,
  workCenter,
  counterActive = false,
  runUpdatedSignal,
  runRealtimeEvent,
  realtimeConnected,
  onOpenVisual,
  onOpenDetail,
}: {
  entry: QueueEntry;
  token: string;
  branch: string;
  workCenter: string;
  counterActive?: boolean;
  runUpdatedSignal: number;
  runRealtimeEvent: MachineLoadRealtimeEvent | null;
  realtimeConnected: boolean;
  onOpenVisual: (target: VisualTarget) => void;
  onOpenDetail: () => void;
}) {
  const { operation } = entry;
  const baseStatus = resolveStatus(operation);
  // Ativa no contador mesmo sem apontamento TOTVS em aberto: ainda é a
  // operação em produção nesta bancada.
  const status: StatusView =
    counterActive && baseStatus.tone !== "running"
      ? {
          tone: "running",
          label: "Em produção",
          operatorNote: baseStatus.operatorNote ?? "Contagem ativa neste posto",
        }
      : baseStatus;
  const pendingQty = operationPendingQty(operation);
  const { paCode, productCode, has3dModel, canOpenVisual, visualLabel, displayProductCode } =
    resolveVisualMeta(operation);

  const openFromCard = (event: MouseEvent<HTMLElement>) => {
    if ((event.target as HTMLElement).closest("button, input, form, .pcp-pub__run")) return;
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

        <ProductionRunControls
          token={token}
          branch={branch}
          workCenter={workCenter}
          operation={operation}
          runUpdatedSignal={runUpdatedSignal}
          runRealtimeEvent={runRealtimeEvent}
          realtimeConnected={realtimeConnected}
        />
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
  const { operation } = entry;
  const pendingQty = operationPendingQty(operation);
  const { paCode, displayProductCode } = resolveVisualMeta(operation);

  return (
    <tr
      className={[
        "pcp-pub__queue-row",
        isNext ? "pcp-pub__queue-row--next" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <td className="pcp-pub__queue-seq">
        <span
          className={
            paCode
              ? "pcp-pub__queue-seq-pa pcp-pub__product-code--pa"
              : "pcp-pub__queue-seq-pa"
          }
        >
          {displayProductCode || "—"}
        </span>
        {isNext ? <span className="pcp-pub__queue-seq-tag">Próxima</span> : null}
      </td>
      <td>
        <div className="pcp-pub__queue-op">
          <strong>{operation.production_order}</strong>
          <span>{operation.product_description}</span>
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

/** Run aberto cuja OP saiu da fila publicada (apontada/retirada no TOTVS).
 * Sem este card o run ficaria invisível e bloquearia a troca de operador —
 * aqui o posto sempre consegue encerrar a produção órfã. */
function OrphanRunCard({
  run,
  token,
  onStopped,
}: {
  run: ProductionRunSnapshot;
  token: string;
  onStopped: () => void;
}) {
  const { session } = useOperatorSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stop = async () => {
    if (!session?.sessionToken) {
      setError("Identifique-se no posto para encerrar a produção.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await stopProductionRun(token, session.sessionToken, run.id);
      onStopped();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível encerrar a produção.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="pcp-pub__now" aria-labelledby="pcp-pub-orphan-title">
      <div className="pcp-pub__now-head">
        <h3 id="pcp-pub-orphan-title">Produção em andamento</h3>
        <span className="pcp-pub__badge pcp-pub__badge--running">
          <span className="pcp-pub__badge-dot" aria-hidden="true" />
          {run.status === "paused" ? "Pausada" : "Em produção"}
        </span>
      </div>
      <article className="pcp-pub__now-card pcp-pub__now-card--running">
        <div className="pcp-pub__now-main">
          <div className="pcp-pub__now-identity">
            <div className="pcp-pub__now-order">
              <strong>{run.productionOrder}</strong>
              <CopyValueButton value={run.productionOrder} label="Copiar OP" />
            </div>
            <p className="pcp-pub__now-product">
              Operação {run.operationCode}
              {run.operatorName ? ` · ${run.operatorName}` : ""}
            </p>
          </div>
        </div>
        <p className="pcp-pub__run-note">
          Esta OP saiu da fila deste posto. Encerre a produção para liberar a troca de operador.
        </p>
        {error ? <p className="pcp-pub__run-error">{error}</p> : null}
        <div className="pcp-pub__run-actions">
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--primary"
            onClick={() => void stop()}
            disabled={busy}
          >
            {busy ? "Encerrando…" : "Encerrar produção"}
          </button>
        </div>
      </article>
    </section>
  );
}
