// src/ui/admin/tabs/GroupsTab.tsx
import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminGroup, AdminRole } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ActionButtons } from "../../../components/ActionButtons";

import { GroupEditModal } from "../modals/GroupEditModal";

export const GroupsTab = () => {
  const { token } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<AdminGroup | null>(null);

  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const groupsResource = usePaginatedResource<AdminGroup>(
    ({ page, pageSize }) => api!.listGroups({ page, pageSize, q: search }),
    10,
    [search]
  );

  if (!api) return null;

  const fetchRoles = async () => {
    const rolesRes = await api.listRoles({ page: 1, pageSize: 999 });
    setRoles(rolesRes.data ?? []);
  };

  const openGroup = async (g: AdminGroup) => {
    setEditing(g);
    setSelectedRoleIds(g.roles.map((r) => r.id));
    await fetchRoles();
  };

  const openNew = async () => {
    setEditing({
      id: "",
      name: "",
      description: "",
      roles: [],
    } as any);
    setSelectedRoleIds([]);
    await fetchRoles();
  };

  const onToggleRole = (roleId: string) => {
    setSelectedRoleIds((prev) =>
      prev.includes(roleId) ? prev.filter((x) => x !== roleId) : [...prev, roleId]
    );
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
      }

      await api.setGroupRoles(groupId, selectedRoleIds);

      setEditing(null);
      groupsResource.refetch();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h2>Grupos ({groupsResource.pagination?.total ?? 0})</h2>

      <DataTable
        columns={[
          { key: "name", header: "Nome" },
          { key: "description", header: "Descrição" },
          { key: "roles", header: "Roles", render: (r) => r.roles.length },
        ]}
        data={groupsResource.data}
        loading={groupsResource.loading}
        searchValue={search}
        onSearchChange={setSearch}
        actions={(row) => <ActionButtons onEdit={() => openGroup(row)} />}
        toolbar={<button onClick={openNew}>Novo Grupo</button>}
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

      <GroupEditModal
        open={!!editing}
        group={editing}
        roles={roles}
        selectedRoleIds={selectedRoleIds}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={save}
        onChangeGroup={(patch) => setEditing((prev) => (prev ? { ...prev, ...patch } : prev))}
        onToggleRole={onToggleRole}
      />
    </div>
  );
};