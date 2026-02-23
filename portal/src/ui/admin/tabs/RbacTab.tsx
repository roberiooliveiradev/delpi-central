// src/ui/admin/tabs/RbacTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminUser } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ActionButtons } from "../../../components/ActionButtons";
import { ConfirmDialog } from "../../../components/ConfirmDialog";

export const RbacTab = () => {
  const { token } = useContext(AuthContext);

  const [userSearch, setUserSearch] = useState("");
  const [sort, setSort] = useState<{ sort?: string; direction?: "asc" | "desc" }>({
    sort: "email",
    direction: "asc",
  });

  const [selected, setSelected] = useState<string[]>([]);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);

  const [toDelete, setToDelete] = useState<AdminUser | null>(null);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const usersResource = usePaginatedResource<AdminUser>(
    ({ page, pageSize }) =>
      api!.listUsers({
        page,
        pageSize,
        q: userSearch,
        sort: sort.sort,
        direction: sort.direction,
      }),
    10,
    [userSearch, sort.sort, sort.direction]
  );

  if (!api) return null;

  const doDeleteOne = async () => {
    if (!toDelete) return;
    setConfirmLoading(true);
    try {
      await api.deleteUser(toDelete.id);
      setToDelete(null);
      setConfirmOpen(false);
      setSelected((s) => s.filter((id) => id !== toDelete.id));
      usersResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  const doBulkDelete = async () => {
    if (selected.length === 0) return;
    setConfirmLoading(true);
    try {
      await api.bulkDeleteUsers(selected);
      setSelected([]);
      setConfirmOpen(false);
      usersResource.setPage(1);
    } finally {
      setConfirmLoading(false);
    }
  };

  return (
    <div>
      <h2>Usuários ({usersResource.pagination?.total ?? 0})</h2>

      <DataTable
        columns={[
          { key: "name", header: "Nome", sortable: true },
          { key: "email", header: "Email", sortable: true },
          {
            key: "roles",
            header: "Roles",
            render: (row) => row.roles.map((r) => r.name).join(", ") || "Nenhuma",
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
        searchValue={userSearch}
        onSearchChange={setUserSearch}
        sort={sort}
        onSortChange={setSort}
        selectable
        getRowId={(row) => row.id}
        selectedRows={selected}
        onSelectionChange={setSelected}
        toolbar={
          selected.length > 0 ? (
            <button
              className="btn-danger"
              onClick={() => {
                setToDelete(null);
                setConfirmOpen(true);
              }}
              disabled={usersResource.loading}
            >
              Excluir selecionados ({selected.length})
            </button>
          ) : (
            <span className="dt-muted">Selecione usuários para excluir em massa</span>
          )
        }
        actions={(row) => (
          <ActionButtons
            onEdit={() => console.log("editar user", row.id)}
            onDelete={() => {
              setToDelete(row);
              setConfirmOpen(true);
            }}
          />
        )}
        pagination={
          usersResource.pagination
            ? {
                page: usersResource.page,
                totalPages: usersResource.pagination.total_pages,
                total: usersResource.pagination.total,
                pageSize: 10,
              }
            : undefined
        }
        onPageChange={usersResource.setPage}
      />

      <ConfirmDialog
        open={confirmOpen}
        title={toDelete ? "Excluir usuário" : "Excluir usuários"}
        message={
          toDelete
            ? `Deseja excluir "${toDelete.email}"?`
            : `Deseja excluir ${selected.length} usuários selecionados?`
        }
        confirmText="Excluir"
        danger
        loading={confirmLoading}
        onCancel={() => {
          setConfirmOpen(false);
          setToDelete(null);
        }}
        onConfirm={toDelete ? doDeleteOne : doBulkDelete}
      />
    </div>
  );
};