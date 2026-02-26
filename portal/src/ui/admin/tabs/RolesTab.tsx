// src/ui/admin/tabs/RolesTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminPermission, AdminRole } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { ActionButtons } from "../../../components/ActionButtons";
import { RoleEditModal } from "../modals/RoleEditModal";

export const RolesTab = () => {
  const { token } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ sort?: string; direction?: "asc" | "desc" }>({
    sort: "name",
    direction: "asc",
  });

  const [editing, setEditing] = useState<AdminRole | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [deleteOneId, setDeleteOneId] = useState<string | null>(null);

  const [allPerms, setAllPerms] = useState<AdminPermission[]>([]);
  const [selectedPermIds, setSelectedPermIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const rolesResource = usePaginatedResource<AdminRole>(
    ({ page, pageSize }) =>
      api!.listRoles({
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

  const fetchPermissions = async () => {
    const res = await api.listPermissions({ page: 1, pageSize: 999 });
    setAllPerms(res.data ?? []);
  };

  const openRole = async (role: AdminRole) => {
    setEditing(role);
    setSelectedPermIds(role.permissions.map((p) => p.id));
    await fetchPermissions();
  };

  const openNew = async () => {
    setEditing({ id: "", name: "", description: "", permissions: [] } as any);
    setSelectedPermIds([]);
    await fetchPermissions();
  };

  const save = async () => {
    if (!editing) return;

    setSaving(true);
    try {
      let roleId: string;

      if (!editing.id) {
        const created = await api.createRole({
          name: editing.name,
          description: editing.description ?? undefined,
        });

        roleId = created.id;
      } else {
        roleId = editing.id;
      }

      await api.setRolePermissions(roleId, selectedPermIds);

      setEditing(null);
      rolesResource.refetch();
    } finally {
      setSaving(false);
    }
  };

  // ================================
  // DELETE INDIVIDUAL
  // ================================
  const handleDeleteOne = async () => {
    if (!deleteOneId) return;

    await api.deleteRole(deleteOneId);

    setDeleteOneId(null);
    rolesResource.refetch();
  };

  // ================================
  // DELETE BULK
  // ================================
  const handleBulkDelete = async () => {
    if (selected.length === 0) return;

    await api.bulkDeleteRoles(selected);

    setSelected([]);
    setConfirmBulk(false);
    rolesResource.refetch();
  };

  return (
    <div>
      <DataTable
        columns={[
          { key: "name", header: "Nome", sortable: true },
          { key: "description", header: "Descrição" },
          {
            key: "permissions",
            header: "Permissões",
            render: (row) => row.permissions.length,
          },
        ]}
        data={rolesResource.data}
        loading={rolesResource.loading}
        searchValue={search}
        onSearchChange={setSearch}
        sort={sort}
        onSortChange={setSort}
        selectable
        getRowId={(row) => row.id}
        selectedRows={selected}
        onSelectionChange={setSelected}
        actions={(row) => (
          <ActionButtons
            onEdit={() => openRole(row)}
            onDelete={() => setDeleteOneId(row.id)}
          />
        )}
        toolbar={
          <>
            <button onClick={openNew}>Novo Papel</button>

            {selected.length > 0 && (
              <button
                className="btn-danger"
                onClick={() => setConfirmBulk(true)}
              >
                Excluir selecionados ({selected.length})
              </button>
            )}
          </>
        }
        pagination={
          rolesResource.pagination && {
            page: rolesResource.page,
            totalPages: rolesResource.pagination.total_pages,
            total: rolesResource.pagination.total,
            pageSize: 10,
          }
        }
        onPageChange={rolesResource.setPage}
      />

      {/* Confirmação delete individual */}
      <ConfirmDialog
        open={!!deleteOneId}
        title="Excluir papel"
        message="Deseja realmente excluir este papel?"
        confirmText="Excluir"
        danger
        onCancel={() => setDeleteOneId(null)}
        onConfirm={handleDeleteOne}
      />

      {/* Confirmação delete múltiplo */}
      <ConfirmDialog
        open={confirmBulk}
        title="Excluir papéis"
        message={`Deseja excluir ${selected.length} papéis?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmBulk(false)}
        onConfirm={handleBulkDelete}
      />

      <RoleEditModal
        open={!!editing}
        role={editing}
        allPerms={allPerms}
        selectedPermIds={selectedPermIds}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={save}
        onChangeRole={(patch) =>
          setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
        }
        onTogglePerm={(permId) =>
          setSelectedPermIds((prev) =>
            prev.includes(permId)
              ? prev.filter((x) => x !== permId)
              : [...prev, permId]
          )
        }
      />
    </div>
  );
};