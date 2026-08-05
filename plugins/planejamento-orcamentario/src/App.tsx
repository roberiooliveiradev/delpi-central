import { configureHttpClient } from "./api/httpClient";
import {
  resolveAppRoute,
  resolveCapexInvestmentId,
  resolveCapexPlanId,
  resolvePersonnelPlanId,
} from "./utils/routing";
import { HomePage } from "./pages/HomePage";
import { OrientacoesPage } from "./pages/OrientacoesPage";
import { CapexMyCostCentersPage } from "./pages/CapexMyCostCentersPage";
import { CapexInvestmentFormPage } from "./pages/CapexInvestmentFormPage";
import { CapexReviewQueuePage } from "./pages/CapexReviewQueuePage";
import { CapexReviewDetailPage } from "./pages/CapexReviewDetailPage";
import { CapexConsolidationPage } from "./pages/CapexConsolidationPage";
import { PersonnelBudgetPage } from "./pages/PersonnelBudgetPage";
import { PersonnelReviewQueuePage } from "./pages/PersonnelReviewQueuePage";
import { PersonnelReviewDetailPage } from "./pages/PersonnelReviewDetailPage";
import { AdminHomePage } from "./pages/admin/AdminHomePage";
import { AdminExercisesPage } from "./pages/admin/AdminExercisesPage";
import { AdminGuidancePage } from "./pages/admin/AdminGuidancePage";
import { AdminScopesPage } from "./pages/admin/AdminScopesPage";
import { AdminResponsaveisPage } from "./pages/admin/AdminResponsaveisPage";
import { AdminCentrosCustoPage } from "./pages/admin/AdminCentrosCustoPage";
import { AdminCategoriasCapexPage } from "./pages/admin/AdminCategoriasCapexPage";
import { PageShell } from "./components/PageShell";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const route = resolveAppRoute(pathname);

  switch (route) {
    case "home":
      return <HomePage />;
    case "orientacoes":
      return <OrientacoesPage />;
    case "capex":
      return <CapexMyCostCentersPage />;
    case "capex-investment-new":
      return <CapexInvestmentFormPage mode="create" />;
    case "capex-investment-edit":
      return (
        <CapexInvestmentFormPage
          mode="edit"
          investmentId={resolveCapexInvestmentId(pathname)}
        />
      );
    case "capex-approvals":
      return <CapexReviewQueuePage />;
    case "capex-approval-detail":
      return (
        <CapexReviewDetailPage
          planId={resolveCapexPlanId(pathname)}
          pathname={pathname}
        />
      );
    case "capex-consolidation":
      return <CapexConsolidationPage />;
    case "pessoal":
      return <PersonnelBudgetPage />;
    case "pessoal-approvals":
      return <PersonnelReviewQueuePage />;
    case "pessoal-approval-detail":
      return (
        <PersonnelReviewDetailPage
          planId={resolvePersonnelPlanId(pathname)}
          pathname={pathname}
        />
      );
    case "admin":
      return <AdminHomePage />;
    case "admin-exercicios":
      return <AdminExercisesPage />;
    case "admin-orientacoes":
      return <AdminGuidancePage />;
    case "admin-escopos":
      return <AdminScopesPage />;
    case "admin-responsaveis":
      return <AdminResponsaveisPage />;
    case "admin-centros-de-custo":
      return <AdminCentrosCustoPage />;
    case "admin-categorias-capex":
      return <AdminCategoriasCapexPage />;
    default:
      return (
        <PageShell title="Página não encontrada" subtitle="Verifique o endereço ou use o menu do portal.">
          <p className="po-muted">A rota solicitada não existe neste aplicativo.</p>
        </PageShell>
      );
  }
}
