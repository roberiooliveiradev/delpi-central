// src/ui/admin/AdminPage.tsx

import { useState } from "react";
import { RbacTab } from "./tabs/RbacTab";
import { AppsTab } from "./tabs/AppsTab";
import { RoutesTab } from "./tabs/RoutesTab";

export const AdminPage = () => {
  const [tab, setTab] = useState<"rbac" | "apps" | "routes">("rbac");

  return (
    <div>
      <h1>Administração do Sistema</h1>

      <div className="admin-tabs">
        <button onClick={() => setTab("rbac")}>RBAC</button>
        <button onClick={() => setTab("apps")}>Apps</button>
        <button onClick={() => setTab("routes")}>Routes</button>
      </div>

      <div className="admin-content">
        {tab === "rbac" && <RbacTab />}
        {tab === "apps" && <AppsTab />}
        {tab === "routes" && <RoutesTab />}
      </div>
    </div>
  );
};
