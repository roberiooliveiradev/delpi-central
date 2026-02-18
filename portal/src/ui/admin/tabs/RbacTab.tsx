// src/ui/admin/tabs/RbacTab.tsx

import { useEffect, useState, useContext } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";

export const RbacTab = () => {
  const { token } = useContext(AuthContext);
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);

  useEffect(() => {
    if (!token) return;

    const api = new AdminApi(new ApiClient("", () => token));

    const load = async () => {
      const [u, r] = await Promise.all([
        api.listUsers(),
        api.listRoles(),
      ]);
      setUsers(u);
      setRoles(r);
    };

    load();
  }, [token]);

  return (
    <div>
      <h2>Usuários</h2>
      {users.map((u) => (
        <div key={u.id} className="card">
          <strong>{u.name}</strong> — {u.email}
          <div>
            Resposabilidade: {u.roles.map((r: any) => r.name).join(", ")}
          </div>
        </div>
      ))}

      <h2 style={{ marginTop: 30 }}>Responsabilidades</h2>
      {roles.map((r) => (
        <div key={r.id} className="card">
          <strong>{r.name}</strong>
          <div>
            Permissões: {r.permissions.map((p: any) => p.code).join(", ")}
          </div>
        </div>
      ))}
    </div>
  );
};
