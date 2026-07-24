import { useState } from "react";
import { BLOCK_REASON_OPTIONS } from "../../domain/status";

type Props = {
  open: boolean;
  busy?: boolean;
  onClose: () => void;
  onConfirm: (payload: {
    block_reason: string;
    block_description: string;
  }) => Promise<void> | void;
};

export function BlockModal({ open, busy, onClose, onConfirm }: Props) {
  const [reason, setReason] = useState("purchase_order");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  return (
    <div className="lnf-modal-backdrop" role="presentation">
      <div
        className="lnf-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lnf-block-title"
      >
        <h2 id="lnf-block-title">Registrar pendência</h2>
        <label className="lnf-field">
          Motivo
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            {BLOCK_REASON_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label className="lnf-field">
          Descrição
          <textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Descreva a pendência"
          />
        </label>
        {error ? (
          <p className="lnf-error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="lnf-modal__actions">
          <button
            type="button"
            className="lnf-btn lnf-btn--ghost"
            onClick={onClose}
            disabled={busy}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="lnf-btn lnf-btn--primary"
            disabled={busy}
            onClick={async () => {
              const text = description.trim();
              if (!text) {
                setError("Informe a descrição da pendência.");
                return;
              }
              setError(null);
              await onConfirm({
                block_reason: reason,
                block_description: text,
              });
              setDescription("");
            }}
          >
            Bloquear
          </button>
        </div>
      </div>
    </div>
  );
}
