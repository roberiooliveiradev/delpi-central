import { DashboardLmpsPage } from "./pages/DashboardLmpsPage";

type AppProps = {
  token?: string;
};

export default function App({ token }: AppProps) {
  return <DashboardLmpsPage token={token} />;
}