// src/ui/admin/tabs/RbacTab.tsx

import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Circle, ShieldCheck, UserRound } from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type {
  AdminGroup,
  AdminRole,
  AdminUser,
  OnlineUserPresence,
} from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { AdminEntityList } from "../../../components/admin/AdminEntityList";
import { UserRbacModal } from "../modals/UserRbacModal";

type UserSortField = "name" | "email";

type UserListFilters = {
  online?: "true" | "false";
  isSuperadmin?: boolean;
  roleId?: string;
  groupId?: string;
};

const PAGE_SIZE = 10;
const FILTER_OPTIONS_PAGE_SIZE = 500;

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
  const [anonymizing, setAnonymizing] = useState<AdminUser | null>(null);
  const [onlineByUserId, setOnlineByUserId] = useState<
    Map<string, OnlineUserPresence>
  >(() => new Map());
  const [onlineTotal, setOnlineTotal] = useState(0);
  const [presenceEnabled, setPresenceEnabled] = useState(true);
  const [filters, setFilters] = useState<UserListFilters>({});
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const loadOnlineUsers = useCallback(async () => {
    try {
      const data = await api.listOnlineUsers();
      setPresenceEnabled(data.enabled);

      if (!data.enabled) {
        setOnlineByUserId(new Map());
        setOnlineTotal(0);
        return;
      }

      setOnlineTotal(data.total);
      setOnlineByUserId(
        new Map(data.items.map((item) => [item.userId, item])),
      );
    } catch {
      // polling silencioso — lista de usuários segue funcionando
    }
  }, [api]);

  useEffect(() => {
    void loadOnlineUsers();
    const intervalId = window.setInterval(() => void loadOnlineUsers(), 30_000);
    return () => window.clearInterval(intervalId);
  }, [loadOnlineUsers]);

  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const [rolesResponse, groupsResponse] = await Promise.all([
          api.listRoles({ page: 1, pageSize: FILTER_OPTIONS_PAGE_SIZE, sort: "name" }),
          api.listGroups({ page: 1, pageSize: FILTER_OPTIONS_PAGE_SIZE, sort: "name" }),
        ]);

        setRoles(rolesResponse.data ?? []);
        setGroups(groupsResponse.data ?? []);
      } catch {
        // selects ficam vazios; filtros por papel/grupo seguem opcionais
      }
    };

    void loadFilterOptions();
  }, [api]);

  const hasActiveFilters =
    filters.online !== undefined ||
    filters.isSuperadmin !== undefined ||
    !!filters.roleId ||
    !!filters.groupId;

  const usersResource = usePaginatedResource<AdminUser>(
    ({ page, pageSize }) =>
      api.listUsers({
        page,
        pageSize,
        q: search || undefined,
        sort: sort.sort,
        direction: sort.direction,
        online: filters.online,
        isSuperadmin: filters.isSuperadmin,
        roleId: filters.roleId,
        groupId: filters.groupId,
      }),
    PAGE_SIZE,
    [
      search,
      sort.sort,
      sort.direction,
      filters.online,
      filters.isSuperadmin,
      filters.roleId,
      filters.groupId,
    ]
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

  const applyFilters = (patch: Partial<UserListFilters>) => {
    setFilters((prev) => {
      const next = { ...prev, ...patch };

      Object.entries(patch).forEach(([key, value]) => {
        if (value === undefined) {
          delete next[key as keyof UserListFilters];
        }
      });

      return next;
    });
    usersResource.setPage(1);
  };

  const toggleOnlineFilter = (value: "true" | "false") => {
    applyFilters({
      online: filters.online === value ? undefined : value,
    });
  };

  const toggleSuperadminFilter = (value: boolean) => {
    applyFilters({
      isSuperadmin: filters.isSuperadmin === value ? undefined : value,
    });
  };

  const clearFilters = () => {
    setFilters({});
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

  const handleAnonymize = async () => {
    if (!anonymizing) return;

    try {
      await api.anonymizeUser(anonymizing.id);
      usersResource.refetch();
    } catch {
      alert("Erro ao anonimizar dados do usuário.");
    } finally {
      setAnonymizing(null);
    }
  };

  const goToPreviousPage = () => {
    usersResource.setPage(Math.max(1, currentPage - 1));
  };

  const goToNextPage = () => {
    usersResource.setPage(Math.min(totalPages, currentPage + 1));
  };

  const sortLabel = sort.direction === "asc" ? "A-Z" : "Z-A";

  const formatPresenceSessions = (presence: OnlineUserPresence) => {
    if (presence.connectionCount <= 1) {
      return "1 sessão no portal";
    }

    return `${presence.connectionCount} sessões no portal`;
  };

  const renderPresenceMeta = (user: AdminUser) => {
    if (!presenceEnabled) {
      return null;
    }

    const presence = onlineByUserId.get(user.id);

    if (presence) {
      return (
        <span className="admin-user-presence-meta admin-user-presence-meta--online">
          <span className="admin-user-presence-meta__dot" aria-hidden="true" />
          Online agora · {formatPresenceSessions(presence)}
        </span>
      );
    }

    return (
      <span className="admin-user-presence-meta admin-user-presence-meta--offline">
        Offline no portal
      </span>
    );
  };

  return (
    <>
      <AdminEntityList<AdminUser>
        title="Usuários"
        description="Administre usuários, papéis diretos, grupos e privilégios administrativos."
        summary={[
          { value: totalUsers, label: "usuários" },
          { value: onlineTotal, label: "online agora" },
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
            label: `Ordenar: Nome ${sort.sort === "name" ? sortLabel : ""}`,
            active: sort.sort === "name",
            onClick: () => toggleSort("name"),
          },
          {
            label: `Ordenar: Email ${sort.sort === "email" ? sortLabel : ""}`,
            active: sort.sort === "email",
            onClick: () => toggleSort("email"),
          },
        ]}
        filterSlot={
          <>
            <div className="admin-entity-filters__group">
              <span className="admin-entity-filters__label">Filtrar:</span>
              {presenceEnabled ? (
                <>
                  <button
                    type="button"
                    className={filters.online === "true" ? "active" : ""}
                    onClick={() => toggleOnlineFilter("true")}
                  >
                    Online
                  </button>
                  <button
                    type="button"
                    className={filters.online === "false" ? "active" : ""}
                    onClick={() => toggleOnlineFilter("false")}
                  >
                    Offline
                  </button>
                </>
              ) : null}
              <button
                type="button"
                className={filters.isSuperadmin === true ? "active" : ""}
                onClick={() => toggleSuperadminFilter(true)}
              >
                Superadmin
              </button>
              <button
                type="button"
                className={filters.isSuperadmin === false ? "active" : ""}
                onClick={() => toggleSuperadminFilter(false)}
              >
                Não superadmin
              </button>
              {hasActiveFilters ? (
                <button type="button" onClick={clearFilters}>
                  Limpar filtros
                </button>
              ) : null}
            </div>
            <div className="admin-entity-filters__group">
              <label className="admin-entity-filters__label" htmlFor="user-filter-role">
                Papel
              </label>
              <select
                id="user-filter-role"
                value={filters.roleId ?? ""}
                onChange={(event) =>
                  applyFilters({
                    roleId: event.target.value || undefined,
                  })
                }
              >
                <option value="">Todos os papéis</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="admin-entity-filters__group">
              <label className="admin-entity-filters__label" htmlFor="user-filter-group">
                Grupo
              </label>
              <select
                id="user-filter-group"
                value={filters.groupId ?? ""}
                onChange={(event) =>
                  applyFilters({
                    groupId: event.target.value || undefined,
                  })
                }
              >
                <option value="">Todos os grupos</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>
          </>
        }
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
        getItemClassName={(user) =>
          onlineByUserId.has(user.id) ? "admin-entity-card--online" : undefined
        }
        renderIcon={(user) => (
          <span className="admin-user-presence-icon">
            {getInitials(user)}
            {onlineByUserId.has(user.id) ? (
              <span
                className="admin-user-presence-icon__dot"
                title="Online no portal"
                aria-hidden="true"
              />
            ) : null}
          </span>
        )}
        renderTitle={(user) => user.name || "Usuário sem nome"}
        renderSubtitle={(user) => user.email}
        renderBadges={(user) => [
          {
            label: getUserStatusLabel(user),
            tone: user.active === false ? "danger" : "success",
          },
          ...(onlineByUserId.has(user.id)
            ? [
                {
                  label: (
                    <>
                      <Circle size={8} fill="currentColor" aria-hidden="true" />
                      Online
                    </>
                  ),
                  tone: "success" as const,
                },
              ]
            : []),
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
          renderPresenceMeta(user),
          <>
            <UserRound size={13} />
            ID: {user.id}
          </>,
          `Último login: ${formatBrazilDateTime(user.last_login_at)}`,
        ].filter(Boolean)}
        renderActions={(user) => [
          {
            label: "Editar RBAC",
            onClick: () => setEditing(user),
          },
          {
            label: "Anonimizar (LGPD)",
            onClick: () => setAnonymizing(user),
            danger: true,
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

      <ConfirmDialog
        open={!!anonymizing}
        title="Anonimizar dados do usuário"
        message={`Deseja anonimizar todos os dados pessoais de "${anonymizing?.name ?? anonymizing?.email}"? Esta ação é irreversível e atende ao direito ao esquecimento (LGPD Art. 18).`}
        confirmText="Anonimizar"
        danger
        onCancel={() => setAnonymizing(null)}
        onConfirm={handleAnonymize}
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