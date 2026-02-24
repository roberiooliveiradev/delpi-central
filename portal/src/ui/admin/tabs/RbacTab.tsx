// src/ui/admin/tabs/RbacTab.tsx
import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminUser } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { ActionButtons } from "../../../components/ActionButtons";
import { UserRbacModal } from "../modals/UserRbacModal";

export const RbacTab = () => {
  const { token } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ sort?: string; direction?: "asc" | "desc" }>({
    sort: "email",
    direction: "asc",
  });

  const [selected, setSelected] = useState<string[]>([]);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [confirmBulk, setConfirmBulk] = useState(false);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const usersResource = usePaginatedResource<AdminUser>(
    ({ page, pageSize }) =>
      api!.listUsers({
        page,
        pageSize,
        q: search,
        sort: sort.sort,
        direction: sort.direction,
      }),
    10,
    [search, sort.sort, sort.direction]
  );

  if (!api) return null;

  return (
    <div>
      <DataTable
        columns={[
          { key: "name", header: "Nome", sortable: true },
          { key: "email", header: "Email", sortable: true },
          {
            key: "roles",
            header: "Roles",
            render: (row) =>
              row.roles.map((r) => r.name).join(", ") || "Nenhuma",
          },
          {
            key: "groups",
            header: "Groups",
            render: (row) =>
              row.groups.map((g) => g.name).join(", ") || "Nenhum",
          },
          {
            key: "is_superadmin",
            header: "Superadmin",
            sortable: true,
            render: (row) => (row.is_superadmin ? "Sim" : "Não"),
          },
        ]}
        data={usersResource.data}
        loading={usersResource.loading}
        searchValue={search}
        onSearchChange={setSearch}
        sort={sort}
        onSortChange={setSort}
        selectable
        getRowId={(row) => row.id}
        selectedRows={selected}
        onSelectionChange={setSelected}
        actions={(row) => (
        <ActionButtons
          onEdit={() => setEditing(row)}
        />
        )}
        toolbar={
          selected.length > 0 && (
            <button
              className="btn-danger"
              onClick={() => setConfirmBulk(true)}
            >
              Excluir selecionados ({selected.length})
            </button>
          )
        }
        pagination={
          usersResource.pagination && {
            page: usersResource.page,
            totalPages: usersResource.pagination.total_pages,
            total: usersResource.pagination.total,
            pageSize: 10,
          }
        }
        onPageChange={usersResource.setPage}
      />

      <ConfirmDialog
        open={confirmBulk}
        title="Excluir usuários"
        message={`Deseja excluir ${selected.length} usuários?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmBulk(false)}
        onConfirm={async () => {
          await api.bulkDeleteUsers(selected);
          setSelected([]);
          setConfirmBulk(false);
          usersResource.refetch();
        }}
      />

      <UserRbacModal
        open={!!editing}
        user={editing}
        api={api}
        onClose={() => setEditing(null)}
        onSaved={() => usersResource.refetch()}
      />
    </div>
  );
};