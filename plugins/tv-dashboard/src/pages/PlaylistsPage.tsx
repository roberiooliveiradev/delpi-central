import { useCallback, useEffect, useMemo, useState } from "react";
import { Copy, MonitorPlay, Plus } from "lucide-react";

import {
  duplicatePlaylist,
  listPlaylists,
  type Playlist,
} from "../api/tvDashboardApi";
import { DataTable, type DataTableColumn } from "../components/dataTableUi";
import { useConfirm } from "../context/ConfirmDialogProvider";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

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
  const [sortKey, setSortKey] = useState<string | null>("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

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

  const columns = useMemo<DataTableColumn<Playlist>[]>(
    () => [
      {
        key: "name",
        header: "Nome",
        render: (row) => row.name,
        sortable: true,
        sortValue: (row) => row.name,
      },
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <span className={`td-badge ${row.isActive ? "td-badge--active" : "td-badge--inactive"}`}>
            {row.isActive ? "Ativa" : "Inativa"}
          </span>
        ),
        sortable: true,
        sortValue: (row) => (row.isActive ? 1 : 0),
      },
      {
        key: "viewCount",
        header: "Visualizações",
        align: "right",
        render: (row) => row.viewCount ?? 0,
        sortable: true,
        sortValue: (row) => row.viewCount ?? 0,
      },
      {
        key: "lastPresentedAt",
        header: "Última exibição",
        render: (row) => formatLastPresented(row.lastPresentedAt),
        sortable: true,
        sortValue: (row) => row.lastPresentedAt ?? "",
      },
      {
        key: "actions",
        header: "Ações",
        interactive: true,
        render: (row) => (
          <div className="td-table-actions">
            <button type="button" className="td-btn" onClick={() => onOpen(row.id)}>
              <MonitorPlay size={16} aria-hidden="true" />
              Gerenciar
            </button>
            <button type="button" className="td-btn" onClick={() => void handleDuplicate(row)}>
              <Copy size={16} aria-hidden="true" />
              Duplicar
            </button>
          </div>
        ),
      },
    ],
    [handleDuplicate, onOpen],
  );

  const sortedItems = useMemo(() => {
    if (!sortKey) return items;
    const column = columns.find((item) => item.key === sortKey);
    if (!column?.sortValue) return items;
    const direction = sortDirection === "asc" ? 1 : -1;
    return [...items].sort((left, right) => {
      const a = column.sortValue?.(left);
      const b = column.sortValue?.(right);
      if (a == null && b == null) return 0;
      if (a == null) return 1;
      if (b == null) return -1;
      if (typeof a === "number" && typeof b === "number") return (a - b) * direction;
      return String(a).localeCompare(String(b), "pt-BR", { sensitivity: "base" }) * direction;
    });
  }, [columns, items, sortDirection, sortKey]);

  function handleSortChange(columnKey: string) {
    if (sortKey === columnKey) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(columnKey);
    setSortDirection("asc");
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
          <Plus size={16} aria-hidden="true" />
          Nova programação
        </button>
      </div>

      {error ? <div className="td-state">{error}</div> : null}

      {!error ? (
        <DataTable
          columns={columns}
          rows={sortedItems}
          rowKey={(row) => row.id}
          loading={loading}
          layout="embedded"
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSortChange={handleSortChange}
        />
      ) : null}
    </div>
  );
}
