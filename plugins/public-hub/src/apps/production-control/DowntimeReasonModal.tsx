import { useEffect, useState } from "react";
import type { MesDowntimeReason, RunDowntimeView } from "./api";
import { DowntimeElapsedTimer } from "./DowntimeElapsedTimer";
import { elapsedSeconds, formatDurationHms, formatTimeHm } from "./runTimeline";

type Props = {
  open: boolean;
  downtime: RunDowntimeView | null | undefined;
  busy: boolean;
  /** "Agora" no servidor (relógio local + offset) — alimenta o timer da parada. */
  serverNow: () => number;
  loadReasons: () => Promise<MesDowntimeReason[]>;
  onClassify: (reasonCode: string, note: string | null) => Promise<void>;
  onClose: () => void;
};

/**
 * Classificação do motivo da parada MES. O `started_at` já foi gravado no
 * Pause — aqui o operador só informa o motivo. Usado tanto no card quanto
 * no detalhamento da operação via ProductionRunControls.
 */
export function DowntimeReasonModal({
  open,
  downtime,
  busy,
  serverNow,
  loadReasons,
  onClassify,
  onClose,
}: Props) {
  const [reasons, setReasons] = useState<MesDowntimeReason[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [selected, setSelected] = useState<MesDowntimeReason | null>(null);
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!open) return;
    let active = true;
    setSelected(null);
    setNote("");
    setSubmitError(null);
    setLoadError(null);
    void loadReasons()
      .then((items) => {
        if (active) setReasons(items);
      })
      .catch((err: unknown) => {
        if (active) {
          setLoadError(
            err instanceof Error ? err.message : "Motivos de parada indisponíveis.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [open, loadReasons]);

  if (!open) return null;

  const submit = async () => {
    if (!selected || busy) return;
    const cleanNote = note.trim();
    if (selected.requiresNote && !cleanNote) {
      setSubmitError("Descreva o motivo da parada para continuar.");
      return;
    }
    setSubmitError(null);
    try {
      await onClassify(selected.code, cleanNote || null);
      onClose();
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Não foi possível registrar o motivo.",
      );
    }
  };

  return (
    <div className="pcp-pub-modal" role="dialog" aria-modal="true" aria-labelledby="pcp-downtime-title">
      <button
        type="button"
        className="pcp-pub-modal__backdrop"
        aria-label="Fechar"
        onClick={onClose}
      />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--downtime-reason">
        <h3 id="pcp-downtime-title" className="pcp-pub__run-title">
          Por que a produção parou?
        </h3>

        {downtime?.startedAt ? (
          <div className="pcp-pub__downtime" role="status">
            <p className="pcp-pub__downtime-title">
              {downtime.endedAt ? "Parada encerrada" : "Parada em registro"}
            </p>
            {downtime.endedAt ? (
              <span className="pcp-pub__downtime-timer" role="timer">
                {formatDurationHms(
                  elapsedSeconds(downtime.startedAt, Date.parse(downtime.endedAt)),
                )}
              </span>
            ) : (
              <DowntimeElapsedTimer
                startedAt={downtime.startedAt}
                serverNow={serverNow}
              />
            )}
            <p className="pcp-pub__downtime-note">
              {downtime.endedAt
                ? "Das " + formatTimeHm(downtime.startedAt) + " às " + formatTimeHm(downtime.endedAt)
                : "Iniciada às " + formatTimeHm(downtime.startedAt) + " · em curso"}
            </p>
          </div>
        ) : null}

        <p className="pcp-pub__run-note">
          Selecione o motivo da parada para continuar.
        </p>

        {loadError ? <p className="pcp-pub__run-error">{loadError}</p> : null}
        {!loadError && !reasons ? (
          <p className="pcp-pub__run-note">Carregando motivos…</p>
        ) : null}

        {reasons ? (
          <div className="pcp-pub-reasons" role="listbox" aria-label="Motivos de parada">
            {reasons.map((reason) => (
              <button
                key={reason.code}
                type="button"
                role="option"
                aria-selected={selected?.code === reason.code}
                className={`pcp-pub-reasons__item${
                  selected?.code === reason.code ? " pcp-pub-reasons__item--selected" : ""
                }`}
                onClick={() => {
                  setSelected(reason);
                  setSubmitError(null);
                }}
                disabled={busy}
              >
                {reason.label}
              </button>
            ))}
          </div>
        ) : null}

        {selected?.requiresNote ? (
          <label className="pcp-pub__run-field pcp-pub-reasons__note">
            <span>Descreva o motivo da parada</span>
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={3}
              maxLength={500}
              required
              placeholder="Descreva o motivo da parada..."
            />
          </label>
        ) : null}

        {submitError ? <p className="pcp-pub__run-error">{submitError}</p> : null}

        {downtime?.confirmed && downtime.reasonLabel ? (
          <p className="pcp-pub__run-note">Motivo atual: {downtime.reasonLabel}</p>
        ) : null}

        <div className="pcp-pub__run-actions">
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--primary"
            onClick={() => void submit()}
            disabled={busy || !selected}
          >
            Confirmar motivo
          </button>
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--ghost"
            onClick={onClose}
            disabled={busy}
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
