import { ExecutiveDashboardPage } from "./ui/pages/ExecutiveDashboardPage";
import { DepartmentDetailsPage } from "./ui/pages/DepartmentDetailsPage";
import { DepartmentsPage } from "./ui/pages/DepartmentsPage";
import { IndicatorsPage } from "./ui/pages/IndicatorsPage";
import { TrendsPage } from "./ui/pages/TrendsPage";
import { AlertsPage } from "./ui/pages/AlertsPage";
import { PresentationPage } from "./ui/pages/PresentationPage";
import { SettingsPage } from "./ui/pages/SettingsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  if (pathname === "/apps/strategic-indicators/departments") {
    return <DepartmentsPage getAccessToken={getAccessToken} />;
  }

  if (pathname?.startsWith("/apps/strategic-indicators/departments/")) {
    return (
      <DepartmentDetailsPage
        pathname={pathname}
        getAccessToken={getAccessToken}
      />
    );
  }

  if (pathname === "/apps/strategic-indicators/indicators") {
    return <IndicatorsPage />;
  }

  if (pathname === "/apps/strategic-indicators/trends") {
    return <TrendsPage />;
  }

  if (pathname === "/apps/strategic-indicators/alerts") {
    return <AlertsPage />;
  }

  if (pathname === "/apps/strategic-indicators/presentation") {
    return <PresentationPage />;
  }

  if (pathname === "/apps/strategic-indicators/settings") {
    return <SettingsPage getAccessToken={getAccessToken} />;
  }

  return <ExecutiveDashboardPage getAccessToken={getAccessToken} />;
}