import { configureHttpClient } from "./api/httpClient";
import { AdminCulturaPage } from "./pages/AdminCulturaPage";
import { PainelCulturaPage } from "./pages/PainelCulturaPage";
import { resolveCulturaDelpiRoute } from "./utils/route";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const route = resolveCulturaDelpiRoute(pathname);

  if (route === "admin") {
    return <AdminCulturaPage />;
  }

  return <PainelCulturaPage />;
}
