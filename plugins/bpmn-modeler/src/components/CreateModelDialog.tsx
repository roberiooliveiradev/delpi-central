import { useState } from "react";

type Props = {
  open: boolean;
  busy: boolean;
  onCancel: () => void;
  onConfirm: (displayName: string) => void;
};

export function CreateModelDialog({ open, busy, onCancel, onConfirm }: Props) {
  const [name, setName] = useState("");
  if (!open) return null;
  const valid = name.trim().length > 0 && name.trim().length <= 120;
  return (
    <div className="bpmnm-overlay" role="presentation">
      <div className="bpmnm-dialog" role="dialog" aria-modal="true" aria-labelledby="bpmnm-create-title">
        <h2 id="bpmnm-create-title">Novo modelo</h2>
        <label className="bpmnm-field">
          Nome do modelo
          <input
            type="text"
            value={name}
            autoFocus
            maxLength={120}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && valid && !busy) onConfirm(name.trim());
            }}
          />
        </label>
        <div className="bpmnm-dialog__actions">
          <button type="button" onClick={onCancel} className="bpmnm-btn" disabled={busy}>
            Cancelar
          </button>
          <button
            type="button"
            className="bpmnm-btn bpmnm-btn--primary"
            disabled={!valid || busy}
            onClick={() => onConfirm(name.trim())}
          >
            {busy ? "Criando…" : "Criar"}
          </button>
        </div>
      </div>
    </div>
  );
}
