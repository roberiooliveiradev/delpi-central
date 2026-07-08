import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { createPlaylist } from "../api/tvDashboardApi";
import { TdNativeTextAreaField, TdNativeTextField } from "../components/tdFormFields";

type Props = {
  onBack: () => void;
  onCreated: (id: string) => void;
};

export function NewPlaylistPage({ onBack, onCreated }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const created = await createPlaylist(name.trim(), description.trim() || undefined);
      onCreated(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar programação.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="td-toolbar">
        <button type="button" className="td-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
      </div>
      <div className="td-card" style={{ maxWidth: 560 }}>
        <h2 style={{ marginTop: 0 }}>Nova programação</h2>
        <p className="td-subtitle">Defina um nome e adicione telas na sequência.</p>
        <form onSubmit={(event) => void handleSubmit(event)}>
          <TdNativeTextField
            id="td-new-name"
            label="Nome"
            value={name}
            onChange={setName}
            placeholder="Ex.: Painel fábrica — turno A"
            required
            autoFocus
          />
          <TdNativeTextAreaField
            id="td-new-description"
            label="Descrição (opcional)"
            value={description}
            onChange={setDescription}
            rows={3}
            span={false}
          />
          {error ? <p className="td-state">{error}</p> : null}
          <div className="td-modal-actions">
            <button type="button" className="td-btn" onClick={onBack}>
              Cancelar
            </button>
            <button type="submit" className="td-btn td-btn--primary" disabled={saving || !name.trim()}>
              {saving ? "Criando…" : "Criar programação"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
