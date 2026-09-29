import { useEffect } from "react";
import type { PendingMesDowntime } from "./api";
import { formatDurationHms, formatTimeHm } from "./runTimeline";

type Props = {
  open: boolean;
  items: PendingMesDowntime[] | null;
  error: string | null;
  busy: boolean;
  onSelect: (item: PendingMesDowntime) => void;
  onClose: () => void;
};

/**
 * Paradas encerradas do posto que ficaram sem motivo — inclui paradas de
 * runs já finalizados. Cada item abre o modal de classificação por
 * downtime_id (mesmo serviço da parada aberta).
 */
export function PendingDowntimesModal({
  open,
  items,
  error,
  busy,
  onSelect,
  onClose,
}: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-pending-title"
    >
      <button
        type="button"
        className="pcp-pub-modal__backdrop"
        aria-label="Fechar"
        onClick={onClose}
      />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--downtime">
        <header className="pcp-pub-modal__head">
          <h2 id="pcp-pub-pending-title">Paradas sem motivo</h2>
          <button
            type="button"
            className="pcp-pub__ghost pcp-pub__ghost--plain"
            onClick={onClose}
          >
            Fechar
          </button>
        </header>

        <p className="pcp-pub-modal__lede">
          Paradas encerradas neste posto que ainda não tiveram o motivo informado.
        </p>

        {error ? <p className="pcp-pub-modal__empty">{error}</p> : null}
        {!error && items === null ? (
          <p className="pcp-pub-modal__empty">Carregando paradas…</p>
        ) : null}
        {!error && items !== null && items.length === 0 ? (
          <p className="pcp-pub-modal__empty">Nenhuma parada pendente de motivo.</p>
        ) : null}

        {items && items.length > 0 ? (
          <ol className="pcp-pub-pending">
            {items.map((item) => (
              <li key={item.id} className="pcp-pub-pending__item">
                <div className="pcp-pub-pending__info">
                  <strong>
                    {item.startedAt ? formatTimeHm(item.startedAt) : "—"} ·{" "}
                    {formatDurationHms(item.durationSeconds)}
                  </strong>
                  <span className="pcp-pub-pending__meta">
                    {item.productionOrder
                      ? `OP ${item.productionOrder}${item.operationCode ? ` · op. ${item.operationCode}` : ""}`
                      : "Sem produção vinculada"}
                    {item.source === "system" ? " · automática" : ""}
                  </span>
                </div>
                <button
                  type="button"
                  className="pcp-pub__btn pcp-pub__btn--ghost"
                  disabled={busy || !item.runId}
                  onClick={() => onSelect(item)}
                >
                  Informar motivo
                </button>
              </li>
            ))}
          </ol>
        ) : null}
      </div>
    </div>
  );
}
