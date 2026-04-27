// src/ui/admin/tabs/GroupsTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminGroup, AdminRole, AdminUser } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ActionButtons } from "../../../components/ActionButtons";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { GroupEditModal } from "../modals/GroupEditModal";

const normalizeIds = (items: unknown[]): string[] => {
  return items
    .map((item) => {
      if (typeof item === "string") return item;

      if (
        item &&
        typeof item === "object" &&
        "id" in item &&
        typeof (item as { id?: unknown }).id === "string"
      ) {
        return (item as { id: string }).id;
      }

      return null;
    })
    .filter((id): id is string => !!id);
};

export const GroupsTab = () => {
  const { getAccessToken } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<AdminGroup | null>(null);

  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [deleteOneId, setDeleteOneId] = useState<string | null>(null);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);

  const [saving, setSaving] = useState(false);

  const [sortState, setSortState] = useState({
    sort: "name",
    direction: "asc" as "asc" | "desc",
  });

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const groupsResource = usePaginatedResource<AdminGroup>(
    ({ page, pageSize }) =>
      api.listGroups({
        page,
        pageSize,
        q: search,
        sort: sortState.sort,
        direction: sortState.direction,
      }),
    10,
    [search, sortState.sort, sortState.direction]
  );

  const loadCatalogs = async () => {
    const [rolesRes, usersRes] = await Promise.all([
      api.listRoles({ page: 1, pageSize: 999 }),
      api.listUsers({ page: 1, pageSize: 999 }),
    ]);

    setRoles(rolesRes.data ?? []);
    setUsers(usersRes.data ?? []);
  };

  const openGroup = async (group: AdminGroup) => {
    setEditing({ ...group });

    const [rolesRes, groupRoles, usersRes, groupUsers] = await Promise.all([
      api.listRoles({ page: 1, pageSize: 999 }),
      api.getGroupRoles(group.id),
      api.listUsers({ page: 1, pageSize: 999 }),
      api.getGroupUsers(group.id),
    ]);

    setRoles(rolesRes.data ?? []);
    setSelectedRoleIds(normalizeIds(groupRoles.data ?? []));

    setUsers(usersRes.data ?? []);
    setSelectedUserIds(normalizeIds(groupUsers.data ?? []));
  };

  const openNew = async () => {
    setEditing({
      id: "",
      name: "",
      description: "",
    } as AdminGroup);

    setSelectedRoleIds([]);
    setSelectedUserIds([]);

    await loadCatalogs();
  };

  const syncGroupUsers = async (groupId: string) => {
    const current = await api.getGroupUsers(groupId);
    const currentIds = normalizeIds(current.data ?? []);
    const nextIds = normalizeIds(selectedUserIds);

    const toAdd = nextIds.filter((id) => !currentIds.includes(id));
    const toRemove = currentIds.filter((id) => !nextIds.includes(id));

    await Promise.all([
      ...toAdd.map((userId) => api.addUserToGroup(groupId, userId)),
      ...toRemove.map((userId) => api.removeUserFromGroup(groupId, userId)),
    ]);
  };

  const save = async () => {
    if (!editing) return;

    setSaving(true);

    try {
      let groupId = editing.id;

      if (!groupId) {
        const created = await api.createGroup({
          name: editing.name,
          description: editing.description,
        });

        groupId = created.id;
      } else {
        await api.updateGroup(groupId, {
          name: editing.name,
          description: editing.description,
        });
      }

      const roleIds = normalizeIds(selectedRoleIds);

      await api.setGroupRoles(groupId, roleIds);
      await syncGroupUsers(groupId);

      setEditing(null);
      groupsResource.refetch();
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteOne = async () => {
    if (!deleteOneId) return;

    await api.deleteGroup(deleteOneId);

    setDeleteOneId(null);
    groupsResource.refetch();
  };

  const handleBulkDelete = async () => {
    if (selected.length === 0) return;

    await api.bulkDeleteGroups(selected);

    setSelected([]);
    setConfirmBulk(false);
    groupsResource.refetch();
  };

  return (
    <div>
      <DataTable
        columns={[
          { key: "name", header: "Nome", sortable: true },
          { key: "description", header: "Descrição" },
        ]}
        data={groupsResource.data}
        loading={groupsResource.loading}
        searchValue={search}
        onSearchChange={setSearch}
        sort={sortState}
        onSortChange={(next) =>
          setSortState({
            sort: next.sort ?? "name",
            direction: next.direction ?? "asc",
          })
        }
        selectable
        getRowId={(row) => row.id}
        selectedRows={selected}
        onSelectionChange={setSelected}
        actions={(row) => (
          <ActionButtons
            onEdit={() => openGroup(row)}
            onDelete={() => setDeleteOneId(row.id)}
          />
        )}
        toolbar={
          <>
            <button onClick={openNew}>Novo Grupo</button>

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
          groupsResource.pagination && {
            page: groupsResource.page,
            totalPages: groupsResource.pagination.total_pages,
            total: groupsResource.pagination.total,
            pageSize: 10,
          }
        }
        onPageChange={groupsResource.setPage}
      />

      <ConfirmDialog
        open={!!deleteOneId}
        title="Excluir grupo"
        message="Deseja realmente excluir este grupo?"
        confirmText="Excluir"
        danger
        onCancel={() => setDeleteOneId(null)}
        onConfirm={handleDeleteOne}
      />

      <ConfirmDialog
        open={confirmBulk}
        title="Excluir grupos"
        message={`Deseja excluir ${selected.length} grupos?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmBulk(false)}
        onConfirm={handleBulkDelete}
      />

      <GroupEditModal
        open={!!editing}
        group={editing}
        users={users}
        selectedUserIds={selectedUserIds}
        roles={roles}
        selectedRoleIds={selectedRoleIds}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={save}
        onChangeGroup={(patch) =>
          setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
        }
        onToggleUser={(userId) =>
          setSelectedUserIds((prev) =>
            prev.includes(userId)
              ? prev.filter((x) => x !== userId)
              : [...prev, userId]
          )
        }
        onToggleRole={(roleId) =>
          setSelectedRoleIds((prev) =>
            prev.includes(roleId)
              ? prev.filter((x) => x !== roleId)
              : [...prev, roleId]
          )
        }
      />
    </div>
  );
};