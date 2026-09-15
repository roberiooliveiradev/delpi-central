import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent } from "react";
import { Search } from "lucide-react";
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
  operationKey,
  resolveStatus,
} from "./cockpitShared";
import { OperationDetailPage } from "./OperationDetailPage";
import { usePublicMachineLoadRealtime } from "./usePublicMachineLoadRealtime";
import { useCockpitView } from "./useCockpitView";
import { useWorkCenterPerformance } from "./useWorkCenterPerformance";
import { WorkCenterPerformancePage } from "./WorkCenterPerformancePage";
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

type Props = {
  token: string;
  branch: string;
  initial: PublicMachineLoadPayload;
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
  const [visualTarget, setVisualTarget] = useState<{
    paCode: string | null;
    productCode: string | null;
    has3dModel: boolean;
  } | null>(null);
  const [queueQuery, setQueueQuery] = useState("");
  const workCenterRef = useRef(workCenter);
  workCenterRef.current = workCenter;
  const reloadGenerationRef = useRef(0);
  const { view, openQueue, openOperation, openPerformance } = useCockpitView();

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
  const items =
    workCenter && payload.selected.work_center === workCenter ? payload.selected.items : [];

  const filteredItems = useMemo(() => {
    const term = queueQuery.trim().toLowerCase();
    if (!term) return items.map((operation, index) => ({ operation, position: index + 1 }));
    return items
      .map((operation, index) => ({ operation, position: index + 1 }))
      .filter(({ operation }) => matchesQueueSearch(operation, term));
  }, [items, queueQuery]);

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

  const running = activeCenter?.in_production_count ?? 0;
  const efficiency = performance.data?.efficiency;
  const downtime = performance.data?.downtime;
  const shiftPct = efficiency?.available ? efficiency.shift_pct : null;
  const shiftLabel = performance.data?.shift?.label ?? "Turno";

  return (
    <section className="pcp-pub">
      <BrandBar
        eyebrow={`Fila de produção · Filial ${branch}`}
        title={activeCenter?.work_center_name || workCenter}
        code={workCenter}
        stats={
          <>
            <span className="pcp-pub__chip">
              {items.length} {items.length === 1 ? "operação" : "operações"}
            </span>
            {running ? (
              <span className="pcp-pub__chip pcp-pub__chip--running">{running} em produção</span>
            ) : null}
            <button
              type="button"
              className={`pcp-pub__chip pcp-pub__chip--metric pcp-pub__chip--eff-${efficiencyTone(
                shiftPct,
              )}`}
              onClick={openPerformance}
              title={`Eficiência do posto no ${shiftLabel.toLowerCase()}`}
            >
              <span className="pcp-pub__chip-label">{shiftLabel}</span>
              <strong>{formatPercent(shiftPct)}</strong>
            </button>
            <button
              type="button"
              className="pcp-pub__chip pcp-pub__chip--metric"
              onClick={openPerformance}
              title="Paradas apontadas hoje neste posto"
            >
              <span className="pcp-pub__chip-label">Paradas hoje</span>
              <strong>{downtime?.available ? formatHours(downtime.today_hours) : "—"}</strong>
            </button>
          </>
        }
        actions={
          <>
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
            <button type="button" className="pcp-pub__ghost" onClick={openPerformance}>
              Ver desempenho
            </button>
            <button type="button" className="pcp-pub__ghost" onClick={clearWorkCenter}>
              Trocar posto
            </button>
          </>
        }
      />

      <div className="pcp-pub__wrap">
        <label className="pcp-pub__search-field">
          <Search className="pcp-pub__search-icon" size={20} strokeWidth={2} aria-hidden="true" />
          <input
            className="pcp-pub__search"
            type="search"
            value={queueQuery}
            onChange={(event) => setQueueQuery(event.target.value)}
            placeholder="Buscar OP ou PA…"
            aria-label="Buscar operação por OP ou PA"
            autoComplete="off"
            enterKeyHint="search"
          />
        </label>

        {error ? <p className="pcp-pub__error">{error}</p> : null}

        {items.length === 0 ? (
          <p className="pcp-pub__empty">
            {loading ? "Carregando fila…" : "Nenhuma operação programada para este posto."}
          </p>
        ) : filteredItems.length === 0 ? (
          <p className="pcp-pub__empty">Nenhuma operação encontrada para “{queueQuery.trim()}”.</p>
        ) : (
          <>
            <div className="pcp-pub__queue-head" aria-hidden="true">
              <span className="pcp-pub__position pcp-pub__position--ghost">#</span>
              <div className="pcp-pub__row">
                <span>OP / Produto</span>
                <span>Operação</span>
                <span>Pendente</span>
                <span>Programada</span>
                <span>Entrega</span>
                <span className="pcp-pub__row-end">Status</span>
              </div>
            </div>

            <ol className="pcp-pub__queue">
              {filteredItems.map(({ operation, position }) => (
                <OperationCard
                  key={operationKey(operation)}
                  position={position}
                  operation={operation}
                  onOpenVisual={setVisualTarget}
                  onOpenDetail={() =>
                    openOperation(operation.production_order, operation.operation_code)
                  }
                />
              ))}
            </ol>
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
    </section>
  );
}

type PickerProps = {
  branch: string;
  workCenters: MachineLoadWorkCenter[];
  onSelect: (workCenter: string) => void;
};

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

function OperationCard({
  position,
  operation,
  onOpenVisual,
  onOpenDetail,
}: {
  position: number;
  operation: MachineLoadOperation;
  onOpenVisual: (target: {
    paCode: string | null;
    productCode: string | null;
    has3dModel: boolean;
  }) => void;
  onOpenDetail: () => void;
}) {
  const status = resolveStatus(operation);
  const paCode = operation.pa_product_code?.trim() || "";
  const productCode = operation.product_code?.trim() || "";
  const has3dModel = Boolean(operation.has_3d_model && productCode);
  const canOpenVisual = Boolean(paCode) || has3dModel;
  const visualLabel =
    paCode && has3dModel ? "Ver desenho / 3D" : has3dModel ? "Ver 3D" : "Ver desenho";
  // No chão de fábrica o operador lê o PA; o intermediário fica só como fallback.
  const displayProductCode = paCode || operation.product_code;

  // Alvo de toque grande no tablet: o card inteiro abre o detalhe, exceto sobre os botões.
  const openFromCard = (event: MouseEvent<HTMLLIElement>) => {
    if ((event.target as HTMLElement).closest("button")) return;
    onOpenDetail();
  };

  return (
    <li className={`pcp-pub__card pcp-pub__card--${status.tone}`} onClick={openFromCard}>
      <span className="pcp-pub__position" aria-label={`Posição ${position}`}>
        {position}
      </span>

      <div className="pcp-pub__row">
        <div className="pcp-pub__cell pcp-pub__cell--order">
          <span className="pcp-pub__order">
            <span className="pcp-pub__order-label">OP</span>
            <strong>{operation.production_order}</strong>
            <CopyValueButton value={operation.production_order} label="Copiar OP" />
          </span>
          <p className="pcp-pub__product">
            <strong className={paCode ? "pcp-pub__product-code--pa" : undefined}>
              {displayProductCode}
            </strong>{" "}
            {operation.product_description}
          </p>
        </div>

        <div className="pcp-pub__cell">
          <span className="pcp-pub__cell-label">Operação</span>
          <span className="pcp-pub__cell-value">
            {operation.operation_code} · {operation.operation_description}
          </span>
          {operation.tool ? (
            <span className="pcp-pub__cell-sub">Ferramenta {operation.tool}</span>
          ) : null}
        </div>

        <div className="pcp-pub__cell">
          <span className="pcp-pub__cell-label">Pendente</span>
          <span className="pcp-pub__cell-value pcp-pub__num">
            {formatQty(operation.pending_qty)} {formatUnit(operation.unit)}
          </span>
        </div>

        <div className="pcp-pub__cell">
          <span className="pcp-pub__cell-label">Programada</span>
          <span className="pcp-pub__cell-value pcp-pub__num">
            {formatDate(operation.scheduled_date)}
          </span>
          {operation.scheduled_start_time ? (
            <span className="pcp-pub__cell-sub">{operation.scheduled_start_time}</span>
          ) : null}
        </div>

        <div className="pcp-pub__cell">
          <span className="pcp-pub__cell-label">Entrega</span>
          <span className="pcp-pub__cell-value pcp-pub__num">
            {formatDate(operation.pa_due_date)}
          </span>
        </div>

        <div className="pcp-pub__cell pcp-pub__cell--status">
          <span className={`pcp-pub__badge pcp-pub__badge--${status.tone}`}>
            {status.tone === "running" ? (
              <span className="pcp-pub__badge-dot" aria-hidden="true" />
            ) : null}
            {status.label}
          </span>
          {status.operatorNote ? (
            <span className="pcp-pub__operator">{status.operatorNote}</span>
          ) : null}
          <span className="pcp-pub__card-actions">
            <button type="button" className="pcp-pub__drawing" onClick={onOpenDetail}>
              Detalhes
            </button>
            {canOpenVisual ? (
              <button
                type="button"
                className="pcp-pub__drawing pcp-pub__drawing--muted"
                onClick={() =>
                  onOpenVisual({
                    paCode: paCode || null,
                    productCode: productCode || null,
                    has3dModel,
                  })
                }
              >
                {visualLabel}
              </button>
            ) : null}
          </span>
        </div>
      </div>
    </li>
  );
}
