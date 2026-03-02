// src/ui/admin/modals/UserRbacModal.tsx
import { useEffect, useState, useMemo } from "react";
import type {
  AdminGroup,
  AdminRole,
  AdminUser,
} from "../../../data/adminApi";
import { AdminApi } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import "./UserRbacModal.css";
import { DataTable } from "../../../components/DataTable";

type Props = {
  open: boolean;
  onClose: () => void;
  user: AdminUser | null;
  api: AdminApi;
  onSaved: () => void;
};

export const UserRbacModal = ({
  open,
  onClose,
  user,
  api,
  onSaved,
}: Props) => {
  const [loading, setLoading] = useState(false);

  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);

  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([]);
  const [isSuperadmin, setIsSuperadmin] = useState(false);

  const [roleSearch, setRoleSearch] = useState("");
  const [groupSearch, setGroupSearch] = useState("");
  const [rolePage, setRolePage] = useState(1);
  const [groupPage, setGroupPage] = useState(1);

  const [rolePageSize, setRolePageSize] = useState(10);
  const [groupPageSize, setGroupPageSize] = useState(10);

  useEffect(() => {
    setRolePage(1);
  }, [roleSearch]);

  useEffect(() => {
    setGroupPage(1);
  }, [groupSearch]);

  useEffect(() => {
    if (!open || !user) return;

    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const [
          allRolesRes,
          allGroupsRes,
          userRolesRes,
          userGroupsRes,
        ] = await Promise.all([
          api.listRoles({ page: 1, pageSize: 999 }),
          api.listGroups({ page: 1, pageSize: 999 }),
          api.getUserRoles(user.id),
          api.getUserGroups(user.id),
        ]);

        if (cancelled) return;

        setRoles(allRolesRes.data ?? []);
        setGroups(allGroupsRes.data ?? []);
        setSelectedRoleIds((userRolesRes.data ?? []).map((r) => r.id));
        setSelectedGroupIds((userGroupsRes.data ?? []).map((g) => g.id));
        setIsSuperadmin(!!user.is_superadmin);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [open, user, api]);

  const filteredRoles = useMemo(() => {
    const base = roleSearch
      ? roles.filter((r) =>
          r.name.toLowerCase().includes(roleSearch.toLowerCase())
        )
      : roles;

    return [...base].sort((a, b) => {
      const aSelected = selectedRoleIds.includes(a.id);
      const bSelected = selectedRoleIds.includes(b.id);

      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;

      return a.name.localeCompare(b.name);
    });
  }, [roles, roleSearch, selectedRoleIds]);

  const filteredGroups = useMemo(() => {
    const base = groupSearch
      ? groups.filter((g) =>
          g.name.toLowerCase().includes(groupSearch.toLowerCase())
        )
      : groups;

    return [...base].sort((a, b) => {
      const aSelected = selectedGroupIds.includes(a.id);
      const bSelected = selectedGroupIds.includes(b.id);

      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;

      return a.name.localeCompare(b.name);
    });
  }, [groups, groupSearch, selectedGroupIds]);

  // 🔹 Paginação ROLES
  const paginatedRoles = useMemo(() => {
    const start = (rolePage - 1) * rolePageSize;
    return filteredRoles.slice(start, start + rolePageSize);
  }, [filteredRoles, rolePage, rolePageSize]);

  const roleTotalPages = Math.max(
    1,
    Math.ceil(filteredRoles.length / rolePageSize)
  );

  // 🔹 Paginação GROUPS
  const paginatedGroups = useMemo(() => {
    const start = (groupPage - 1) * groupPageSize;
    return filteredGroups.slice(start, start + groupPageSize);
  }, [filteredGroups, groupPage, groupPageSize]);

  const groupTotalPages = Math.max(
    1,
    Math.ceil(filteredGroups.length / groupPageSize)
  );

  if (!open || !user) return null;

  const save = async () => {
    setLoading(true);
    try {
      await api.updateUser(user.id, {
        roleIds: selectedRoleIds,
        groupIds: selectedGroupIds,
        is_superadmin: isSuperadmin,
      });
      onSaved();
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      title={`Editar RBAC — ${user.email}`}
      onClose={onClose}
      size="xl"
      footer={
        <>
          <button onClick={onClose} disabled={loading}>
            Cancelar
          </button>
          <button onClick={save} disabled={loading}>
            Salvar
          </button>
        </>
      }
    >
      <div className="superadmin-row">
        <input
          type="checkbox"
          checked={isSuperadmin}
          onChange={(e) => setIsSuperadmin(e.target.checked)}
          disabled={loading}
        />
        <span>Superadmin</span>
      </div>

      <div className="rbac-grid">
        {/* ROLES */}
        <div className="rbac-column">
          <DataTable<AdminRole>
            columns={[
              { key: "name", header: "Nome", sortable: true },
              {
                key: "description",
                header: "Descrição",
                render: (r) => r.description ?? "-",
              },
            ]}
            data={paginatedRoles}
            loading={loading}
            searchValue={roleSearch}
            onSearchChange={setRoleSearch}
            selectable
            getRowId={(r) => r.id}
            selectedRows={selectedRoleIds}
            onSelectionChange={setSelectedRoleIds}
            pagination={{
              page: rolePage,
              totalPages: roleTotalPages,
              total: filteredRoles.length,
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
                <h4>Papéis do usuário</h4>
                <div className="dt-muted">
                  {filteredRoles.length} de {roles.length} papéis
                </div>
              </>
            }
          />
        </div>

        {/* GROUPS */}
        <div className="rbac-column">
          <DataTable<AdminGroup>
            columns={[
              { key: "name", header: "Nome", sortable: true },
              {
                key: "description",
                header: "Descrição",
                render: (g) => g.description ?? "-",
              },
            ]}
            data={paginatedGroups}
            loading={loading}
            searchValue={groupSearch}
            onSearchChange={setGroupSearch}
            selectable
            getRowId={(g) => g.id}
            selectedRows={selectedGroupIds}
            onSelectionChange={setSelectedGroupIds}
            pagination={{
              page: groupPage,
              totalPages: groupTotalPages,
              total: filteredGroups.length,
              pageSize: groupPageSize,
            }}
            onPageChange={setGroupPage}
            onPageSizeChange={(size) => {
              setGroupPageSize(size);
              setGroupPage(1);
            }}
            pageSizeOptions={[5, 10, 20, 50]}
            emptyText="Nenhum grupo encontrado"
            toolbar={
              <>
                <h4>Grupos do usuário</h4>
                <div className="dt-muted">
                  {filteredGroups.length} de {groups.length} grupos
                </div>
              </>
            }
          />
        </div>
      </div>
    </Modal>
  );
};