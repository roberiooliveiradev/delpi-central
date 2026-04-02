import { ExecutiveDashboardPage } from "./ui/pages/ExecutiveDashboardPage";
import { DepartmentDetailsPage } from "./ui/pages/DepartmentDetailsPage";
import { DepartmentsPage } from "./ui/pages/DepartmentsPage";
import { IndicatorsPage } from "./ui/pages/IndicatorsPage";
import { TrendsPage } from "./ui/pages/TrendsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  void getAccessToken;

  if (pathname === "/apps/strategic-indicators/departments") {
    return <DepartmentsPage />;
  }

  if (pathname?.startsWith("/apps/strategic-indicators/departments/")) {
    return <DepartmentDetailsPage pathname={pathname} />;
  }

  if (pathname === "/apps/strategic-indicators/indicators") {
    return <IndicatorsPage />;
  }

  if (pathname === "/apps/strategic-indicators/trends") {
    return <TrendsPage />;
  }

  return <ExecutiveDashboardPage />;
}