// src/ui/admin/tabs/GroupsTab.tsx

import { useContext, useMemo, useState } from "react";
import {
  Edit,
  ShieldCheck,
  Trash2,
  UsersRound,
} from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type {
  AdminGroup,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { AdminEntityList } from "../../../components/admin/AdminEntityList";
import { GroupEditModal } from "../modals/GroupEditModal";

type GroupSortField = "name" | "description";

const PAGE_SIZE = 10;

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

const getGroupInitials = (group: AdminGroup) => {
  const source = group.name?.trim() || "Grupo";

  const parts = source
    .split(" ")
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return source.slice(0, 2).toUpperCase();
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

  const [sortState, setSortState] = useState<{
    sort: GroupSortField;
    direction: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
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
    PAGE_SIZE,
    [search, sortState.sort, sortState.direction]
  );

  const groups = groupsResource.data ?? [];

  const totalGroups = groupsResource.pagination?.total ?? groups.length;
  const totalPages = groupsResource.pagination?.total_pages ?? 1;
  const currentPage = groupsResource.page;

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

      await api.setGroupRoles(groupId, normalizeIds(selectedRoleIds));
      await syncGroupUsers(groupId);

      setEditing(null);
      groupsResource.refetch();
    } finally {
      setSaving(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    groupsResource.setPage(1);
  };

  const toggleSort = (field: GroupSortField) => {
    setSortState((prev) => {
      if (prev.sort === field) {
        return {
          sort: field,
          direction: prev.direction === "asc" ? "desc" : "asc",
        };
      }

      return {
        sort: field,
        direction: "asc",
      };
    });

    groupsResource.setPage(1);
  };

  const toggleGroupSelection = (groupId: string) => {
    setSelected((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    );
  };

  const clearSelection = () => {
    setSelected([]);
  };

  const selectVisibleGroups = () => {
    const visibleIds = groups.map((group) => group.id);

    setSelected((prev) => {
      const next = new Set(prev);

      visibleIds.forEach((id) => {
        next.add(id);
      });

      return Array.from(next);
    });
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

  const goToPreviousPage = () => {
    groupsResource.setPage(Math.max(1, currentPage - 1));
  };

  const goToNextPage = () => {
    groupsResource.setPage(Math.min(totalPages, currentPage + 1));
  };

  const sortLabel = sortState.direction === "asc" ? "A-Z" : "Z-A";

  return (
    <>
      <AdminEntityList<AdminGroup>
        title="Grupos"
        description="Administre agrupamentos de usuários e os papéis herdados por cada grupo."
        summary={[
          { value: totalGroups, label: "grupos" },
          { value: groups.length, label: "nesta página" },
          { value: selected.length, label: "selecionados" },
        ]}
        search={{
          value: search,
          placeholder: "Buscar por nome ou descrição...",
          onChange: handleSearchChange,
        }}
        toolbarActions={[
          {
            label: `Nome ${sortState.sort === "name" ? sortLabel : ""}`,
            active: sortState.sort === "name",
            onClick: () => toggleSort("name"),
          },
          {
            label: `Descrição ${
              sortState.sort === "description" ? sortLabel : ""
            }`,
            active: sortState.sort === "description",
            onClick: () => toggleSort("description"),
          },
          {
            label: "Novo Grupo",
            primary: true,
            onClick: openNew,
          },
        ]}
        listTitle="Listagem de grupos"
        listSubtitle={`Página ${currentPage} de ${totalPages}`}
        items={groups}
        loading={groupsResource.loading}
        emptyText="Nenhum grupo encontrado."
        getId={(group) => group.id}
        selectedIds={selected}
        selectionLabel="grupos selecionados"
        onToggleSelected={toggleGroupSelection}
        onSelectVisible={selectVisibleGroups}
        onClearSelection={clearSelection}
        bulkActions={[
          {
            label: (
              <>
                <Trash2 size={14} />
                Excluir selecionados
              </>
            ),
            danger: true,
            onClick: () => setConfirmBulk(true),
          },
        ]}
        pagination={
          groupsResource.pagination
            ? {
                page: currentPage,
                totalPages,
                onPrevious: goToPreviousPage,
                onNext: goToNextPage,
              }
            : undefined
        }
        renderIcon={getGroupInitials}
        renderTitle={(group) => group.name}
        renderSubtitle={(group) => group.id}
        renderBadges={() => [
          {
            label: (
              <>
                <UsersRound size={12} />
                Grupo RBAC
              </>
            ),
          },
        ]}
        renderDescription={(group) =>
          group.description || "Sem descrição cadastrada."
        }
        renderMeta={() => [
          <>
            <ShieldCheck size={13} />
            Usuários e papéis gerenciados no modal
          </>,
        ]}
        renderActions={(group) => [
          {
            label: (
              <>
                <Edit size={14} />
                Editar
              </>
            ),
            onClick: () => openGroup(group),
          },
          {
            label: (
              <>
                <Trash2 size={14} />
                Excluir
              </>
            ),
            danger: true,
            onClick: () => setDeleteOneId(group.id),
          },
        ]}
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
        onChangeUserIds={setSelectedUserIds}
        onChangeRoleIds={setSelectedRoleIds}
      />
    </>
  );
};