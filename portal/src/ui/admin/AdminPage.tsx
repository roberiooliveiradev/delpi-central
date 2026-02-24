// src/ui/admin/AdminPage.tsx
import { useMemo, useState } from "react";
import { RbacTab } from "./tabs/RbacTab";
import { RolesTab } from "./tabs/RolesTab";
import { GroupsTab } from "./tabs/GroupsTab";
import { PermissionsTab } from "./tabs/PermissionsTab";
import { AppsTab } from "./tabs/AppsTab";
import {
  Users,
  LayoutGrid,
  Shield,
  UsersRound,
  KeyRound,
} from "lucide-react";

type AdminTab = "apps" | "users" | "roles" | "groups" | "permissions";

export const AdminPage = () => {
  const [tab, setTab] = useState<AdminTab>("users");

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

  const activeLabel = items.find((i) => i.key === tab)?.label ?? "Admin";

  return (
    <div className="admin-page">
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
      </nav>

      <div className="admin-content">
        {tab === "users" && <RbacTab />}
        {tab === "apps" && <AppsTab />}
        {tab === "roles" && <RolesTab />}
        {tab === "groups" && <GroupsTab />}
        {tab === "permissions" && <PermissionsTab />}
      </div>
    </div>
  );
};