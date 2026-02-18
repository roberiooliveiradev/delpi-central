// src/ui/admin/tabs/AppsTab.tsx

import { useEffect, useState, useContext } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";

export const AppsTab = () => {
  const { token } = useContext(AuthContext);
  const [apps, setApps] = useState<any[]>([]);

  useEffect(() => {
    if (!token) return;

    const api = new AdminApi(new ApiClient("", () => token));

    api.listApps().then(setApps);
  }, [token]);

  return (
    <div>
      <h2>Aplicações</h2>
      {apps.map((app) => (
        <div key={app.id} className="card">
          <strong>{app.name}</strong> ({app.version})
          <div>Base: {app.base_path}</div>
          <div>Status: {app.active ? "Ativo" : "Inativo"}</div>
        </div>
      ))}
    </div>
  );
};
