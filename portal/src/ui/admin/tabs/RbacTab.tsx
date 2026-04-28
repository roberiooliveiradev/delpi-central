// src/ui/admin/tabs/RbacTab.tsx

import { useContext, useMemo, useState } from "react";
import { ShieldCheck, UserRound } from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminUser } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { AdminEntityList } from "../../../components/admin/AdminEntityList";
import { UserRbacModal } from "../modals/UserRbacModal";

type UserSortField = "name" | "email" | "is_superadmin";

const PAGE_SIZE = 10;

const getInitials = (user: AdminUser) => {
  const source = user.name?.trim() || user.email?.trim() || "?";

  const parts = source
    .split(" ")
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return source.slice(0, 2).toUpperCase();
};

const getUserStatusLabel = (user: AdminUser) => {
  return user.active === false ? "Inativo" : "Ativo";
};

const formatBrazilDateTime = (value?: string | null) => {
  if (!value) return "Nunca acessou";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Data inválida";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
};

export const RbacTab = () => {
  const { getAccessToken } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{
    sort?: UserSortField;
    direction?: "asc" | "desc";
  }>({
    sort: "email",
    direction: "asc",
  });

  const [selected, setSelected] = useState<string[]>([]);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [confirmBulk, setConfirmBulk] = useState(false);

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const usersResource = usePaginatedResource<AdminUser>(
    ({ page, pageSize }) =>
      api.listUsers({
        page,
        pageSize,
        q: search,
        sort: sort.sort,
        direction: sort.direction,
      }),
    PAGE_SIZE,
    [search, sort.sort, sort.direction]
  );

  const users = usersResource.data ?? [];
  const totalUsers = usersResource.pagination?.total ?? users.length;
  const totalPages = usersResource.pagination?.total_pages ?? 1;
  const currentPage = usersResource.page;

  const superadminCount = users.filter((user) => user.is_superadmin).length;
  const activeCount = users.filter((user) => user.active !== false).length;

  const handleSearchChange = (value: string) => {
    setSearch(value);
    usersResource.setPage(1);
  };

  const toggleSort = (field: UserSortField) => {
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

    usersResource.setPage(1);
  };

  const toggleUserSelection = (userId: string) => {
    setSelected((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    );
  };

  const clearSelection = () => {
    setSelected([]);
  };

  const selectVisibleUsers = () => {
    const visibleIds = users.map((user) => user.id);

    setSelected((prev) => {
      const next = new Set(prev);

      visibleIds.forEach((id) => {
        next.add(id);
      });

      return Array.from(next);
    });
  };

  const handleBulkDelete = async () => {
    if (selected.length === 0) return;

    await api.bulkDeleteUsers(selected);

    setSelected([]);
    setConfirmBulk(false);
    usersResource.refetch();
  };

  const goToPreviousPage = () => {
    usersResource.setPage(Math.max(1, currentPage - 1));
  };

  const goToNextPage = () => {
    usersResource.setPage(Math.min(totalPages, currentPage + 1));
  };

  const sortLabel = sort.direction === "asc" ? "A-Z" : "Z-A";

  return (
    <>
      <AdminEntityList<AdminUser>
        title="Usuários"
        description="Administre usuários, papéis diretos, grupos e privilégios administrativos."
        summary={[
          { value: totalUsers, label: "usuários" },
          { value: activeCount, label: "ativos nesta página" },
          { value: superadminCount, label: "superadmins nesta página" },
        ]}
        search={{
          value: search,
          placeholder: "Buscar por nome ou email...",
          onChange: handleSearchChange,
        }}
        toolbarActions={[
          {
            label: `Nome ${sort.sort === "name" ? sortLabel : ""}`,
            active: sort.sort === "name",
            onClick: () => toggleSort("name"),
          },
          {
            label: `Email ${sort.sort === "email" ? sortLabel : ""}`,
            active: sort.sort === "email",
            onClick: () => toggleSort("email"),
          },
          {
            label: "Superadmin",
            active: sort.sort === "is_superadmin",
            onClick: () => toggleSort("is_superadmin"),
          },
        ]}
        listTitle="Listagem de usuários"
        listSubtitle={`Página ${currentPage} de ${totalPages}`}
        items={users}
        loading={usersResource.loading}
        emptyText="Nenhum usuário encontrado."
        getId={(user) => user.id}
        selectedIds={selected}
        selectionLabel="usuários selecionados"
        onToggleSelected={toggleUserSelection}
        onSelectVisible={selectVisibleUsers}
        onClearSelection={clearSelection}
        bulkActions={[
          {
            label: "Excluir selecionados",
            danger: true,
            onClick: () => setConfirmBulk(true),
          },
        ]}
        pagination={
          usersResource.pagination
            ? {
                page: currentPage,
                totalPages,
                onPrevious: goToPreviousPage,
                onNext: goToNextPage,
              }
            : undefined
        }
        renderIcon={getInitials}
        renderTitle={(user) => user.name || "Usuário sem nome"}
        renderSubtitle={(user) => user.email}
        renderBadges={(user) => [
          {
            label: getUserStatusLabel(user),
            tone: user.active === false ? "danger" : "success",
          },
          ...(user.is_superadmin
            ? [
                {
                  label: (
                    <>
                      <ShieldCheck size={12} />
                      Superadmin
                    </>
                  ),
                  tone: "warning" as const,
                },
              ]
            : []),
        ]}
        renderMeta={(user) => [
          <>
            <UserRound size={13} />
            ID: {user.id}
          </>,
          `Último login: ${formatBrazilDateTime(user.last_login_at)}`,
        ]}
        renderActions={(user) => [
          {
            label: "Editar RBAC",
            onClick: () => setEditing(user),
          },
        ]}
      />

      <ConfirmDialog
        open={confirmBulk}
        title="Excluir usuários"
        message={`Deseja excluir ${selected.length} usuários?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmBulk(false)}
        onConfirm={handleBulkDelete}
      />

      <UserRbacModal
        open={!!editing}
        user={editing}
        api={api}
        onClose={() => setEditing(null)}
        onSaved={() => usersResource.refetch()}
      />
    </>
  );
};