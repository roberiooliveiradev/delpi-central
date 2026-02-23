// src/ui/admin/AdminPage.tsx

import { useState } from "react";
import { RbacTab } from "./tabs/RbacTab";
import { AppsTab } from "./tabs/AppsTab";
import { RoutesTab } from "./tabs/RoutesTab";
import { RolesTab } from "./tabs/RolesTab";

export const AdminPage = () => {
  const [tab, setTab] = useState<"rbac" | "roles" | "apps" | "routes">("rbac");

  return (
    <div>
      <h1>Administração do Sistema</h1>

      <div className="admin-tabs">
        <button onClick={() => setTab("rbac")}>Users</button>
        <button onClick={() => setTab("roles")}>Roles</button>
        <button onClick={() => setTab("apps")}>Apps</button>
        <button onClick={() => setTab("routes")}>Routes</button>
      </div>

      <div className="admin-content">
        {tab === "rbac" && <RbacTab />}
        {tab === "roles" && <RolesTab />}
        {tab === "apps" && <AppsTab />}
        {tab === "routes" && <RoutesTab />}
      </div>
    </div>
  );
};