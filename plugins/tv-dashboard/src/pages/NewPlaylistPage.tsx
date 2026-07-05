import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { createPlaylist } from "../api/tvDashboardApi";

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
          <div className="td-field">
            <label htmlFor="td-new-name">Nome</label>
            <input
              id="td-new-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex.: Painel fábrica — turno A"
              required
              autoFocus
            />
          </div>
          <div className="td-field">
            <label htmlFor="td-new-description">Descrição (opcional)</label>
            <textarea
              id="td-new-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
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
