import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { ReportEditorPage } from "./pages/ReportEditorPage";
import { ReportListPage } from "./pages/ReportListPage";
import { parseMetalographyPath } from "./utils/route";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export default function App({ getAccessToken, pathname, permissions, isSuperadmin }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const [path, setPath] = useState(pathname ?? "");

  useEffect(() => {
    setPath(pathname ?? window.location.pathname);
  }, [pathname]);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const route = parseMetalographyPath(path || undefined);
  if (route.kind === "create") {
    return <ReportEditorPage readOnly={false} permissions={permissions} isSuperadmin={isSuperadmin} />;
  }
  if (route.kind === "editor") {
    return (
      <ReportEditorPage
        reportId={route.reportId}
        readOnly={route.readOnly}
        permissions={permissions}
        isSuperadmin={isSuperadmin}
      />
    );
  }
  return <ReportListPage permissions={permissions} isSuperadmin={isSuperadmin} />;
}
