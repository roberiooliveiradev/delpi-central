// src/ui/admin/tabs/RbacTab.tsx


import { useContext, useMemo } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminUser, AdminRole } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { PaginationControls } from "../../../components/PaginationControls";

export const RbacTab = () => {
  const { token } = useContext(AuthContext);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const usersResource = usePaginatedResource<AdminUser>(
    ({ page, pageSize }) =>
      api!.listUsers({ page, pageSize }),
    10
  );

  const rolesResource = usePaginatedResource<AdminRole>(
    ({ page, pageSize }) =>
      api!.listRoles({ page, pageSize }),
    10
  );

  if (!api) return null;

  return (
    <div>
      {/* ================= USERS ================= */}
      <h2>Usuários ({usersResource.pagination?.total ?? 0})</h2>

      {usersResource.loading && <p>Carregando...</p>}

      <div className="table">
        {usersResource.data.map((u) => (
          <div key={u.id} className="card">
            <strong>{u.name}</strong> — {u.email}
            <div>
              Responsabilidades:{" "}
              {u.roles.map((r) => r.name).join(", ") || "Nenhuma"}
            </div>
          </div>
        ))}
      </div>

      {usersResource.pagination && (
        <PaginationControls
          page={usersResource.page}
          totalPages={usersResource.pagination.total_pages}
          onNext={usersResource.next}
          onPrev={usersResource.prev}
        />
      )}

      {/* ================= ROLES ================= */}
      <h2 style={{ marginTop: 40 }}>
        Responsabilidades ({rolesResource.pagination?.total ?? 0})
      </h2>

      {rolesResource.loading && <p>Carregando...</p>}

      <div className="table">
        {rolesResource.data.map((r) => (
          <div key={r.id} className="card">
            <strong>{r.name}</strong>
            <div>
              Permissões:{" "}
              {r.permissions.map((p) => p.code).join(", ") || "Nenhuma"}
            </div>
          </div>
        ))}
      </div>

      {rolesResource.pagination && (
        <PaginationControls
          page={rolesResource.page}
          totalPages={rolesResource.pagination.total_pages}
          onNext={rolesResource.next}
          onPrev={rolesResource.prev}
        />
      )}
    </div>
  );
};