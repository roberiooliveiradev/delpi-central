// src/ui/admin/modals/RoleEditModal.tsx

import { useMemo, useState, useEffect } from "react";
import type {
  AdminPermission,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import { DataTable } from "../../../components/DataTable";
import "./RoleEditModal.css";

type RoleModalTab = "details" | "users" | "permissions";

type Props = {
  open: boolean;
  role: AdminRole | null;

  users: AdminUser[];
  selectedUserIds: string[];

  allPerms: AdminPermission[];
  selectedPermIds: string[];

  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeRole: (patch: Partial<AdminRole>) => void;
  onToggleUser: (userId: string) => void;
  onTogglePerm: (permId: string) => void;
};

export const RoleEditModal = ({
  open,
  role,
  users,
  selectedUserIds,
  allPerms,
  selectedPermIds,
  saving = false,
  onClose,
  onSave,
  onChangeRole,
  onToggleUser,
  onTogglePerm,
}: Props) => {
  const [activeTab, setActiveTab] = useState<RoleModalTab>("details");

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

  const [permSearch, setPermSearch] = useState("");
  const [permSort, setPermSort] = useState<{
    sort?: string;
    direction?: "asc" | "desc";
  }>({
    sort: "code",
    direction: "asc",
  });
  const [permPage, setPermPage] = useState(1);
  const [permPageSize, setPermPageSize] = useState(10);

  useEffect(() => {
    if (open) {
      setActiveTab("details");
      setUserSearch("");
      setPermSearch("");
      setUserPage(1);
      setPermPage(1);
    }
  }, [open, role?.id]);

  useEffect(() => {
    setUserPage(1);
  }, [userSearch]);

  useEffect(() => {
    setPermPage(1);
  }, [permSearch]);

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

  const processedPerms = useMemo(() => {
    const search = permSearch.trim().toLowerCase();

    let base = search
      ? allPerms.filter(
          (permission) =>
            (permission.code || "").toLowerCase().includes(search) ||
            (permission.name || "").toLowerCase().includes(search) ||
            (permission.module || "").toLowerCase().includes(search)
        )
      : [...allPerms];

    base.sort((a, b) => {
      const aSelected = selectedPermIds.includes(a.id);
      const bSelected = selectedPermIds.includes(b.id);

      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;

      const key = permSort.sort as keyof AdminPermission;
      if (!key) return 0;

      const aValue = (a[key] ?? "").toString();
      const bValue = (b[key] ?? "").toString();

      const result = aValue.localeCompare(bValue);

      return permSort.direction === "desc" ? -result : result;
    });

    return base;
  }, [allPerms, permSearch, selectedPermIds, permSort]);

  const permTotalPages = Math.max(
    1,
    Math.ceil(processedPerms.length / permPageSize)
  );

  const paginatedPerms = useMemo(() => {
    const start = (permPage - 1) * permPageSize;
    return processedPerms.slice(start, start + permPageSize);
  }, [processedPerms, permPage, permPageSize]);

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

  const reconcilePermissionSelection = (ids: string[]) => {
    const current = new Set(selectedPermIds);
    const next = new Set(ids);

    ids.forEach((id) => {
      if (!current.has(id)) onTogglePerm(id);
    });

    selectedPermIds.forEach((id) => {
      if (!next.has(id)) onTogglePerm(id);
    });
  };

  if (!open || !role) return null;

  const isEdit = !!role.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Papel — ${role.name}` : "Novo Papel"}
      onClose={onClose}
      size="xl"
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button onClick={onSave} disabled={saving || !role.name?.trim()}>
            Salvar
          </button>
        </>
      }
    >
      <div className="role-edit-body">
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
            Usuários diretos
          </button>

          <button
            type="button"
            className={activeTab === "permissions" ? "active" : ""}
            onClick={() => setActiveTab("permissions")}
          >
            Permissões
          </button>
        </div>

        {activeTab === "details" && (
          <>
            <label>
              Nome
              <input
                value={role.name}
                onChange={(event) =>
                  onChangeRole({ name: event.target.value })
                }
                disabled={saving}
              />
            </label>

            <label>
              Descrição
              <textarea
                value={role.description || ""}
                onChange={(event) =>
                  onChangeRole({ description: event.target.value })
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
                <h4>Usuários diretos do Papel</h4>
                <div className="dt-muted">
                  {selectedUserIds.length} usuários selecionados
                </div>
              </>
            }
          />
        )}

        {activeTab === "permissions" && (
          <DataTable<AdminPermission>
            columns={[
              {
                key: "code",
                header: "Código",
                sortable: true,
                render: (permission) => (
                  <span className="role-edit-perm-code">
                    {permission.code}
                  </span>
                ),
              },
              {
                key: "name",
                header: "Nome",
                sortable: true,
                render: (permission) => (
                  <span className="role-edit-perm-name">
                    {permission.name ?? "-"}
                  </span>
                ),
              },
              {
                key: "module",
                header: "Módulo",
                sortable: true,
                render: (permission) => permission.module ?? "-",
              },
            ]}
            data={paginatedPerms}
            loading={saving}
            searchValue={permSearch}
            onSearchChange={setPermSearch}
            sort={permSort}
            onSortChange={setPermSort}
            selectable
            getRowId={(permission) => permission.id}
            selectedRows={selectedPermIds}
            onSelectionChange={reconcilePermissionSelection}
            pagination={{
              page: permPage,
              totalPages: permTotalPages,
              total: processedPerms.length,
              pageSize: permPageSize,
            }}
            onPageChange={setPermPage}
            onPageSizeChange={(size) => {
              setPermPageSize(size);
              setPermPage(1);
            }}
            pageSizeOptions={[5, 10, 20, 50]}
            emptyText="Nenhuma permissão encontrada"
            toolbar={
              <>
                <h4>Permissões do Papel</h4>
                <div className="dt-muted">
                  {selectedPermIds.length} permissões selecionadas
                </div>
              </>
            }
          />
        )}
      </div>
    </Modal>
  );
};