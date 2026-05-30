import { Suspense, lazy, useMemo } from "react";

import "./App.css";

import { buildChatHref, parseChatRoute } from "./navigation/chatRoutes";
import { navigateChatHref } from "./navigation/chatNavigation";
import { ChatAnimatedPanel } from "./ui/components/ChatAnimatedPanel";
import { ChatPage } from "./ui/pages/ChatPage";

const ChatAdminPage = lazy(() =>
  import("./ui/pages/ChatAdminPage").then((module) => ({
    default: module.ChatAdminPage,
  })),
);

export type AppProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  pathname?: string;
  search?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  const route = useMemo(() => parseChatRoute(pathname), [pathname]);

  if (route.kind === "admin" || route.kind === "admin-agent") {
    return (
      <Suspense
        fallback={
          <div className="minha-delpi-chat__loading-page">
            Carregando administração...
          </div>
        }
      >
        <ChatAnimatedPanel panelKey="admin" variant="page" className="mdc-chat-page-panel--fill">
          <ChatAdminPage
            getAccessToken={getAccessToken}
            initialTab={route.kind === "admin-agent" ? "agents" : undefined}
            initialAgentId={route.kind === "admin-agent" ? route.agentId : null}
            onBack={() => navigateChatHref(buildChatHref({ kind: "home" }))}
          />
        </ChatAnimatedPanel>
      </Suspense>
    );
  }

  return (
    <ChatPage
      getAccessToken={getAccessToken}
      pathname={pathname}
      initialRoute={route}
      onOpenAdmin={() => navigateChatHref(buildChatHref({ kind: "admin" }))}
    />
  );
}
