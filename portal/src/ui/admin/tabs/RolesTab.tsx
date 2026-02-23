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
  const [editing, setEditing] = useState<AdminRole | null>(null);
  const [deleting, setDeleting] = useState<AdminRole | null>(null);

  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulk, setConfirmBulk] = useState(false);

  const [allPerms, setAllPerms] = useState<AdminPermission[]>([]);
  const [selectedPermIds, setSelectedPermIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const rolesResource = usePaginatedResource<AdminRole>(
    ({ page, pageSize }) => api!.listRoles({ page, pageSize, q: search }),
    10,
    [search]
  );

  if (!api) return null;

  const fetchPerms = async () => {
    const permsRes = await api.listPermissions({ page: 1, pageSize: 999 });
    setAllPerms(permsRes.data ?? []);
  };

  const openRole = async (role: AdminRole) => {
    setEditing(role);
    setSelectedPermIds(role.permissions.map((p) => p.id));
    await fetchPerms();
  };

  const openNew = async () => {
    setEditing({
      id: "",
      name: "",
      description: "",
      permissions: [],
    } as any);
    setSelectedPermIds([]);
    await fetchPerms();
  };

  const onTogglePerm = (permId: string) => {
    setSelectedPermIds((prev) =>
      prev.includes(permId) ? prev.filter((x) => x !== permId) : [...prev, permId]
    );
  };

  const save = async () => {
    if (!editing) return;

    setSaving(true);
    try {
      let roleId = editing.id;

      if (!roleId) {
        const created = await api.createRole({
          name: editing.name,
          description: editing.description,
        });
        roleId = created.id;
      }

      await api.setRolePermissions(roleId, selectedPermIds);

      setEditing(null);
      rolesResource.refetch();
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleting) return;
    await api.deleteRole(deleting.id);
    setDeleting(null);
    rolesResource.refetch();
  };

  const handleBulkDelete = async () => {
    await api.bulkDeleteRoles(selected);
    setSelected([]);
    setConfirmBulk(false);
    rolesResource.refetch();
  };

  return (
    <div>
      <h2>Papéis ({rolesResource.pagination?.total ?? 0})</h2>

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
        selectable
        getRowId={(r) => r.id}
        selectedRows={selected}
        onSelectionChange={setSelected}
        actions={(row) => (
          <ActionButtons onEdit={() => openRole(row)} onDelete={() => setDeleting(row)} />
        )}
        toolbar={
          <>
            <button onClick={openNew}>Novo Papel</button>
            {selected.length > 0 && (
              <button className="danger" onClick={() => setConfirmBulk(true)}>
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

      <RoleEditModal
        open={!!editing}
        role={editing}
        allPerms={allPerms}
        selectedPermIds={selectedPermIds}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={save}
        onChangeRole={(patch) => setEditing((prev) => (prev ? { ...prev, ...patch } : prev))}
        onTogglePerm={onTogglePerm}
      />

      <ConfirmDialog
        open={!!deleting}
        title="Excluir papel"
        message={`Deseja excluir "${deleting?.name}"?`}
        onCancel={() => setDeleting(null)}
        onConfirm={handleDelete}
      />

      <ConfirmDialog
        open={confirmBulk}
        title="Excluir papéis"
        message={`Deseja excluir ${selected.length} roles?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmBulk(false)}
        onConfirm={handleBulkDelete}
      />
    </div>
  );
};