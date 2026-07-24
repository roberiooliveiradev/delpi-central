import { useState } from "react";

type Props = {
  open: boolean;
  busy?: boolean;
  onClose: () => void;
  onConfirm: (justification: string) => Promise<void> | void;
};

export function CancelModal({ open, busy, onClose, onConfirm }: Props) {
  const [justification, setJustification] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  if (!open) return null;

  return (
    <div className="lnf-modal-backdrop" role="presentation">
      <div
        className="lnf-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lnf-cancel-title"
      >
        <h2 id="lnf-cancel-title">Cancelar solicitação</h2>
        <p className="lnf-muted">
          Esta ação encerra a solicitação. Informe a justificativa e confirme.
        </p>
        <label className="lnf-field">
          Justificativa
          <textarea
            rows={4}
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
          />
        </label>
        <label className="lnf-check">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          Confirmo o cancelamento desta solicitação
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
            Voltar
          </button>
          <button
            type="button"
            className="lnf-btn lnf-btn--danger"
            disabled={busy}
            onClick={async () => {
              const text = justification.trim();
              if (!text) {
                setError("Justificativa obrigatória.");
                return;
              }
              if (!confirmed) {
                setError("Marque a confirmação explícita.");
                return;
              }
              setError(null);
              await onConfirm(text);
              setJustification("");
              setConfirmed(false);
            }}
          >
            Cancelar solicitação
          </button>
        </div>
      </div>
    </div>
  );
}
