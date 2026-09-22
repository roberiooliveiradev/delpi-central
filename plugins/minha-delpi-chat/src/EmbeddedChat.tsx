import type { CSSProperties } from "react";
import { useEffect, useMemo } from "react";

import { ChatPage } from "./ui/pages/ChatPage";
import { setChatNavigationHostMode } from "./navigation/chatNavigation";
import { parseChatRoute } from "./navigation/chatRoutes";
import {
  buildTvDashboardHostContext,
  type ChatHostContext,
} from "./hostSurfaceContext";
import { buildEmbeddedSessionScopeKey } from "./embeddedSessionPersistence";

export type TvWorkspaceContext = {
  playlistId?: string | null;
  slideId?: string | null;
  selectedBlockIds?: string[];
  selectedBlockTypes?: string[];
  focusBlockId?: string | null;
  focusBlockType?: string | null;
  operationId?: string | null;
  dataSourceId?: string | null;
  selectedDataSourceId?: string | null;
  selectedVisualId?: string | null;
  dataSources?: Array<{ id: string; operationId: string; label: string }>;
  hasLocalDraft?: boolean;
  presetKey?: string | null;
  nativeConfigSummary?: {
    blockCount?: number;
    dataSourceOperationIds?: string[];
  } | null;
};

export type EmbeddedChatHostCallbacks = {
  /** Persiste drafts do host antes de ações sensíveis no chat embutido. */
  flushBeforeMutation?: () => Promise<void>;
};

export type EmbeddedChatProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  agentId?: string | null;
  surface?: "tv-dashboard" | string;
  workspaceContext?: TvWorkspaceContext | null;
  hostCallbacks?: EmbeddedChatHostCallbacks;
  className?: string;
  style?: CSSProperties;
  pathname?: string;
};

/**
 * Remote parcial MF para hosts: chat sem shell admin completo.
 * Mutação TV fica no especialista VISTA; o embed só injeta hostContext ambient.
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

  const embeddedScopeKey = useMemo(
    () =>
      buildEmbeddedSessionScopeKey({
        surface,
        playlistId: workspaceContext?.playlistId,
      }),
    [surface, workspaceContext?.playlistId],
  );

  useEffect(() => {
    setChatNavigationHostMode("embedded");
    return () => setChatNavigationHostMode("portal");
  }, []);

  const hostContext = useMemo<ChatHostContext>(
    () =>
      buildTvDashboardHostContext({
        surface,
        playlistId: workspaceContext?.playlistId,
        slideId: workspaceContext?.slideId,
        selectedBlockIds: workspaceContext?.selectedBlockIds,
        selectedBlockTypes: workspaceContext?.selectedBlockTypes,
        focusBlockId: workspaceContext?.focusBlockId,
        focusBlockType: workspaceContext?.focusBlockType,
        operationId:
          workspaceContext?.operationId ||
          workspaceContext?.nativeConfigSummary?.dataSourceOperationIds?.[0] ||
          null,
        dataSourceId: workspaceContext?.dataSourceId,
        selectedDataSourceId: workspaceContext?.selectedDataSourceId,
        selectedVisualId: workspaceContext?.selectedVisualId,
        dataSources: workspaceContext?.dataSources,
        hasLocalDraft: workspaceContext?.hasLocalDraft,
        presetKey: workspaceContext?.presetKey,
      }),
    [
      surface,
      workspaceContext?.playlistId,
      workspaceContext?.slideId,
      workspaceContext?.selectedBlockIds,
      workspaceContext?.selectedBlockTypes,
      workspaceContext?.focusBlockId,
      workspaceContext?.focusBlockType,
      workspaceContext?.operationId,
      workspaceContext?.dataSourceId,
      workspaceContext?.selectedDataSourceId,
      workspaceContext?.selectedVisualId,
      workspaceContext?.dataSources,
      workspaceContext?.hasLocalDraft,
      workspaceContext?.presetKey,
      workspaceContext?.nativeConfigSummary?.dataSourceOperationIds,
    ],
  );

  const contextBanner = useMemo(() => {
    if (
      !workspaceContext?.playlistId &&
      !workspaceContext?.slideId &&
      !(workspaceContext?.selectedBlockIds && workspaceContext.selectedBlockIds.length > 0)
    ) {
      return null;
    }
    const playlistShort = workspaceContext.playlistId
      ? `playlist ${String(workspaceContext.playlistId).slice(0, 8)}…`
      : null;
    const slideShort = workspaceContext.slideId
      ? `slide ${String(workspaceContext.slideId).slice(0, 8)}…`
      : null;
    const selectionCount = workspaceContext.selectedBlockIds?.length ?? 0;
    const focusType = workspaceContext.focusBlockType || workspaceContext.selectedBlockTypes?.[0];
    const selectionShort =
      selectionCount > 0
        ? focusType
          ? `${selectionCount} bloco(s) · ${focusType}`
          : `${selectionCount} bloco(s)`
        : null;
    return [playlistShort, slideShort, selectionShort].filter(Boolean).join(" · ");
  }, [
    workspaceContext?.playlistId,
    workspaceContext?.slideId,
    workspaceContext?.selectedBlockIds,
    workspaceContext?.selectedBlockTypes,
    workspaceContext?.focusBlockType,
  ]);

  return (
    <div
      className={["mdc-embedded-chat", className].filter(Boolean).join(" ")}
      style={style}
      data-surface={surface}
      data-agent-id={agentId || undefined}
      data-playlist-id={workspaceContext?.playlistId || undefined}
      data-slide-id={workspaceContext?.slideId || undefined}
      data-selected-block-count={
        workspaceContext?.selectedBlockIds?.length
          ? String(workspaceContext.selectedBlockIds.length)
          : undefined
      }
      data-embedded-scope={embeddedScopeKey}
    >
      {contextBanner ? (
        <div className="mdc-embedded-chat__context" role="status">
          Contexto TV: {contextBanner}
        </div>
      ) : null}
      <div className="mdc-embedded-chat__body">
        <ChatPage
          getAccessToken={getAccessToken}
          pathname={pathname}
          initialRoute={route}
          variant="embedded"
          hostContext={hostContext}
          beforeHostMutation={hostCallbacks?.flushBeforeMutation}
          embeddedScopeKey={embeddedScopeKey}
        />
      </div>
    </div>
  );
}

export default EmbeddedChat;
