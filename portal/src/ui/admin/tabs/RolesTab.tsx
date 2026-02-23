// src/ui/admin/tabs/RolesTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminRole } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { Modal } from "../../../components/Modal";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { ActionButtons } from "../../../components/ActionButtons";

export const RolesTab = () => {
  const { token } = useContext(AuthContext);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<AdminRole | null>(null);
  const [deleting, setDeleting] = useState<AdminRole | null>(null);
  const [selected, setSelected] = useState<string[]>([]);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const rolesResource = usePaginatedResource<AdminRole>(
    ({ page, pageSize }) =>
      api!.listRoles({ page, pageSize, q: search }),
    10,
    [search]
  );

  const handleDelete = async () => {
    if (!deleting) return;
    await api!.deleteRole(deleting.id);
    setDeleting(null);
    rolesResource.setPage(1);
  };

  const handleBulkDelete = async () => {
    await api!.bulkDeleteRoles(selected);
    setSelected([]);
    rolesResource.setPage(1);
  };

  if (!api) return null;

  return (
    <div>
      <h2>Roles ({rolesResource.pagination?.total ?? 0})</h2>

      <DataTable
        columns={[
          { key: "name", header: "Nome", sortable: true },
          { key: "description", header: "Descrição" },
        ]}
        data={rolesResource.data}
        loading={rolesResource.loading}
        searchValue={search}
        onSearchChange={setSearch}
        selectable
        getRowId={(r) => r.id}
        selectedRows={selected}
        onSelectionChange={setSelected}
        actions={(row) => (
          <ActionButtons
            onEdit={() => setEditing(row)}
            onDelete={() => setDeleting(row)}
          />
        )}
        toolbar={
          selected.length > 0 && (
            <button
              className="danger"
              onClick={handleBulkDelete}
            >
              Excluir selecionados ({selected.length})
            </button>
          )
        }
        pagination={
          rolesResource.pagination
            ? {
                page: rolesResource.page,
                totalPages:
                  rolesResource.pagination.total_pages,
                total: rolesResource.pagination.total,
                pageSize: 10,
              }
            : undefined
        }
        onPageChange={rolesResource.setPage}
      />

      {/* EDIT MODAL */}
      <Modal
        open={!!editing}
        title="Editar Role"
        onClose={() => setEditing(null)}
        footer={
          <>
            <button onClick={() => setEditing(null)}>
              Cancelar
            </button>
            <button
              onClick={async () => {
                await api!.updateRole(editing!.id, editing!);
                setEditing(null);
                rolesResource.setPage(1);
              }}
            >
              Salvar
            </button>
          </>
        }
      >
        {editing && (
          <>
            <input
              value={editing.name}
              onChange={(e) =>
                setEditing({
                  ...editing,
                  name: e.target.value,
                })
              }
            />
            <textarea
              value={editing.description ?? ""}
              onChange={(e) =>
                setEditing({
                  ...editing,
                  description: e.target.value,
                })
              }
            />
          </>
        )}
      </Modal>

      {/* DELETE CONFIRM */}
      <ConfirmDialog
        open={!!deleting}
        message={`Deseja excluir a role "${deleting?.name}"?`}
        onCancel={() => setDeleting(null)}
        onConfirm={handleDelete}
      />
    </div>
  );
};