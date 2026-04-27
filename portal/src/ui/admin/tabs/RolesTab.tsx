// src/ui/admin/tabs/RolesTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type {
  AdminPermission,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { ActionButtons } from "../../../components/ActionButtons";
import { RoleEditModal } from "../modals/RoleEditModal";

export const RolesTab = () => {
  const { getAccessToken } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{
    sort?: string;
    direction?: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
  });

  const [editing, setEditing] = useState<AdminRole | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [deleteOneId, setDeleteOneId] = useState<string | null>(null);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  const [allPerms, setAllPerms] = useState<AdminPermission[]>([]);
  const [selectedPermIds, setSelectedPermIds] = useState<string[]>([]);

  const [saving, setSaving] = useState(false);

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const rolesResource = usePaginatedResource<AdminRole>(
    ({ page, pageSize }) =>
      api.listRoles({
        page,
        pageSize,
        q: search,
        sort: sort.sort,
        direction: sort.direction,
      }),
    10,
    [search, sort.sort, sort.direction]
  );

  const loadCatalogs = async () => {
    const [permissionsRes, usersRes] = await Promise.all([
      api.listPermissions({ page: 1, pageSize: 999 }),
      api.listUsers({ page: 1, pageSize: 999 }),
    ]);

    setAllPerms(permissionsRes.data ?? []);
    setUsers(usersRes.data ?? []);
  };

  const openRole = async (role: AdminRole) => {
    setEditing({ ...role });

    const [permissionsRes, rolePermissions, usersRes, roleUsers] =
      await Promise.all([
        api.listPermissions({ page: 1, pageSize: 999 }),
        api.getRolePermissions(role.id),
        api.listUsers({ page: 1, pageSize: 999 }),
        api.getRoleUsers(role.id),
      ]);

    setAllPerms(permissionsRes.data ?? []);
    setSelectedPermIds(
      (rolePermissions.data ?? []).map((permission) => permission.id)
    );

    setUsers(usersRes.data ?? []);
    setSelectedUserIds((roleUsers.data ?? []).map((user) => user.id));
  };

  const openNew = async () => {
    setEditing({
      id: "",
      name: "",
      description: "",
    } as AdminRole);

    setSelectedPermIds([]);
    setSelectedUserIds([]);

    await loadCatalogs();
  };

  const syncRoleUsers = async (roleId: string) => {
    const current = await api.getRoleUsers(roleId);
    const currentIds = (current.data ?? []).map((user) => user.id);

    const toAdd = selectedUserIds.filter((id) => !currentIds.includes(id));
    const toRemove = currentIds.filter((id) => !selectedUserIds.includes(id));

    await Promise.all([
      ...toAdd.map((userId) => api.addUserToRole(roleId, userId)),
      ...toRemove.map((userId) => api.removeUserFromRole(roleId, userId)),
    ]);
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
        await api.updateRole(editing.id, {
          name: editing.name,
          description: editing.description ?? undefined,
        });

        roleId = editing.id;
      }

      await api.setRolePermissions(roleId, selectedPermIds);
      await syncRoleUsers(roleId);

      setEditing(null);
      rolesResource.refetch();
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteOne = async () => {
    if (!deleteOneId) return;

    await api.deleteRole(deleteOneId);

    setDeleteOneId(null);
    rolesResource.refetch();
  };

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

      <ConfirmDialog
        open={!!deleteOneId}
        title="Excluir papel"
        message="Deseja realmente excluir este papel?"
        confirmText="Excluir"
        danger
        onCancel={() => setDeleteOneId(null)}
        onConfirm={handleDeleteOne}
      />

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
        users={users}
        selectedUserIds={selectedUserIds}
        allPerms={allPerms}
        selectedPermIds={selectedPermIds}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={save}
        onChangeRole={(patch) =>
          setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
        }
        onToggleUser={(userId) =>
          setSelectedUserIds((prev) =>
            prev.includes(userId)
              ? prev.filter((x) => x !== userId)
              : [...prev, userId]
          )
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