// src/ui/admin/tabs/AppsTab.tsx

import { useContext, useMemo } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminApp } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { PaginationControls } from "../../../components/PaginationControls";

export const AppsTab = () => {
  const { token } = useContext(AuthContext);

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const appsResource = usePaginatedResource<AdminApp>(
    ({ page, pageSize }) =>
      api
        ? api.listApps({ page, pageSize })
        : Promise.resolve({
            data: [],
            pagination: {
              page: 1,
              page_size: 10,
              total: 0,
              total_pages: 1,
            },
          }),
    10
  );

  if (!api) return null;

  if (!appsResource.pagination) {
    return <div>Carregando...</div>;
  }

  return (
    <div>
      <h2>Aplicações ({appsResource.pagination.total})</h2>

      <div className="table">
        {(appsResource.data ?? []).map((app) => (
          <div key={app.id} className="card">
            <strong>{app.name}</strong> ({app.version})
            <div>Base: {app.base_path}</div>
            <div>Status: {app.active ? "Ativo" : "Inativo"}</div>
          </div>
        ))}
      </div>

      <PaginationControls
        page={appsResource.page}
        totalPages={appsResource.pagination.total_pages}
        onNext={appsResource.next}
        onPrev={appsResource.prev}
      />
    </div>
  );
};