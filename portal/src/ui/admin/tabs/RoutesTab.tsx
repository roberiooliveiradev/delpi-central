// src/ui/admin/tabs/RoutesTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminAppRoute } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ActionButtons } from "../../../components/ActionButtons";
import { Modal } from "../../../components/Modal";
import { ConfirmDialog } from "../../../components/ConfirmDialog";

export const RoutesTab = () => {
  const { token } = useContext(AuthContext);

  const [appId, setAppId] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ sort?: string; direction?: "asc" | "desc" }>({
    sort: "path",
    direction: "asc",
  });

  const [selected, setSelected] = useState<string[]>([]);
  const [editing, setEditing] = useState<AdminAppRoute | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [toDelete, setToDelete] = useState<AdminAppRoute | null>(null);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const routesResource = usePaginatedResource<AdminAppRoute>(
    ({ page, pageSize }) => {
      if (!api || !appId) {
        return Promise.resolve({
          data: [],
          pagination: { page: 1, page_size: 10, total: 0, total_pages: 1 },
        });
      }

      return api.listRoutes(appId, {
        page,
        pageSize,
        q: search,
        sort: sort.sort,
        direction: sort.direction,
      });
    },
    10,
    [appId, search, sort.sort, sort.direction]
  );

  if (!api) return null;

  const saveEdit = async () => {
    if (!editing) return;
    setConfirmLoading(true);
    try {
      await api.updateRoute(editing.id, {
        path: editing.path,
        label: editing.label,
        active: editing.active,
      });
      setEditing(null);
      routesResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  const doDeleteOne = async () => {
    if (!toDelete) return;
    setConfirmLoading(true);
    try {
      await api.deleteRoute(toDelete.id);
      setToDelete(null);
      setConfirmOpen(false);
      setSelected((s) => s.filter((id) => id !== toDelete.id));
      routesResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  const doBulkDeactivate = async () => {
    if (selected.length === 0) return;
    setConfirmLoading(true);
    try {
      await api.bulkDeactivateRoutes(selected);
      setSelected([]);
      setConfirmOpen(false);
      routesResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  return (
    <div>
      <h2>Rotas</h2>

      <input
        placeholder="App ID (ex: crm)"
        value={appId}
        onChange={(e) => setAppId(e.target.value)}
        style={{ marginBottom: 20 }}
      />

      {!appId && <p>Digite um App ID para carregar as rotas.</p>}

      {appId && (
        <DataTable
          columns={[
            { key: "path", header: "Path", sortable: true },
            { key: "label", header: "Label", sortable: true },
            {
              key: "permission_code",
              header: "Permissão",
              render: (row) => row.permission_code || "Pública",
            },
            {
              key: "active",
              header: "Status",
              sortable: true,
              render: (row) => (row.active ? "Ativa" : "Inativa"),
            },
          ]}
          data={routesResource.data}
          loading={routesResource.loading}
          searchValue={search}
          onSearchChange={setSearch}
          sort={sort}
          onSortChange={setSort}
          selectable
          getRowId={(row) => row.id}
          selectedRows={selected}
          onSelectionChange={setSelected}
          toolbar={
            selected.length > 0 ? (
              <>
                <button
                  className="btn-danger"
                  onClick={() => {
                    setToDelete(null);
                    setConfirmOpen(true);
                  }}
                  disabled={confirmLoading}
                >
                  Desativar ({selected.length})
                </button>
              </>
            ) : (
              <span className="dt-muted">Selecione rotas para ação em massa</span>
            )
          }
          actions={(row) => (
            <ActionButtons
              onEdit={() => setEditing(row)}
              onDelete={() => {
                setToDelete(row);
                setConfirmOpen(true);
              }}
            />
          )}
          pagination={
            routesResource.pagination
              ? {
                  page: routesResource.page,
                  totalPages: routesResource.pagination.total_pages,
                  total: routesResource.pagination.total,
                  pageSize: 10,
                }
              : undefined
          }
          onPageChange={routesResource.setPage}
        />
      )}

      <Modal
        open={!!editing}
        title="Editar Rota"
        onClose={() => setEditing(null)}
        footer={
          <>
            <button onClick={() => setEditing(null)} disabled={confirmLoading}>
              Cancelar
            </button>
            <button onClick={saveEdit} disabled={confirmLoading}>
              Salvar
            </button>
          </>
        }
      >
        {editing && (
          <>
            <label>
              Path
              <input value={editing.path} onChange={(e) => setEditing({ ...editing, path: e.target.value })} />
            </label>

            <label>
              Label
              <input
                value={editing.label ?? ""}
                onChange={(e) => setEditing({ ...editing, label: e.target.value })}
              />
            </label>

            <label style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={!!editing.active}
                onChange={(e) => setEditing({ ...editing, active: e.target.checked })}
              />
              Ativa
            </label>
          </>
        )}
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title={toDelete ? "Excluir rota" : "Desativar rotas"}
        message={
          toDelete
            ? `Deseja excluir a rota "${toDelete.path}"?`
            : `Deseja desativar ${selected.length} rotas selecionadas?`
        }
        confirmText={toDelete ? "Excluir" : "Desativar"}
        danger
        loading={confirmLoading}
        onCancel={() => {
          setConfirmOpen(false);
          setToDelete(null);
        }}
        onConfirm={toDelete ? doDeleteOne : doBulkDeactivate}
      />
    </div>
  );
};