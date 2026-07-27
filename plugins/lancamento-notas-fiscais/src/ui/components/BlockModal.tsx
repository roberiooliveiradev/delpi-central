import { useState } from "react";
import { UserDirectoryPicker } from "@delpi/plugin-ui/index";
import {
  searchDirectoryUsers,
  type DirectoryUser,
} from "../../data/api/directoryApi";
import { BLOCK_REASON_OPTIONS } from "../../domain/status";

export type BlockModalPayload = {
  block_reason: string;
  block_description: string;
  assignee_user_id: string;
  assignee_name: string;
};

type Props = {
  open: boolean;
  busy?: boolean;
  onClose: () => void;
  onConfirm: (payload: BlockModalPayload) => Promise<void> | void;
};

export function BlockModal({ open, busy, onClose, onConfirm }: Props) {
  const [reason, setReason] = useState("purchase_order");
  const [description, setDescription] = useState("");
  const [responsible, setResponsible] = useState<DirectoryUser[]>([]);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const resetForm = () => {
    setDescription("");
    setResponsible([]);
    setReason("purchase_order");
    setError(null);
  };

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
        <div className="lnf-field">
          <UserDirectoryPicker
            value={responsible}
            onChange={setResponsible}
            searchUsers={searchDirectoryUsers}
            disabled={busy}
            showEmail={false}
            maxSelected={1}
            labels={{
              title: "Responsável pela correção",
              hint: "Selecione um usuário do Minha Delpi. Apenas o nome é exibido.",
              placeholder: "Buscar por nome",
            }}
          />
        </div>
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
            onClick={() => {
              resetForm();
              onClose();
            }}
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
              const selected = responsible[0];
              if (!selected) {
                setError("Selecione o responsável pela correção da pendência.");
                return;
              }
              if (!text) {
                setError("Informe a descrição da pendência.");
                return;
              }
              setError(null);
              await onConfirm({
                block_reason: reason,
                block_description: text,
                assignee_user_id: selected.id,
                assignee_name: (selected.name || "").trim() || selected.email,
              });
              resetForm();
            }}
          >
            Bloquear
          </button>
        </div>
      </div>
    </div>
  );
}
