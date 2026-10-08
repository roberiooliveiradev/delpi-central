import { useCallback, useEffect, useRef, useState } from "react";
import { Flame, Loader2, PackageCheck, PackageSearch } from "lucide-react";

import {
  fetchLineFeederUrgentRequests,
  patchLineFeederUrgentRequest,
} from "../api/ppcApi";
import { copy } from "../content/copy";
import type { LineFeederUrgentRequest, PpcBranch } from "../types";
import { formatRefreshedAt } from "../utils/formatRefreshedAt";

const POLL_MS = 30_000;

type Props = {
  branch: PpcBranch;
};

/**
 * Fila urgente do Alimentador (C5): materiais que o operador marcou como
 * faltantes via Operator Feedback. Convive com as pick lists planejadas —
 * nunca se mistura a elas. delivered sai da fila ativa; feedback resolvido
 * pelo PCP também sai (o backend filtra).
 */
export function LineFeederUrgentRequestsPanel({ branch }: Props) {
  const labels = copy.lineFeeder.urgent;
  const [items, setItems] = useState<LineFeederUrgentRequest[]>([]);
  const [summary, setSummary] = useState({ total: 0, pending: 0, picked: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const requestSeq = useRef(0);

  const load = useCallback(async () => {
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
  }, [branch, labels.loadError]);

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

  return (
    <section
      className="ppc-feeder-urgent"
      aria-labelledby="ppc-feeder-urgent-title"
    >
      <div className="ppc-feeder-urgent__head">
        <h3 id="ppc-feeder-urgent-title" className="ppc-feeder-urgent__title">
          <Flame size={17} strokeWidth={2} aria-hidden />
          {labels.titleCount(summary.total)}
        </h3>
        <p className="ppc-feeder-urgent__hint">{labels.hint}</p>
      </div>

      {error ? (
        <p className="ppc-state ppc-state--error" role="alert">
          {error}
        </p>
      ) : null}

      {loading && items.length === 0 ? (
        <p className="ppc-feeder-urgent__empty" role="status">
          <Loader2 className="ppc-icon-btn__spin" size={16} aria-hidden /> {labels.loading}
        </p>
      ) : items.length === 0 ? (
        <p className="ppc-feeder-urgent__empty">{labels.empty}</p>
      ) : (
        <ul className="ppc-feeder-urgent__list">
          {items.map((item) => {
            const picked = item.status === "picked";
            const busy = busyId === item.id;
            return (
              <li
                key={item.id}
                className={
                  "ppc-feeder-urgent__item" + (picked ? " is-picked" : "")
                }
              >
                <div className="ppc-feeder-urgent__body">
                  <p className="ppc-feeder-urgent__item-title">
                    <strong>{item.productCode}</strong>
                    <span>{item.description}</span>
                    <span
                      className={
                        "ppc-feeder-urgent__status" +
                        (picked ? " is-picked" : "")
                      }
                    >
                      {picked ? labels.pickedBadge : labels.pendingBadge}
                    </span>
                  </p>
                  <p className="ppc-feeder-urgent__meta">
                    <span>
                      {labels.orderLabel(item.productionOrder, item.operationCode)}
                    </span>
                    <span>{labels.reportedCenter(item.reportedWorkCenter)}</span>
                    {item.currentWorkCenter &&
                    item.currentWorkCenter !== item.reportedWorkCenter ? (
                      <span>{labels.currentCenter(item.currentWorkCenter)}</span>
                    ) : null}
                    {item.outOfQueue ? (
                      <span className="ppc-feeder-urgent__out">
                        {labels.outOfQueue}
                      </span>
                    ) : null}
                  </p>
                  <p className="ppc-feeder-urgent__meta">
                    <span>
                      {labels.reportedBy(item.operatorName, item.operatorCode)}
                    </span>
                    <span>{labels.reportedAt(formatRefreshedAt(item.reportedAt))}</span>
                    <span>{labels.balanceLabel(item.openQty, item.unit)}</span>
                  </p>
                  {item.note ? (
                    <p className="ppc-feeder-urgent__note">
                      <strong>{labels.noteLabel}: </strong>
                      {item.note}
                    </p>
                  ) : null}
                </div>
                <div className="ppc-feeder-urgent__actions">
                  {picked ? (
                    <button
                      type="button"
                      className="ppc-feeder-urgent__action ppc-feeder-urgent__action--deliver"
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
                      className="ppc-feeder-urgent__action"
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
    </section>
  );
}
