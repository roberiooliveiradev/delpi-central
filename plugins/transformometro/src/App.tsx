import { HomePage } from "./ui/pages/HomePage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  return <HomePage getAccessToken={getAccessToken} />;
}
