import "./App.css";

import { ChatPage } from "./ui/pages/ChatPage";

export type AppProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  return <ChatPage getAccessToken={getAccessToken} />;
}
