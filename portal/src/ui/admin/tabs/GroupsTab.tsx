// src/ui/admin/tabs/GroupsTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminGroup, AdminRole } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ActionButtons } from "../../../components/ActionButtons";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { GroupEditModal } from "../modals/GroupEditModal";

export const GroupsTab = () => {
  const { getAccessToken } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<AdminGroup | null>(null);

  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [deleteOneId, setDeleteOneId] = useState<string | null>(null);

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
      api!.listGroups({
        page,
        pageSize,
        q: search,
        sort: sortState.sort,
        direction: sortState.direction,
      }),
    10,
    [search, sortState]
  );

  if (!api) return null;

  const fetchRoles = async () => {
    const res = await api.listRoles({ page: 1, pageSize: 999 });
    setRoles(res.data ?? []);
  };

  const openGroup = async (g: AdminGroup) => {
    setEditing(g);

    const rolesRes = await api.listRoles({ page: 1, pageSize: 999 });
    setRoles(rolesRes.data ?? []);

    const groupRoles = await api.getGroupRoles(g.id);
    setSelectedRoleIds(groupRoles.data ?? []);
  };

  const openNew = async () => {
    setEditing({ id: "", name: "", description: "" } as any);
    setSelectedRoleIds([]);
    await fetchRoles();
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

      await api.setGroupRoles(groupId, selectedRoleIds);

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
        roles={roles}
        selectedRoleIds={selectedRoleIds}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={save}
        onChangeGroup={(patch) =>
          setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
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