import { ExecutiveDashboardPage } from "./ui/pages/ExecutiveDashboardPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  void getAccessToken;

  return <ExecutiveDashboardPage />;
}