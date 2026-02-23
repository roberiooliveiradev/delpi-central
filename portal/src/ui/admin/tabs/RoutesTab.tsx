// src/ui/admin/tabs/RoutesTab.tsx

import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminAppRoute } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { PaginationControls } from "../../../components/PaginationControls";

export const RoutesTab = () => {
  const { token } = useContext(AuthContext);
  const [appId, setAppId] = useState("");

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const routesResource = usePaginatedResource<AdminAppRoute>(
    ({ page, pageSize }) => {
      if (!api || !appId) {
        return Promise.resolve({
          data: [],
          pagination: {
            page: 1,
            page_size: 10,
            total: 0,
            total_pages: 1,
          },
        });
      }

      return api.listRoutes(appId, { page, pageSize });
    },
    10,
    [appId] // dependência importante
  );

  if (!api) return null;

  return (
    <div>
      <h2>Rotas</h2>

      <input
        placeholder="App ID (ex: crm)"
        value={appId}
        onChange={(e) => setAppId(e.target.value)}
        style={{ marginBottom: 15 }}
      />

      {!appId && <p>Digite um App ID para carregar as rotas.</p>}

      {routesResource.loading && <p>Carregando...</p>}

      <div className="table">
        {routesResource.data.map((r) => (
          <div key={r.id} className="card">
            <strong>{r.path}</strong>
            <div>Permissão: {r.permission_code || "Pública"}</div>
            <div>Status: {r.active ? "Ativa" : "Inativa"}</div>
          </div>
        ))}
      </div>

      {appId && routesResource.pagination && (
        <PaginationControls
          page={routesResource.page}
          totalPages={routesResource.pagination.total_pages}
          onNext={routesResource.next}
          onPrev={routesResource.prev}
        />
      )}
    </div>
  );
};