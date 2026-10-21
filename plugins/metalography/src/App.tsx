import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { MetallographicWorkspace } from "./components/MetallographicWorkspace";
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
  return (
    <MetallographicWorkspace
      editing={route.kind !== "list"}
      reportId={route.kind === "editor" ? route.reportId : undefined}
      readOnly={route.kind === "editor" ? route.readOnly : false}
      permissions={permissions}
      isSuperadmin={isSuperadmin}
    />
  );
}
