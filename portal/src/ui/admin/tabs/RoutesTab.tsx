// src/ui/admin/tabs/RoutesTab.tsx

import { useEffect, useState, useContext } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";

export const RoutesTab = () => {
  const { token } = useContext(AuthContext);
  const [appId, setAppId] = useState("");
  const [routes, setRoutes] = useState<any[]>([]);

  useEffect(() => {
    if (!token || !appId) return;

    const api = new AdminApi(new ApiClient("", () => token));
    api.listRoutes(appId).then(setRoutes);
  }, [token, appId]);

  return (
    <div>
      <h2>Rotas</h2>
      <input
        placeholder="App ID (ex: crm)"
        value={appId}
        onChange={(e) => setAppId(e.target.value)}
      />

      {routes.map((r) => (
        <div key={r.id} className="card">
          <strong>{r.path}</strong>
          <div>Permissões: {r.permission_code || "Pública"}</div>
          <div>Status: {r.active ? "Ativa" : "Inativa"}</div>
        </div>
      ))}
    </div>
  );
};
