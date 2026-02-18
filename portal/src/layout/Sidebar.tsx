// src/layout/Sidebar.tsx

import { useContext, useMemo, useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { LayoutDashboard, Users, Package, ChevronDown } from "lucide-react";


type IconType = React.ComponentType<{ size?: number }>;

// Mapeamento inteligente de ícones
const iconMap: Record<string, IconType> = {
  dashboard: LayoutDashboard,
  leads: Users,
  default: Package,
};

export const Sidebar = () => {
  const { routes } = useContext(AuthContext);
  const location = useLocation();

  // Sidebar global collapse
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem("sidebar-collapsed") === "true";
  });

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  // Controle de collapse por app
  const [openApps, setOpenApps] = useState<Record<string, boolean>>({});

  const toggleApp = (app: string) => {
    setOpenApps((prev) => ({
      ...prev,
      [app]: !prev[app],
    }));
  };

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
        {!collapsed && 
          <div style={{width:"100%", display:"flex", flexDirection:"column", alignItems:"center"}}>

          <div
            style={{
              width: "130px",
              height: "130px",
              borderRadius: "50%",
              overflow: "hidden",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            >
            <img
              src="/logoTransformaMaisDelpi.svg"
              alt="Transforma mais DELPI"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
              }}
              />
              </div>
          </div>

        }

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
      {Object.entries(grouped).map(([app, appRoutes]) => {
        const isOpen = openApps[app] ?? true;

        return (
          <div key={app} style={{ marginTop: 20 }}>
            {/* Título do App */}
            {!collapsed && (
              <div
                onClick={() => toggleApp(app)}
                style={{
                  fontSize: 11,
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  color: "var(--text-muted)",
                  marginBottom: 8,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  cursor: "pointer",
                }}
              >
                {app}
                <ChevronDown
                  size={14}
                  style={{
                    transform: isOpen ? "rotate(0deg)" : "rotate(-90deg)",
                    transition: "0.2s",
                  }}
                />
              </div>
            )}

            {/* Rotas */}
            {isOpen &&
              appRoutes.map((route) => {
                const rawLabel =
                  route.path.split("/").filter(Boolean).pop() ?? "";

                const label = rawLabel
                  .replace(/-/g, " ")
                  .replace(/\b\w/g, (c) => c.toUpperCase());

                const Icon =
                  iconMap[rawLabel.toLowerCase()] || iconMap.default;

                const isActive = location.pathname === route.path;

                return (
                  <NavLink
                    key={route.path}
                    to={route.path}
                    className={`sidebar-link ${
                      isActive ? "active" : ""
                    }`}
                    style={{
                      justifyContent: collapsed ? "center" : "flex-start",
                    }}
                  >
                    <Icon size={18} />

                    {!collapsed && <span>{label}</span>}
                  </NavLink>
                );
              })}
          </div>
        );
      })}
    </div>
  );
};
