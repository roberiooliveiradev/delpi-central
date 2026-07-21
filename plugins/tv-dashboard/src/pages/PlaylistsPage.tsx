import { useCallback, useEffect, useMemo, useState } from "react";
import { Copy, MonitorPlay, Plus, Search } from "lucide-react";

import {
  duplicatePlaylist,
  listPlaylists,
  type Playlist,
} from "../api/tvDashboardApi";
import { useConfirm } from "../context/ConfirmDialogProvider";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

function formatLastPresented(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function greetingPt(now = new Date()): string {
  const hour = now.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

export type PlaylistHomeFilter = "recent" | "active" | "inactive";

type Props = {
  onOpen: (id: string) => void;
  onCreate: () => void;
};

export function filterPlaylists(
  items: Playlist[],
  filter: PlaylistHomeFilter,
  query: string,
): Playlist[] {
  const q = query.trim().toLowerCase();
  let next = items;
  if (filter === "active") next = next.filter((item) => item.isActive);
  if (filter === "inactive") next = next.filter((item) => !item.isActive);
  if (q) next = next.filter((item) => item.name.toLowerCase().includes(q));

  if (filter === "recent") {
    return [...next].sort((a, b) => {
      const ta = a.lastPresentedAt ? Date.parse(a.lastPresentedAt) : 0;
      const tb = b.lastPresentedAt ? Date.parse(b.lastPresentedAt) : 0;
      if (tb !== ta) return tb - ta;
      return a.name.localeCompare(b.name, "pt-BR", { sensitivity: "base" });
    });
  }
  return [...next].sort((a, b) =>
    a.name.localeCompare(b.name, "pt-BR", { sensitivity: "base" }),
  );
}

export function PlaylistsPage({ onOpen, onCreate }: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<PlaylistHomeFilter>("recent");
  const [query, setQuery] = useState("");

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

  const handleDuplicate = useCallback(
    async (item: Playlist) => {
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
        tvDashboardNotice(err instanceof Error ? err.message : "Erro ao duplicar programação.");
      }
    },
    [confirm, onOpen],
  );

  const visible = useMemo(
    () => filterPlaylists(items, filter, query),
    [filter, items, query],
  );

  const greeting = useMemo(() => greetingPt(), []);

  return (
    <div className="td-home">
      <section className="td-home__greeting" aria-label="Início">
        <h2 className="td-home__hello">{greeting}</h2>
        <div className="td-home__create-row">
          <button
            type="button"
            className="td-home__create-card"
            onClick={onCreate}
          >
            <span className="td-home__create-icon" aria-hidden="true">
              <Plus size={28} strokeWidth={2} />
            </span>
            <span className="td-home__create-title">Nova programação</span>
            <span className="td-home__create-hint">
              Monte playlists de telas e gere um link público para TVs.
            </span>
          </button>
        </div>
      </section>

      <section className="td-home__library" aria-label="Programações">
        <div className="td-home__library-bar">
          <div className="td-home__filters" role="tablist" aria-label="Filtrar programações">
            {(
              [
                ["recent", "Recentes"],
                ["active", "Ativas"],
                ["inactive", "Inativas"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={filter === id}
                className={[
                  "td-home__filter",
                  filter === id ? "td-home__filter--active" : null,
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => setFilter(id)}
              >
                {label}
              </button>
            ))}
          </div>
          <label className="td-home__search">
            <Search size={16} aria-hidden="true" />
            <span className="td-sr-only">Buscar programação</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar programação"
              autoComplete="off"
            />
          </label>
        </div>

        {error ? <div className="td-state">{error}</div> : null}

        {loading ? <div className="td-state">Carregando programações…</div> : null}

        {!loading && !error && visible.length === 0 ? (
          <div className="td-home__empty">
            <p>Nenhuma programação neste filtro.</p>
            <button type="button" className="td-btn td-btn--primary" onClick={onCreate}>
              <Plus size={16} aria-hidden="true" />
              Nova programação
            </button>
          </div>
        ) : null}

        {!loading && !error && visible.length > 0 ? (
          <ul className="td-home__grid">
            {visible.map((item) => (
              <li key={item.id} className="td-home__card">
                <button
                  type="button"
                  className="td-home__card-main"
                  onClick={() => onOpen(item.id)}
                  aria-label={`Abrir ${item.name}`}
                >
                  <span className="td-home__card-thumb" aria-hidden="true">
                    <MonitorPlay size={28} strokeWidth={1.6} />
                  </span>
                  <span className="td-home__card-body">
                    <span className="td-home__card-name">{item.name}</span>
                    <span className="td-home__card-meta">
                      <span
                        className={`td-badge ${item.isActive ? "td-badge--active" : "td-badge--inactive"}`}
                      >
                        {item.isActive ? "Ativa" : "Inativa"}
                      </span>
                      <span>{item.viewCount ?? 0} visualizações</span>
                      <span>Última: {formatLastPresented(item.lastPresentedAt)}</span>
                    </span>
                  </span>
                </button>
                <div className="td-home__card-actions">
                  <button
                    type="button"
                    className="td-btn td-btn--sm"
                    onClick={() => onOpen(item.id)}
                  >
                    <MonitorPlay size={14} aria-hidden="true" />
                    Abrir
                  </button>
                  <button
                    type="button"
                    className="td-btn td-btn--sm"
                    onClick={() => void handleDuplicate(item)}
                  >
                    <Copy size={14} aria-hidden="true" />
                    Duplicar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
