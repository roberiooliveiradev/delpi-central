import { configureHttpClient } from "./api/httpClient";
import { useControleRetrabalhosRouterPath } from "./hooks/useControleRetrabalhosRouterPath";
import { ControleRetrabalhosPage } from "./pages/ControleRetrabalhosPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useControleRetrabalhosRouterPath(pathnameFromHost);

  return <ControleRetrabalhosPage pathname={pathname} />;
}
