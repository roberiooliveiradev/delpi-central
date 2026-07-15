import { configureHttpClient } from "./api/httpClient";
import { InadimplenciaPage } from "./app/InadimplenciaPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  basePath?: string;
  pathname?: string;
  search?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return <InadimplenciaPage />;
}
