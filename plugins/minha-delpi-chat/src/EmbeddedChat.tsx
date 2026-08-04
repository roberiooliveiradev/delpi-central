import type { CSSProperties } from "react";
import { useEffect, useMemo } from "react";

import { ChatPage } from "./ui/pages/ChatPage";
import { setChatNavigationHostMode } from "./navigation/chatNavigation";
import { parseChatRoute } from "./navigation/chatRoutes";

export type TvWorkspaceContext = {
  playlistId?: string | null;
  slideId?: string | null;
  selectedBlockIds?: string[];
  /** Resumo do native_config sem resolved — só metadados. */
  nativeConfigSummary?: {
    blockCount?: number;
    dataSourceOperationIds?: string[];
  } | null;
};

export type EmbeddedChatHostCallbacks = {
  /** Preview do patch aplicado ao draft local do editor (sem persistir). */
  onPreviewPatch?: (payload: {
    nativeConfig?: Record<string, unknown> | null;
    diff?: Record<string, unknown> | null;
    ops?: unknown[];
  }) => void;
  onApplyPatchResult?: (payload: {
    ok: boolean;
    persisted?: boolean;
    target?: { playlistId?: string | null; slideId?: string | null };
  }) => void;
};

export type EmbeddedChatProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  agentId?: string | null;
  surface?: "tv-dashboard" | string;
  workspaceContext?: TvWorkspaceContext | null;
  hostCallbacks?: EmbeddedChatHostCallbacks;
  className?: string;
  style?: CSSProperties;
  /** Pathname interno do chat (default home). */
  pathname?: string;
};

/**
 * Remote parcial MF para hosts (TV Dashboard): chat sem shell admin completo.
 * Inteligência continua na minha-delpi-ai-api; host só injeta contexto e callbacks.
 */
export function EmbeddedChat({
  getAccessToken,
  agentId,
  surface = "tv-dashboard",
  workspaceContext,
  hostCallbacks,
  className,
  style,
  pathname,
}: EmbeddedChatProps) {
  const route = useMemo(() => parseChatRoute(pathname), [pathname]);

  useEffect(() => {
    setChatNavigationHostMode("embedded");
    return () => setChatNavigationHostMode("portal");
  }, []);

  const contextBanner = useMemo(() => {
    if (!workspaceContext?.playlistId && !workspaceContext?.slideId) return null;
    const parts = [
      workspaceContext.playlistId ? `playlist=${workspaceContext.playlistId}` : null,
      workspaceContext.slideId ? `slide=${workspaceContext.slideId}` : null,
      workspaceContext.selectedBlockIds?.length
        ? `blocos=${workspaceContext.selectedBlockIds.length}`
        : null,
    ].filter(Boolean);
    return parts.join(" · ");
  }, [workspaceContext]);

  // Expõe callbacks no window para o host/instrumentação (MVP A1).
  if (typeof window !== "undefined" && hostCallbacks) {
    (window as unknown as { __DELPI_TV_COPILOT_HOST__?: EmbeddedChatHostCallbacks }).__DELPI_TV_COPILOT_HOST__ =
      hostCallbacks;
  }

  return (
    <div
      className={["mdc-embedded-chat", className].filter(Boolean).join(" ")}
      style={style}
      data-surface={surface}
      data-agent-id={agentId || undefined}
      data-playlist-id={workspaceContext?.playlistId || undefined}
      data-slide-id={workspaceContext?.slideId || undefined}
    >
      {contextBanner ? (
        <div className="mdc-embedded-chat__context" role="status">
          Contexto TV: {contextBanner}
          {workspaceContext?.nativeConfigSummary?.dataSourceOperationIds?.length ? (
            <span className="mdc-embedded-chat__context-ops">
              {" "}
              · fontes:{" "}
              {workspaceContext.nativeConfigSummary.dataSourceOperationIds.slice(0, 4).join(", ")}
            </span>
          ) : null}
        </div>
      ) : null}
      <div className="mdc-embedded-chat__body">
        <ChatPage
          getAccessToken={getAccessToken}
          pathname={pathname}
          initialRoute={route}
          variant="embedded"
        />
      </div>
    </div>
  );
}

export default EmbeddedChat;
