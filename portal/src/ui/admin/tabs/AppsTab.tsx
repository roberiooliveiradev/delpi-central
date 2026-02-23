// src/ui/admin/tabs/AppsTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminApp } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ActionButtons } from "../../../components/ActionButtons";
import { Modal } from "../../../components/Modal";
import { ConfirmDialog } from "../../../components/ConfirmDialog";

export const AppsTab = () => {
  const { token } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ sort?: string; direction?: "asc" | "desc" }>({
    sort: "name",
    direction: "asc",
  });

  const [selected, setSelected] = useState<string[]>([]);
  const [editing, setEditing] = useState<AdminApp | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [toDelete, setToDelete] = useState<AdminApp | null>(null);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const appsResource = usePaginatedResource<AdminApp>(
    ({ page, pageSize }) =>
      api!.listApps({
        page,
        pageSize,
        q: search,
        sort: sort.sort,
        direction: sort.direction,
      }),
    10,
    [search, sort.sort, sort.direction]
  );

  if (!api) return null;

  const saveEdit = async () => {
    if (!editing) return;
    setConfirmLoading(true);
    try {
      await api.updateApp(editing.id, {
        name: editing.name,
        version: editing.version,
        base_path: editing.base_path,
        icon: editing.icon,
        type: editing.type,
        active: editing.active,
      });
      setEditing(null);
      appsResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  const doDeleteOne = async () => {
    if (!toDelete) return;
    setConfirmLoading(true);
    try {
      await api.deleteApp(toDelete.id);
      setToDelete(null);
      setConfirmOpen(false);
      setSelected((s) => s.filter((id) => id !== toDelete.id));
      appsResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  const doBulkDelete = async () => {
    if (selected.length === 0) return;
    setConfirmLoading(true);
    try {
      await api.bulkDeleteApps(selected);
      setSelected([]);
      setConfirmOpen(false);
      appsResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  const bulkActivate = async () => {
    if (selected.length === 0) return;
    setConfirmLoading(true);
    try {
      await api.bulkActivateApps(selected);
      setSelected([]);
      appsResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  const bulkDeactivate = async () => {
    if (selected.length === 0) return;
    setConfirmLoading(true);
    try {
      await api.bulkDeactivateApps(selected);
      setSelected([]);
      appsResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  return (
    <div>
      <h2>Aplicações ({appsResource.pagination?.total ?? 0})</h2>

      <DataTable
        columns={[
          { key: "name", header: "Nome", sortable: true },
          { key: "version", header: "Versão", sortable: true },
          { key: "base_path", header: "Base Path" },
          {
            key: "active",
            header: "Status",
            sortable: true,
            render: (row) => (row.active ? "Ativo" : "Inativo"),
          },
        ]}
        data={appsResource.data}
        loading={appsResource.loading}
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
              <button onClick={bulkActivate} disabled={confirmLoading}>
                Ativar ({selected.length})
              </button>
              <button onClick={bulkDeactivate} disabled={confirmLoading}>
                Desativar ({selected.length})
              </button>
              <button
                className="btn-danger"
                onClick={() => {
                  setToDelete(null);
                  setConfirmOpen(true);
                }}
                disabled={confirmLoading}
              >
                Excluir ({selected.length})
              </button>
            </>
          ) : (
            <span className="dt-muted">Selecione apps para ações em massa</span>
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
          appsResource.pagination
            ? {
                page: appsResource.page,
                totalPages: appsResource.pagination.total_pages,
                total: appsResource.pagination.total,
                pageSize: 10,
              }
            : undefined
        }
        onPageChange={appsResource.setPage}
      />

      <Modal
        open={!!editing}
        title="Editar Aplicação"
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
              Nome
              <input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            </label>

            <label>
              Versão
              <input
                value={editing.version ?? ""}
                onChange={(e) => setEditing({ ...editing, version: e.target.value })}
              />
            </label>

            <label>
              Base Path
              <input
                value={editing.base_path ?? ""}
                onChange={(e) => setEditing({ ...editing, base_path: e.target.value })}
              />
            </label>

            <label style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={!!editing.active}
                onChange={(e) => setEditing({ ...editing, active: e.target.checked })}
              />
              Ativo
            </label>
          </>
        )}
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title={toDelete ? "Excluir aplicação" : "Excluir aplicações"}
        message={
          toDelete
            ? `Deseja excluir "${toDelete.name}"?`
            : `Deseja excluir ${selected.length} aplicações selecionadas?`
        }
        confirmText="Excluir"
        danger
        loading={confirmLoading}
        onCancel={() => {
          setConfirmOpen(false);
          setToDelete(null);
        }}
        onConfirm={toDelete ? doDeleteOne : doBulkDelete}
      />
    </div>
  );
};