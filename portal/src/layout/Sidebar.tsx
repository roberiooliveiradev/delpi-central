// src/layout/Sidebar.tsx

import { useContext, useMemo, useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { LayoutDashboard, Users, Package } from "lucide-react";

type IconType = React.ComponentType<{ size?: number }>;

// Mapeamento inteligente de ícones
const iconMap: Record<string, IconType> = {
  dashboard: LayoutDashboard,
  leads: Users,
  default: Package,
};

export const Sidebar = () => {
  const { routes } = useContext(AuthContext);

  // Persistência do estado colapsado
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("sidebar-collapsed") === "true";
  });

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  // Agrupar rotas por app
  const grouped = useMemo(() => {
    const map: Record<string, typeof routes> = {};

    routes.forEach((route) => {
      if (!map[route.app]) {
        map[route.app] = [];
      }
      map[route.app].push(route);
    });

    return map;
  }, [routes]);

  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: collapsed ? "center" : "space-between",
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        {!collapsed && <h2 style={{ fontWeight: 600 }}>DELPI</h2>}

        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: 18,
            color: "var(--text-muted)",
          }}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>

      {/* Apps */}
      {Object.entries(grouped).map(([app, appRoutes]) => (
        <div key={app} style={{ marginTop: 20 }}>
          {!collapsed && (
            <div
              style={{
                fontSize: 11,
                letterSpacing: 1,
                textTransform: "uppercase",
                color: "var(--text-muted)",
                marginBottom: 8,
              }}
            >
              {app}
            </div>
          )}

          {appRoutes.map((route) => {
            const rawLabel =
              route.path.split("/").filter(Boolean).pop() ?? "";

            const label = rawLabel
              .replace(/-/g, " ")
              .replace(/\b\w/g, (c) => c.toUpperCase());

            const Icon =
              iconMap[rawLabel.toLowerCase()] || iconMap.default;

            return (
              <NavLink
                key={route.path}
                to={route.path}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? "active" : ""}`
                }
              >
                <Icon size={18} />

                {!collapsed && <span>{label}</span>}
              </NavLink>
            );
          })}
        </div>
      ))}
    </div>
  );
};
