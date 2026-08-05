// src/ui/admin/tabs/RolesTab.tsx

import { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Edit, KeyRound, ShieldCheck, Trash2, UsersRound } from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminRole } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { AdminEntityList } from "../../../components/admin/AdminEntityList";

export type AppInfoByModule = Record<
  string,
  {
    name?: string | null;
    icon?: string | null;
  }
>;

type RoleSortField = "name" | "description";

const PAGE_SIZE = 10;

const getRoleInitials = (role: AdminRole) => {
  const parts = (role.name || "?").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
};

export const RolesTab = () => {
  const { getAccessToken } = useContext(AuthContext);
  const navigate = useNavigate();

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{
    sort?: RoleSortField;
    direction?: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
  });

  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [deleteOneId, setDeleteOneId] = useState<string | null>(null);

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

  const openRole = (role: AdminRole) => {
    navigate(`/admin/roles/${role.id}`);
  };

  const openNew = () => {
    navigate("/admin/roles/new");
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
      visibleIds.forEach((id) => next.add(id));
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
            Usuários e permissões na página do papel
          </>,
          <>
            <KeyRound size={13} />
            Abrir para conceder codes de apps
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
    </>
  );
};
