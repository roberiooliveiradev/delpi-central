// src/ui/admin/modals/GroupEditModal.tsx

import { useMemo, useState, useEffect } from "react";
import type { AdminGroup, AdminRole, AdminUser } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import { DataTable } from "../../../components/DataTable";
import "./GroupEditModal.css";

type GroupModalTab = "details" | "users" | "roles";

type Props = {
  open: boolean;
  group: AdminGroup | null;

  users: AdminUser[];
  selectedUserIds: string[];

  roles: AdminRole[];
  selectedRoleIds: string[];

  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeGroup: (patch: Partial<AdminGroup>) => void;
  onToggleUser: (userId: string) => void;
  onToggleRole: (roleId: string) => void;
};

export const GroupEditModal = ({
  open,
  group,
  users,
  selectedUserIds,
  roles,
  selectedRoleIds,
  saving = false,
  onClose,
  onSave,
  onChangeGroup,
  onToggleUser,
  onToggleRole,
}: Props) => {
  const [activeTab, setActiveTab] = useState<GroupModalTab>("details");

  const [userSearch, setUserSearch] = useState("");
  const [userSort, setUserSort] = useState<{
    sort?: string;
    direction?: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
  });
  const [userPage, setUserPage] = useState(1);
  const [userPageSize, setUserPageSize] = useState(10);

  const [roleSearch, setRoleSearch] = useState("");
  const [roleSort, setRoleSort] = useState<{
    sort?: string;
    direction?: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
  });
  const [rolePage, setRolePage] = useState(1);
  const [rolePageSize, setRolePageSize] = useState(10);

  useEffect(() => {
    if (open) {
      setActiveTab("details");
      setUserSearch("");
      setRoleSearch("");
      setUserPage(1);
      setRolePage(1);
    }
  }, [open, group?.id]);

  useEffect(() => {
    setUserPage(1);
  }, [userSearch]);

  useEffect(() => {
    setRolePage(1);
  }, [roleSearch]);

  const processedUsers = useMemo(() => {
    const search = userSearch.trim().toLowerCase();

    let base = search
      ? users.filter(
          (user) =>
            (user.name || "").toLowerCase().includes(search) ||
            (user.email || "").toLowerCase().includes(search)
        )
      : [...users];

    base.sort((a, b) => {
      const aSelected = selectedUserIds.includes(a.id);
      const bSelected = selectedUserIds.includes(b.id);

      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;

      const key = userSort.sort as keyof AdminUser;
      if (!key) return 0;

      const aValue = (a[key] ?? "").toString();
      const bValue = (b[key] ?? "").toString();

      const result = aValue.localeCompare(bValue);

      return userSort.direction === "desc" ? -result : result;
    });

    return base;
  }, [users, userSearch, selectedUserIds, userSort]);

  const userTotalPages = Math.max(
    1,
    Math.ceil(processedUsers.length / userPageSize)
  );

  const paginatedUsers = useMemo(() => {
    const start = (userPage - 1) * userPageSize;
    return processedUsers.slice(start, start + userPageSize);
  }, [processedUsers, userPage, userPageSize]);

  const processedRoles = useMemo(() => {
    const search = roleSearch.trim().toLowerCase();

    let base = search
      ? roles.filter(
          (role) =>
            (role.name || "").toLowerCase().includes(search) ||
            (role.description || "").toLowerCase().includes(search)
        )
      : [...roles];

    base.sort((a, b) => {
      const aSelected = selectedRoleIds.includes(a.id);
      const bSelected = selectedRoleIds.includes(b.id);

      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;

      const key = roleSort.sort as keyof AdminRole;
      if (!key) return 0;

      const aValue = (a[key] ?? "").toString();
      const bValue = (b[key] ?? "").toString();

      const result = aValue.localeCompare(bValue);

      return roleSort.direction === "desc" ? -result : result;
    });

    return base;
  }, [roles, roleSearch, selectedRoleIds, roleSort]);

  const roleTotalPages = Math.max(
    1,
    Math.ceil(processedRoles.length / rolePageSize)
  );

  const paginatedRoles = useMemo(() => {
    const start = (rolePage - 1) * rolePageSize;
    return processedRoles.slice(start, start + rolePageSize);
  }, [processedRoles, rolePage, rolePageSize]);

  const reconcileUserSelection = (ids: string[]) => {
    const current = new Set(selectedUserIds);
    const next = new Set(ids);

    ids.forEach((id) => {
      if (!current.has(id)) onToggleUser(id);
    });

    selectedUserIds.forEach((id) => {
      if (!next.has(id)) onToggleUser(id);
    });
  };

  const reconcileRoleSelection = (ids: string[]) => {
    const current = new Set(selectedRoleIds);
    const next = new Set(ids);

    ids.forEach((id) => {
      if (!current.has(id)) onToggleRole(id);
    });

    selectedRoleIds.forEach((id) => {
      if (!next.has(id)) onToggleRole(id);
    });
  };

  if (!open || !group) return null;

  const isEdit = !!group.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Grupo — ${group.name}` : "Novo Grupo"}
      onClose={onClose}
      size="xl"
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button onClick={onSave} disabled={saving || !group.name?.trim()}>
            Salvar
          </button>
        </>
      }
    >
      <div className="group-edit-body">
        <div className="tabs">
          <button
            type="button"
            className={activeTab === "details" ? "active" : ""}
            onClick={() => setActiveTab("details")}
          >
            Dados
          </button>

          <button
            type="button"
            className={activeTab === "users" ? "active" : ""}
            onClick={() => setActiveTab("users")}
          >
            Usuários
          </button>

          <button
            type="button"
            className={activeTab === "roles" ? "active" : ""}
            onClick={() => setActiveTab("roles")}
          >
            Papéis
          </button>
        </div>

        {activeTab === "details" && (
          <>
            <label>
              Nome
              <input
                value={group.name}
                onChange={(event) =>
                  onChangeGroup({ name: event.target.value })
                }
                disabled={saving}
              />
            </label>

            <label>
              Descrição
              <textarea
                value={group.description || ""}
                onChange={(event) =>
                  onChangeGroup({ description: event.target.value })
                }
                disabled={saving}
              />
            </label>
          </>
        )}

        {activeTab === "users" && (
          <DataTable<AdminUser>
            columns={[
              {
                key: "name",
                header: "Nome",
                sortable: true,
              },
              {
                key: "email",
                header: "Email",
                sortable: true,
              },
              {
                key: "is_superadmin",
                header: "Superadmin",
                sortable: true,
                render: (user) => (user.is_superadmin ? "Sim" : "Não"),
              },
            ]}
            data={paginatedUsers}
            loading={saving}
            searchValue={userSearch}
            onSearchChange={setUserSearch}
            sort={userSort}
            onSortChange={setUserSort}
            selectable
            getRowId={(user) => user.id}
            selectedRows={selectedUserIds}
            onSelectionChange={reconcileUserSelection}
            pagination={{
              page: userPage,
              totalPages: userTotalPages,
              total: processedUsers.length,
              pageSize: userPageSize,
            }}
            onPageChange={setUserPage}
            onPageSizeChange={(size) => {
              setUserPageSize(size);
              setUserPage(1);
            }}
            pageSizeOptions={[5, 10, 20, 50]}
            emptyText="Nenhum usuário encontrado"
            toolbar={
              <>
                <h4>Usuários do Grupo</h4>
                <div className="dt-muted">
                  {selectedUserIds.length} usuários selecionados
                </div>
              </>
            }
          />
        )}

        {activeTab === "roles" && (
          <DataTable<AdminRole>
            columns={[
              {
                key: "name",
                header: "Nome",
                sortable: true,
              },
              {
                key: "description",
                header: "Descrição",
                sortable: true,
                render: (role) => role.description ?? "-",
              },
            ]}
            data={paginatedRoles}
            loading={saving}
            searchValue={roleSearch}
            onSearchChange={setRoleSearch}
            sort={roleSort}
            onSortChange={setRoleSort}
            selectable
            getRowId={(role) => role.id}
            selectedRows={selectedRoleIds}
            onSelectionChange={reconcileRoleSelection}
            pagination={{
              page: rolePage,
              totalPages: roleTotalPages,
              total: processedRoles.length,
              pageSize: rolePageSize,
            }}
            onPageChange={setRolePage}
            onPageSizeChange={(size) => {
              setRolePageSize(size);
              setRolePage(1);
            }}
            pageSizeOptions={[5, 10, 20, 50]}
            emptyText="Nenhum papel encontrado"
            toolbar={
              <>
                <h4>Papéis do Grupo</h4>
                <div className="dt-muted">
                  {selectedRoleIds.length} papéis selecionados
                </div>
              </>
            }
          />
        )}
      </div>
    </Modal>
  );
};