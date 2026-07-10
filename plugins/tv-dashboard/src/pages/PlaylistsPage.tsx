import { useCallback, useEffect, useState } from "react";
import { Copy, MonitorPlay, Plus } from "lucide-react";

import {
  duplicatePlaylist,
  listPlaylists,
  type Playlist,
} from "../api/tvDashboardApi";
import { useConfirm } from "../context/ConfirmDialogProvider";

function formatLastPresented(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

type Props = {
  onOpen: (id: string) => void;
  onCreate: () => void;
};

export function PlaylistsPage({ onOpen, onCreate }: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  async function handleDuplicate(item: Playlist) {
    const confirmed = await confirm({
      title: "Duplicar programação",
      message: `Duplicar «${item.name}»?`,
      confirmLabel: "Duplicar",
    });
    if (!confirmed) return;
    try {
      const copy = await duplicatePlaylist(item.id);
      onOpen(copy.id);
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Erro ao duplicar programação.");
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
        <button type="button" className="td-btn td-btn--primary" onClick={onCreate}>
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
                <th>Última exibição</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={5}>Nenhuma programação cadastrada.</td>
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
                    <td>{formatLastPresented(item.lastPresentedAt)}</td>
                    <td>
                      <button type="button" className="td-btn" onClick={() => onOpen(item.id)}>
                        <MonitorPlay size={16} />
                        Gerenciar
                      </button>
                      <button type="button" className="td-btn" onClick={() => void handleDuplicate(item)}>
                        <Copy size={16} />
                        Duplicar
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
