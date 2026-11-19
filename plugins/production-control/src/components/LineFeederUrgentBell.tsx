import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { Bell, Loader2, PackageCheck, PackageSearch } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchLineFeederUrgentRequests,
  fetchLatestMyWegNeedBatch,
  patchLineFeederUrgentRequest,
} from "../api/ppcApi";
import { copy } from "../content/copy";
import type { LineFeederUrgentRequest, MyWegNeedsBatchSummary, PpcBranch } from "../types";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";

const POLL_MS = 30_000;

type Props = {
  branch: PpcBranch;
  canViewUrgent?: boolean;
  canViewMyWeg?: boolean;
};

/**
 * Sino de urgentes no header do Alimentador (C5).
 * Substitui o card de página — mesma fila, superfície compacta em popover.
 */
export function LineFeederUrgentBell({ branch, canViewUrgent = true, canViewMyWeg = false }: Props) {
  const labels = copy.lineFeeder.urgent;
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<LineFeederUrgentRequest[]>([]);
  const [summary, setSummary] = useState({ total: 0, pending: 0, picked: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [qualityBatch, setQualityBatch] = useState<MyWegNeedsBatchSummary | null>(null);
  const [qualityError, setQualityError] = useState<string | null>(null);
  const requestSeq = useRef(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    if (!canViewUrgent) {
      setItems([]);
      setSummary({ total: 0, pending: 0, picked: 0 });
      setLoading(false);
      return;
    }
    const seq = ++requestSeq.current;
    setLoading(true);
    try {
      const payload = await fetchLineFeederUrgentRequests({ branch });
      if (seq !== requestSeq.current) return;
      setItems(payload.items);
      setSummary(payload.summary);
      setError(null);
    } catch (err: unknown) {
      if (seq !== requestSeq.current) return;
      setError(err instanceof Error ? err.message : labels.loadError);
    } finally {
      if (seq === requestSeq.current) setLoading(false);
    }
  }, [branch, canViewUrgent, labels.loadError]);

  useEffect(() => {
    queueMicrotask(() => {
      setItems([]);
      void load();
    });
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      void load();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  useEffect(() => {
    if (!canViewMyWeg || branch !== "02") {
      queueMicrotask(() => {
        setQualityBatch(null);
        setQualityError(null);
      });
      return;
    }
    let active = true;
    const refresh = async () => {
      try {
        const batch = await fetchLatestMyWegNeedBatch();
        if (active) {
          setQualityBatch(batch.quality?.excludedCount ? batch : null);
          setQualityError(null);
        }
      } catch (err: unknown) {
        if (active) {
          // Sem lote aceito ainda: painel sem avisos, sem expor detalhes da API.
          setQualityError(err instanceof Error ? err.message : "Falha ao consultar MyWEG.");
        }
      }
    };
    void refresh();
    const timer = window.setInterval(() => {
      if (document.visibilityState !== "hidden") void refresh();
    }, 60_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [branch, canViewMyWeg]);

  const update = async (
    item: LineFeederUrgentRequest,
    status: "picked" | "delivered",
  ) => {
    if (busyId) return;
    setBusyId(item.id);
    setError(null);
    try {
      await patchLineFeederUrgentRequest({
        branch,
        materialId: item.id,
        status,
      });
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : labels.updateError);
      void load();
    } finally {
      setBusyId(null);
    }
  };

  const count = (canViewUrgent ? summary.total : 0) + (qualityBatch ? 1 : 0);
  const hasUrgent = count > 0;
  const bellLabel = `Avisos do Portal PCP${count ? ` (${count})` : ""}`;

  return (
    <div
      ref={rootRef}
      className={`ppc-feeder-urgent-bell${open ? " is-open" : ""}${
        hasUrgent ? " has-items" : ""
      }`}
    >
      <button
        type="button"
        className="ppc-icon-btn ppc-feeder-urgent-bell__trigger"
        aria-label={bellLabel}
        aria-haspopup="dialog"
        aria-expanded={open}
        title={bellLabel}
        onClick={() => setOpen((current) => !current)}
      >
        <Bell size={16} strokeWidth={1.75} aria-hidden />
        {hasUrgent ? (
          <span className="ppc-feeder-urgent-bell__badge" aria-hidden="true">
            {count > 99 ? "99+" : count}
          </span>
        ) : null}
      </button>

      <AnchoredPanelPortal
        open={open}
        anchorRef={rootRef}
        panelRef={panelRef}
        className="ppc-feeder-urgent-bell__panel"
        variant="bare"
        role="dialog"
        aria-label="Avisos operacionais do Portal PCP"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={8}
        portalScopeClassName="dashboard-production-control"
        onDismiss={() => setOpen(false)}
      >
        <header className="ppc-feeder-urgent-bell__head">
          <h3 className="ppc-feeder-urgent-bell__title">Avisos do Portal PCP</h3>
          <p className="ppc-feeder-urgent-bell__hint">Pendências da integração e solicitações operacionais.</p>
        </header>

        {qualityBatch?.quality ? (
          <section className="ppc-feeder-urgent-bell__item" aria-label="Pendências de integração MyWEG">
            <p className="ppc-feeder-urgent-bell__item-title">
              <strong>MyWEG: coleta com pendências</strong>
            </p>
            <p className="ppc-feeder-urgent-bell__meta">
              {qualityBatch.collectionDate}: {qualityBatch.quality.excludedCount} registros
              sem identificação de material ({qualityBatch.quality.excludedQuantityUn} UN).
              Não computados na demanda por produto.
            </p>
            <p className="ppc-feeder-urgent-bell__meta">
              Linhas de origem: {qualityBatch.quality.excludedRecords
                .map((item) => item.sourceLine || String(item.index + 1))
                .join(", ")}
            </p>
            <a className="ppc-feeder-urgent-bell__action" href="/apps/production-control/myweg-needs?branch=02">
              Abrir Necessidades WEG
            </a>
          </section>
        ) : null}

        {qualityError && !qualityBatch ? (
          <p className="ppc-state ppc-state--error" role="status">{qualityError}</p>
        ) : null}

        {error ? (
          <p className="ppc-state ppc-state--error" role="alert">
            {error}
          </p>
        ) : null}

        {!canViewUrgent ? (
          !qualityBatch && !qualityError ? <p className="ppc-feeder-urgent-bell__empty">Nenhum aviso ativo.</p> : null
        ) : loading && items.length === 0 ? (
          <p className="ppc-feeder-urgent-bell__empty" role="status">
            <Loader2 className="ppc-icon-btn__spin" size={15} aria-hidden />
            {labels.loading}
          </p>
        ) : items.length === 0 ? (
          !qualityBatch ? <p className="ppc-feeder-urgent-bell__empty">{labels.empty}</p> : null
        ) : (
          <ul className="ppc-feeder-urgent-bell__list">
            {items.map((item) => {
              const picked = item.status === "picked";
              const busy = busyId === item.id;
              return (
                <li
                  key={item.id}
                  className={
                    "ppc-feeder-urgent-bell__item" + (picked ? " is-picked" : "")
                  }
                >
                  <div className="ppc-feeder-urgent-bell__body">
                    <p className="ppc-feeder-urgent-bell__item-title">
                      <strong>{item.productCode}</strong>
                      {item.description ? <span>{item.description}</span> : null}
                      <span
                        className={
                          "ppc-feeder-urgent-bell__status" +
                          (picked ? " is-picked" : "")
                        }
                      >
                        {picked ? labels.pickedBadge : labels.pendingBadge}
                      </span>
                    </p>
                    <p className="ppc-feeder-urgent-bell__meta">
                      <span>
                        {labels.orderLabel(item.productionOrder, item.operationCode)}
                      </span>
                      <span>{labels.reportedCenter(item.reportedWorkCenter)}</span>
                      {item.currentWorkCenter &&
                      item.currentWorkCenter !== item.reportedWorkCenter ? (
                        <span>{labels.currentCenter(item.currentWorkCenter)}</span>
                      ) : null}
                      {item.outOfQueue ? (
                        <span className="ppc-feeder-urgent-bell__out">
                          {labels.outOfQueue}
                        </span>
                      ) : null}
                    </p>
                    <p className="ppc-feeder-urgent-bell__meta">
                      <span>
                        {labels.reportedBy(item.operatorName, item.operatorCode)}
                      </span>
                      <span>
                        {labels.reportedAt(formatRefreshedAt(item.reportedAt))}
                      </span>
                      <span>{labels.balanceLabel(item.openQty, item.unit)}</span>
                    </p>
                    {item.note ? (
                      <p className="ppc-feeder-urgent-bell__note">
                        <strong>{labels.noteLabel}: </strong>
                        {item.note}
                      </p>
                    ) : null}
                  </div>
                  <div className="ppc-feeder-urgent-bell__actions">
                    {picked ? (
                      <button
                        type="button"
                        className="ppc-feeder-urgent-bell__action ppc-feeder-urgent-bell__action--deliver"
                        disabled={busy || busyId !== null}
                        aria-busy={busy}
                        onClick={() => void update(item, "delivered")}
                      >
                        <PackageCheck size={14} strokeWidth={1.9} aria-hidden />
                        {busy ? labels.markDeliveredBusy : labels.markDelivered}
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="ppc-feeder-urgent-bell__action"
                        disabled={busy || busyId !== null}
                        aria-busy={busy}
                        onClick={() => void update(item, "picked")}
                      >
                        <PackageSearch size={14} strokeWidth={1.9} aria-hidden />
                        {busy ? labels.startPickingBusy : labels.startPicking}
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </AnchoredPanelPortal>
    </div>
  );
}
