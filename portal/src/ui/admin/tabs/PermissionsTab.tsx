// src/ui/admin/tabs/PermissionsTab.tsx
import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminPermission } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";

export const PermissionsTab = () => {
  const { token } = useContext(AuthContext);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ sort?: string; direction?: "asc" | "desc" }>({
    sort: "code",
    direction: "asc",
  });

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const permsResource = usePaginatedResource<AdminPermission>(
    ({ page, pageSize }) =>
      api!.listPermissions({ page, pageSize, q: search, sort: sort.sort, direction: sort.direction }),
    10,
    [search, sort.sort, sort.direction]
  );

  if (!api) return null;

  return (
    <div>
      <DataTable
        columns={[
          { key: "module", header: "App", sortable: true, render: (row) => row.module?.toUpperCase() }, 
          { key: "code", header: "Code", sortable: true },
          { key: "name", header: "Nome", sortable: true },
          { key: "description", header: "Descrição" },
        ]}
        data={permsResource.data}
        loading={permsResource.loading}
        searchValue={search}
        onSearchChange={setSearch}
        sort={sort}
        onSortChange={setSort}
        pagination={
          permsResource.pagination
            ? {
                page: permsResource.page,
                totalPages: permsResource.pagination.total_pages,
                total: permsResource.pagination.total,
                pageSize: 10,
              }
            : undefined
        }
        onPageChange={permsResource.setPage}
      />

      <div className="dt-muted" style={{ marginTop: 10 }}>
        Dica: permissões são criadas/atualizadas via manifesto (plugins). Use “Roles” para conceder permissões.
      </div>
    </div>
  );
};