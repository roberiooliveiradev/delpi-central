// src/ui/HomePage.tsx

import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";

export const HomePage = () => {
  const { user, dashboard, favorites } = useContext(AuthContext);
  const navigate = useNavigate();

  if (!dashboard) return null;

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
        Bem-vindo à Central DELPI.
      </p>

      {/* FAVORITOS */}
      {favorites && favorites.length > 0 && (
        <div className="dashboard-section">
          <h3>Aplicações Favoritas</h3>

          <div className="favorites-grid">
            {favorites.map((app) => (
              <div
                key={app.id}
                className="favorite-card"
                onClick={() => navigate(app.base_path)}
              >
                {app.icon && (
                  <div className="favorite-icon">
                    <i className={`icon-${app.icon}`} />
                  </div>
                )}

                <span>{app.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STATS */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>{dashboard.appsCount}</h3>
          <span>Aplicações Disponíveis</span>
        </div>

        <div className="stat-card">
          <h3>{dashboard.rolesCount}</h3>
          <span>Perfis Ativos</span>
        </div>

        <div className="stat-card">
          <h3>{dashboard.permissionsCount}</h3>
          <span>Permissões</span>
        </div>
      </div>

      {/* ATIVIDADE */}
      <div className="dashboard-section">
        <h3>Atividade Recente</h3>

        <div className="activity-card">
          {(dashboard.recentActivity ?? []).length === 0 && (
            <p style={{ color: "var(--text-muted)" }}>
              Nenhuma atividade recente.
            </p>
          )}

          {(dashboard.recentActivity ?? []).map((item, index) => (
            <p key={index}>✔ {item}</p>
          ))}
        </div>
      </div>
    </div>
  );
};
