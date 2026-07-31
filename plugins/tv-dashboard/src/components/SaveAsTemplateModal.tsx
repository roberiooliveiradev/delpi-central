import { useState } from "react";

import { createSlideTemplateFromSlide } from "../api/tvDashboardApi";
import { HostContainedDialog } from "./ui/Modal";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

type Props = {
  open: boolean;
  nativeConfig: Record<string, unknown>;
  onClose: () => void;
  onCreated?: (id: string) => void;
};

export function SaveAsTemplateModal({ open, nativeConfig, onClose, onCreated }: Props) {
  const [label, setLabel] = useState("Novo template");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    const name = label.trim();
    if (!name) {
      tvDashboardNotice("Informe um nome.");
      return;
    }
    setBusy(true);
    try {
      const created = await createSlideTemplateFromSlide({
        label: name,
        description: description.trim() || undefined,
        nativeConfig,
        nativeScreenKey: "custom_message",
      });
      tvDashboardNotice("Template salvo como rascunho na biblioteca.");
      onCreated?.(created.id);
      onClose();
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao salvar template.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <HostContainedDialog open={open} title="Salvar slide como template" onClose={onClose}>
      <div className="td-save-as-template">
        <label>
          Nome
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            autoComplete="off"
          />
        </label>
        <label>
          Descrição
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          />
        </label>
        <div className="td-save-as-template__actions">
          <button type="button" className="td-btn td-btn--ghost" onClick={onClose} disabled={busy}>
            Cancelar
          </button>
          <button type="button" className="td-btn" onClick={() => void submit()} disabled={busy}>
            {busy ? "Salvando…" : "Salvar rascunho"}
          </button>
        </div>
      </div>
    </HostContainedDialog>
  );
}
