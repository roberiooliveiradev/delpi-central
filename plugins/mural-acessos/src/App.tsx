import { useEffect, useState } from "react";

import { configureHttpClient } from "./api/httpClient";
import { MuralAcessosListPage } from "./pages/MuralAcessosListPage";
import { MuralAcessosPage } from "./pages/MuralAcessosPage";
import { parseMuralPath } from "./utils/route";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
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

  const route = parseMuralPath(path || undefined);
  if (route.kind === "detail") {
    return <MuralAcessosPage hubId={route.hubId} />;
  }
  return <MuralAcessosListPage />;
}
