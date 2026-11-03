import { useEffect, useState } from "react";
import type { MesDowntimeReason, RunDowntimeView } from "./api";
import { DowntimeElapsedTimer } from "./DowntimeElapsedTimer";
import { elapsedSeconds, formatDurationHms } from "./runTimeline";
import { formatTimeHmSp } from "./workCenterActivity";

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

function isEditingClassified(downtime: RunDowntimeView | null | undefined): boolean {
  if (!downtime) return false;
  return Boolean(
    downtime.confirmed ||
      downtime.reasonCode?.trim() ||
      downtime.reasonLabel?.trim(),
  );
}

/**
 * Classificação do motivo da parada MES. Informa pendências e permite
 * alterar motivo/observação de paradas já classificadas, pré-carregando
 * os valores atuais. Usado no card de operação e em Paradas do posto.
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
  const [inactiveCurrent, setInactiveCurrent] = useState(false);

  useEffect(() => {
    if (!open) return;
    let active = true;
    setSubmitError(null);
    setLoadError(null);
    setSelected(null);
    setInactiveCurrent(false);
    setNote(downtime?.note?.trim() ? downtime.note : "");
    setReasons(null);
    void loadReasons()
      .then((items) => {
        if (!active) return;
        setReasons(items);
        const code = downtime?.reasonCode?.trim();
        if (!code) return;
        const match = items.find((reason) => reason.code === code);
        if (match) {
          setSelected(match);
        } else {
          setInactiveCurrent(true);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setLoadError(
            err instanceof Error
              ? err.message
              : "Motivos de parada indisponíveis.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [open, downtime?.id, downtime?.reasonCode, downtime?.note, loadReasons]);

  if (!open) return null;

  const editing = isEditingClassified(downtime);
  const title = editing
    ? "Alterar motivo da parada"
    : "Informar motivo da parada";
  const showNote =
    selected != null &&
    (selected.requiresNote || Boolean(note) || Boolean(downtime?.note));

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
        err instanceof Error
          ? err.message
          : "Não foi possível registrar o motivo.",
      );
    }
  };

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-downtime-title"
    >
      <button
        type="button"
        className="pcp-pub-modal__backdrop"
        aria-label="Fechar"
        onClick={onClose}
      />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--downtime-reason">
        <h3 id="pcp-downtime-title" className="pcp-pub__run-title">
          {title}
        </h3>

        {downtime?.startedAt ? (
          <div className="pcp-pub__downtime" role="status">
            <p className="pcp-pub__downtime-title">
              {downtime.endedAt ? "Parada encerrada" : "Parada em andamento"}
            </p>
            {downtime.endedAt ? (
              <span className="pcp-pub__downtime-timer" role="timer">
                {formatDurationHms(
                  elapsedSeconds(
                    downtime.startedAt,
                    Date.parse(downtime.endedAt),
                  ),
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
                ? "Das " +
                  formatTimeHmSp(downtime.startedAt) +
                  " às " +
                  formatTimeHmSp(downtime.endedAt)
                : "Iniciada às " +
                  formatTimeHmSp(downtime.startedAt) +
                  " · em andamento"}
            </p>
          </div>
        ) : null}

        {editing && downtime?.reasonLabel ? (
          <p className="pcp-pub__run-note">
            Motivo atual: <strong>{downtime.reasonLabel}</strong>
            {downtime.note?.trim()
              ? ` · Obs.: ${downtime.note.trim()}`
              : ""}
          </p>
        ) : (
          <p className="pcp-pub__run-note">
            Selecione o motivo da parada para continuar.
          </p>
        )}

        {inactiveCurrent && downtime?.reasonLabel ? (
          <p className="pcp-pub__run-error" role="status">
            O motivo atual ({downtime.reasonLabel}) não está mais disponível.
            Selecione um motivo válido para confirmar.
          </p>
        ) : null}

        {loadError ? <p className="pcp-pub__run-error">{loadError}</p> : null}
        {!loadError && !reasons ? (
          <p className="pcp-pub__run-note">Carregando motivos…</p>
        ) : null}

        {reasons ? (
          <div
            className="pcp-pub-reasons"
            role="listbox"
            aria-label="Motivos de parada"
          >
            {reasons.map((reason) => (
              <button
                key={reason.code}
                type="button"
                role="option"
                aria-selected={selected?.code === reason.code}
                className={`pcp-pub-reasons__item${
                  selected?.code === reason.code
                    ? " pcp-pub-reasons__item--selected"
                    : ""
                }`}
                onClick={() => {
                  setSelected(reason);
                  setSubmitError(null);
                  if (!reason.requiresNote && !downtime?.note?.trim()) {
                    setNote("");
                  }
                }}
                disabled={busy}
              >
                {reason.label}
              </button>
            ))}
          </div>
        ) : null}

        {showNote ? (
          <label className="pcp-pub__run-field pcp-pub-reasons__note">
            <span>
              {selected?.requiresNote
                ? "Descreva o motivo da parada"
                : "Observação (opcional)"}
            </span>
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={3}
              maxLength={500}
              required={Boolean(selected?.requiresNote)}
              placeholder={
                selected?.requiresNote
                  ? "Descreva o motivo da parada..."
                  : "Observação..."
              }
            />
          </label>
        ) : null}

        {submitError ? <p className="pcp-pub__run-error">{submitError}</p> : null}

        <div className="pcp-pub__run-actions">
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--primary"
            onClick={() => void submit()}
            disabled={busy || !selected}
          >
            {editing ? "Salvar alteração" : "Confirmar motivo"}
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
