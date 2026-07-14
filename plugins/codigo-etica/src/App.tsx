import { CodigoEticaPage } from "./pages/CodigoEticaPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App(_: AppProps) {
  return <CodigoEticaPage />;
}
