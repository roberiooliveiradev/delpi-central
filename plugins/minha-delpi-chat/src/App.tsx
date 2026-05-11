import { useState } from "react";

import "./App.css";

import { ChatPage } from "./ui/pages/ChatPage";
import { ChatAdminPage } from "./ui/pages/ChatAdminPage";

export type AppProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  const [mode, setMode] = useState<"chat" | "admin">(
    pathname?.includes("/admin") ? "admin" : "chat",
  );

  if (mode === "admin") {
    return (
      <ChatAdminPage
        getAccessToken={getAccessToken}
        onBack={() => setMode("chat")}
      />
    );
  }

  return (
    <ChatPage
      getAccessToken={getAccessToken}
      onOpenAdmin={() => setMode("admin")}
    />
  );
}
