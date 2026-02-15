// src/ui/HomePage.tsx

import { useContext } from "react";
import { AuthContext } from "../state/AuthContext";

export const HomePage = () => {
  const { user, apps } = useContext(AuthContext);

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Bom dia";
    if (hour < 18) return "Boa tarde";
    return "Boa noite";
  };

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>
        {greeting()}, {user?.name}
      </h1>

      <p style={{ marginBottom: 30, color: "var(--text-muted)" }}>
        Bem-vindo à DELPI Central.
      </p>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>{apps.length}</h3>
          <span>Aplicações Disponíveis</span>
        </div>

        <div className="stat-card">
          <h3>{user?.roles.length || 0}</h3>
          <span>Perfis Ativos</span>
        </div>

        <div className="stat-card">
          <h3>{user?.permissions.length || 0}</h3>
          <span>Permissões</span>
        </div>
      </div>

      {/* Activity */}
      <div className="dashboard-section">
        <h3>Atividade Recente</h3>

        <div className="activity-card">
          <p>✔ Login realizado com sucesso</p>
          <p>✔ Permissões carregadas</p>
          <p>✔ Sistema operacional</p>
        </div>
      </div>
    </div>
  );
};
