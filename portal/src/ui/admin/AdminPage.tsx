// src/ui/admin/AdminPage.tsx

import { useMemo, useState } from "react";
import {
  Users,
  LayoutGrid,
  Shield,
  UsersRound,
  KeyRound,
  ChevronDown,
} from "lucide-react";

import { RbacTab } from "./tabs/RbacTab";
import { RolesTab } from "./tabs/RolesTab";
import { GroupsTab } from "./tabs/GroupsTab";
import { PermissionsTab } from "./tabs/PermissionsTab";
import { AppsTab } from "./tabs/AppsTab";

type AdminTab = "apps" | "users" | "roles" | "groups" | "permissions";

export const AdminPage = () => {
  const [tab, setTab] = useState<AdminTab>("users");
  const [mobileOpen, setMobileOpen] = useState(false);

  const items = useMemo(
    () => [
      { key: "users" as const, label: "Usuários", icon: Users },
      { key: "apps" as const, label: "Aplicações", icon: LayoutGrid },
      { key: "roles" as const, label: "Papéis", icon: Shield },
      { key: "groups" as const, label: "Grupos", icon: UsersRound },
      { key: "permissions" as const, label: "Permissões", icon: KeyRound },
    ],
    []
  );

  const activeItem = items.find((i) => i.key === tab)!;
  const ActiveIcon = activeItem.icon;

  return (
    <div className="admin-page">
      {/* DESKTOP / TABLET NAV */}
      <nav className="admin-navbar" aria-label="Navegação de administração">
        <div className="admin-navbar-inner">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = item.key === tab;

            return (
              <button
                key={item.key}
                type="button"
                className={`admin-nav-item ${isActive ? "active" : ""}`}
                onClick={() => setTab(item.key)}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* MOBILE DROPDOWN */}
        <div className="admin-mobile-select">
          <button
            type="button"
            className="admin-mobile-trigger"
            onClick={() => setMobileOpen((p) => !p)}
          >
            <ActiveIcon size={18} />
            <span>{activeItem.label}</span>
            <ChevronDown size={16} />
          </button>

          {mobileOpen && (
            <div className="admin-mobile-menu">
              {items.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.key}
                    onClick={() => {
                      setTab(item.key);
                      setMobileOpen(false);
                    }}
                  >
                    <Icon size={16} />
                    {item.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </nav>

      <div className="admin-content">
        <div key={tab} className="admin-tab-panel">
          {tab === "users" && <RbacTab />}
          {tab === "apps" && <AppsTab />}
          {tab === "roles" && <RolesTab />}
          {tab === "groups" && <GroupsTab />}
          {tab === "permissions" && <PermissionsTab />}
        </div>
      </div>
    </div>
  );
};