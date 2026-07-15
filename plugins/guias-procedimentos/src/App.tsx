import type { ReactNode } from "react";

import { configureHttpClient } from "./api/httpClient";
import { AdminAccessDenied } from "./components/AdminAccessDenied";
import { useGuiasPermissions } from "./hooks/useGuiasPermissions";
import { useGuiasProcedimentosRouterPath } from "./hooks/useGuiasProcedimentosRouterPath";
import { AdminDepartmentFormPage } from "./pages/admin/AdminDepartmentFormPage";
import { AdminDepartmentsPage } from "./pages/admin/AdminDepartmentsPage";
import { AdminHomePage } from "./pages/admin/AdminHomePage";
import { AdminProcedureFormPage } from "./pages/admin/AdminProcedureFormPage";
import { AdminProceduresPage } from "./pages/admin/AdminProceduresPage";
import { DepartmentPage } from "./pages/DepartmentPage";
import { GuideDetailPage } from "./pages/GuideDetailPage";
import { GuidesHomePage } from "./pages/GuidesHomePage";
import {
  isAdminView,
  parseGuiasProcedimentosPath,
} from "./utils/route";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  basePath?: string;
  /** true quando montado via `main.tsx` (Vite standalone). */
  standalone?: boolean;
};

function AdminGate({
  standalone,
  children,
}: {
  standalone?: boolean;
  children: ReactNode;
}) {
  const { canManage, loading, error } = useGuiasPermissions(true);

  if (loading) {
    return (
      <div className="dashboard-guias-procedimentos gp-page">
        <div className="gp-shell">
          <p className="gp-intro">Verificando permissões…</p>
        </div>
      </div>
    );
  }

  if (!canManage) {
    return (
      <AdminAccessDenied
        standalone={standalone}
        message={
          error === "Não autenticado."
            ? "É necessário estar autenticado para administrar este módulo."
            : "Você não tem permissão para administrar este módulo (guias-procedimentos.manage)."
        }
      />
    );
  }

  return children;
}

export default function App({
  pathname: pathnameFromHost,
  standalone = false,
  getAccessToken,
}: AppProps) {
  // Síncrono (igual quality-action-plans): o fetch de /me no primeiro render
  // precisa do token antes de qualquer useEffect.
  configureHttpClient(() => getAccessToken?.());

  const pathname = useGuiasProcedimentosRouterPath(pathnameFromHost);
  const route = parseGuiasProcedimentosPath(pathname);

  if (isAdminView(route.view)) {
    let adminPage: ReactNode = null;
    switch (route.view) {
      case "admin-home":
        adminPage = <AdminHomePage standalone={standalone} />;
        break;
      case "admin-departments":
        adminPage = <AdminDepartmentsPage standalone={standalone} />;
        break;
      case "admin-department-new":
        adminPage = <AdminDepartmentFormPage standalone={standalone} />;
        break;
      case "admin-department-edit":
        adminPage = (
          <AdminDepartmentFormPage id={route.id} standalone={standalone} />
        );
        break;
      case "admin-procedures":
        adminPage = <AdminProceduresPage standalone={standalone} />;
        break;
      case "admin-procedure-new":
        adminPage = <AdminProcedureFormPage standalone={standalone} />;
        break;
      case "admin-procedure-edit":
        adminPage = (
          <AdminProcedureFormPage id={route.id} standalone={standalone} />
        );
        break;
      default:
        adminPage = <AdminHomePage standalone={standalone} />;
    }
    return <AdminGate standalone={standalone}>{adminPage}</AdminGate>;
  }

  if (route.view === "department" && route.slug) {
    return <DepartmentPage slug={route.slug} standalone={standalone} />;
  }

  if (route.view === "detail" && route.slug) {
    return <GuideDetailPage slug={route.slug} standalone={standalone} />;
  }

  return <GuidesHomePage standalone={standalone} />;
}
