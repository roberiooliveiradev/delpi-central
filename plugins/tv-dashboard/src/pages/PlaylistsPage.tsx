import { useCallback, useEffect, useState } from "react";
import { MonitorPlay, Plus } from "lucide-react";

import {
  createPlaylist,
  listPlaylists,
  type Playlist,
} from "../api/tvDashboardApi";

type Props = {
  onOpen: (id: string) => void;
};

export function PlaylistsPage({ onOpen }: Props) {
  const [items, setItems] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await listPlaylists());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar programações.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreate() {
    const name = window.prompt("Nome da programação:");
    if (!name?.trim()) return;
    setCreating(true);
    try {
      const created = await createPlaylist(name.trim());
      onOpen(created.id);
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Erro ao criar programação.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="td-card">
      <div className="td-toolbar">
        <div>
          <h2 style={{ margin: 0 }}>Programações</h2>
          <p className="td-subtitle" style={{ marginTop: 4 }}>
            Monte playlists de telas e gere links públicos para TVs.
          </p>
        </div>
        <button type="button" className="td-btn td-btn--primary" disabled={creating} onClick={() => void handleCreate()}>
          <Plus size={16} />
          Nova programação
        </button>
      </div>

      {loading ? <div className="td-state">Carregando…</div> : null}
      {error ? <div className="td-state">{error}</div> : null}

      {!loading && !error ? (
        <div className="td-table-wrap">
          <table className="td-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Status</th>
                <th>Visualizações</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={4}>Nenhuma programação cadastrada.</td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td>
                      <span className={`td-badge ${item.isActive ? "td-badge--active" : "td-badge--inactive"}`}>
                        {item.isActive ? "Ativa" : "Inativa"}
                      </span>
                    </td>
                    <td>{item.viewCount ?? 0}</td>
                    <td>
                      <button type="button" className="td-btn" onClick={() => onOpen(item.id)}>
                        <MonitorPlay size={16} />
                        Gerenciar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
