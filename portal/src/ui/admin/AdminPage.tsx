// src/ui/admin/AdminPage.tsx
import { useState } from "react";
import { RbacTab } from "./tabs/RbacTab";
import { RolesTab } from "./tabs/RolesTab";
import { GroupsTab } from "./tabs/GroupsTab";
import { PermissionsTab } from "./tabs/PermissionsTab";
import { AppsTab } from "./tabs/AppsTab";

export const AdminPage = () => {
  const [tab, setTab] = useState<
    "users" | "roles" | "groups" | "permissions" | "apps" | "routes"
  >("users");

  return (
    <div>
      <h1>Administração do Sistema</h1>

      <div className="admin-tabs">
        <button onClick={() => setTab("apps")}>Aplicações</button>
        <button onClick={() => setTab("users")}>Usuários</button>
        <button onClick={() => setTab("roles")}>Papéis</button>
        <button onClick={() => setTab("groups")}>Grupos</button>
        <button onClick={() => setTab("permissions")}>Permissões</button>
      </div>

      <div className="admin-content">
        {tab === "apps" && <AppsTab />}
        {tab === "users" && <RbacTab />}
        {tab === "roles" && <RolesTab />}
        {tab === "groups" && <GroupsTab />}
        {tab === "permissions" && <PermissionsTab />}
      </div>
    </div>
  );
};