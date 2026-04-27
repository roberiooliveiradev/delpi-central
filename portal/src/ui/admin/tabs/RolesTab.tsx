// src/ui/admin/tabs/RolesTab.tsx

import { useContext, useMemo, useState } from "react";
import {
  Edit,
  KeyRound,
  ShieldCheck,
  Trash2,
  UsersRound,
} from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type {
  AdminApp,
  AdminPermission,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { AdminEntityList } from "../../../components/admin/AdminEntityList";
import { RoleEditModal } from "../modals/RoleEditModal";

export type AppInfoByModule = Record<
  string,
  {
    name?: string | null;
    icon?: string | null;
  }
>;

type RoleSortField = "name" | "description";

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

const normalizeModuleKey = (value: string | null | undefined) => {
  return (value ?? "")
    .trim()
    .toLowerCase()
    .replace(/^\/+/, "")
    .replace(/^apps\//, "");
};

const buildAppInfoByModule = (apps: AdminApp[]): AppInfoByModule => {
  const result: AppInfoByModule = {};

  apps.forEach((app) => {
    const info = {
      name: app.name ?? app.id,
      icon: app.icon ?? null,
    };

    const idKey = normalizeModuleKey(app.id);
    const basePathKey = normalizeModuleKey(app.base_path);

    if (idKey) {
      result[idKey] = info;
    }

    if (basePathKey) {
      result[basePathKey] = info;
    }
  });

  return result;
};

const getRoleInitials = (role: AdminRole) => {
  const source = role.name?.trim() || "Papel";

  const parts = source
    .split(" ")
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return source.slice(0, 2).toUpperCase();
};

export const RolesTab = () => {
  const { getAccessToken } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{
    sort?: RoleSortField;
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

  const [appInfoByModule, setAppInfoByModule] =
    useState<AppInfoByModule>({});

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
    PAGE_SIZE,
    [search, sort.sort, sort.direction]
  );

  const roles = rolesResource.data ?? [];
  const totalRoles = rolesResource.pagination?.total ?? roles.length;
  const totalPages = rolesResource.pagination?.total_pages ?? 1;
  const currentPage = rolesResource.page;

  const loadCatalogs = async () => {
    const [permissionsRes, usersRes, appsRes] = await Promise.all([
      api.listPermissions({ page: 1, pageSize: 999 }),
      api.listUsers({ page: 1, pageSize: 999 }),
      api.listApps({ page: 1, pageSize: 999 }),
    ]);

    setAllPerms(permissionsRes.data ?? []);
    setUsers(usersRes.data ?? []);
    setAppInfoByModule(buildAppInfoByModule(appsRes.data ?? []));
  };

  const openRole = async (role: AdminRole) => {
    setEditing({ ...role });

    const [
      permissionsRes,
      rolePermissions,
      usersRes,
      roleUsers,
      appsRes,
    ] = await Promise.all([
      api.listPermissions({ page: 1, pageSize: 999 }),
      api.getRolePermissions(role.id),
      api.listUsers({ page: 1, pageSize: 999 }),
      api.getRoleUsers(role.id),
      api.listApps({ page: 1, pageSize: 999 }),
    ]);

    setAllPerms(permissionsRes.data ?? []);
    setSelectedPermIds(normalizeIds(rolePermissions.data ?? []));

    setUsers(usersRes.data ?? []);
    setSelectedUserIds(normalizeIds(roleUsers.data ?? []));

    setAppInfoByModule(buildAppInfoByModule(appsRes.data ?? []));
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
    const currentIds = normalizeIds(current.data ?? []);
    const nextIds = normalizeIds(selectedUserIds);

    const toAdd = nextIds.filter((id) => !currentIds.includes(id));
    const toRemove = currentIds.filter((id) => !nextIds.includes(id));

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

      await api.setRolePermissions(roleId, normalizeIds(selectedPermIds));
      await syncRoleUsers(roleId);

      setEditing(null);
      rolesResource.refetch();
    } finally {
      setSaving(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    rolesResource.setPage(1);
  };

  const toggleSort = (field: RoleSortField) => {
    setSort((prev) => {
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

    rolesResource.setPage(1);
  };

  const toggleRoleSelection = (roleId: string) => {
    setSelected((prev) =>
      prev.includes(roleId)
        ? prev.filter((id) => id !== roleId)
        : [...prev, roleId]
    );
  };

  const clearSelection = () => {
    setSelected([]);
  };

  const selectVisibleRoles = () => {
    const visibleIds = roles.map((role) => role.id);

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

  const goToPreviousPage = () => {
    rolesResource.setPage(Math.max(1, currentPage - 1));
  };

  const goToNextPage = () => {
    rolesResource.setPage(Math.min(totalPages, currentPage + 1));
  };

  const sortLabel = sort.direction === "asc" ? "A-Z" : "Z-A";

  return (
    <>
      <AdminEntityList<AdminRole>
        title="Papéis"
        description="Administre papéis, usuários diretos e permissões vinculadas ao RBAC."
        summary={[
          { value: totalRoles, label: "papéis" },
          { value: roles.length, label: "nesta página" },
          { value: selected.length, label: "selecionados" },
        ]}
        search={{
          value: search,
          placeholder: "Buscar por nome ou descrição...",
          onChange: handleSearchChange,
        }}
        toolbarActions={[
          {
            label: `Nome ${sort.sort === "name" ? sortLabel : ""}`,
            active: sort.sort === "name",
            onClick: () => toggleSort("name"),
          },
          {
            label: `Descrição ${sort.sort === "description" ? sortLabel : ""}`,
            active: sort.sort === "description",
            onClick: () => toggleSort("description"),
          },
          {
            label: "Novo Papel",
            primary: true,
            onClick: openNew,
          },
        ]}
        listTitle="Listagem de papéis"
        listSubtitle={`Página ${currentPage} de ${totalPages}`}
        items={roles}
        loading={rolesResource.loading}
        emptyText="Nenhum papel encontrado."
        getId={(role) => role.id}
        selectedIds={selected}
        selectionLabel="papéis selecionados"
        onToggleSelected={toggleRoleSelection}
        onSelectVisible={selectVisibleRoles}
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
          rolesResource.pagination
            ? {
                page: currentPage,
                totalPages,
                onPrevious: goToPreviousPage,
                onNext: goToNextPage,
              }
            : undefined
        }
        renderIcon={getRoleInitials}
        renderTitle={(role) => role.name}
        renderSubtitle={(role) => role.id}
        renderBadges={() => [
          {
            label: (
              <>
                <ShieldCheck size={12} />
                Papel RBAC
              </>
            ),
          },
        ]}
        renderDescription={(role) =>
          role.description || "Sem descrição cadastrada."
        }
        renderMeta={() => [
          <>
            <UsersRound size={13} />
            Usuários diretos gerenciados no modal
          </>,
          <>
            <KeyRound size={13} />
            Permissões vinculadas no modal
          </>,
        ]}
        renderActions={(role) => [
          {
            label: (
              <>
                <Edit size={14} />
                Editar
              </>
            ),
            onClick: () => openRole(role),
          },
          {
            label: (
              <>
                <Trash2 size={14} />
                Excluir
              </>
            ),
            danger: true,
            onClick: () => setDeleteOneId(role.id),
          },
        ]}
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
        appInfoByModule={appInfoByModule}
        saving={saving}
        onClose={() => setEditing(null)}
        onSave={save}
        onChangeRole={(patch) =>
          setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
        }
        onChangeUserIds={setSelectedUserIds}
        onChangePermissionIds={setSelectedPermIds}
      />
    </>
  );
};