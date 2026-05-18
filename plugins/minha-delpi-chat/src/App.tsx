import { Suspense, lazy, useState } from "react";

import "./App.css";

import { ChatPage } from "./ui/pages/ChatPage";

const ChatAdminPage = lazy(() =>
  import("./ui/pages/ChatAdminPage").then((module) => ({
    default: module.ChatAdminPage,
  })),
);

export type AppProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  const [mode, setMode] = useState<"chat" | "admin">(
    pathname?.includes("/admin") ? "admin" : "chat",
  );
  const [adminInitialAgentId, setAdminInitialAgentId] = useState<string | null>(null);

  if (mode === "admin") {
    return (
      <Suspense
        fallback={
          <div className="minha-delpi-chat__loading-page">
            Carregando administração...
          </div>
        }
      >
        <ChatAdminPage
          getAccessToken={getAccessToken}
          initialAgentId={adminInitialAgentId}
          initialTab={adminInitialAgentId ? "agents" : undefined}
          onBack={() => {
            setAdminInitialAgentId(null);
            setMode("chat");
          }}
        />
      </Suspense>
    );
  }

  return (
    <ChatPage
      getAccessToken={getAccessToken}
      onOpenAdmin={(agentId) => {
        setAdminInitialAgentId(agentId ?? null);
        setMode("admin");
      }}
    />
  );
}
