import type { CSSProperties } from "react";
import { useEffect, useMemo } from "react";

import { ChatPage } from "./ui/pages/ChatPage";
import { setChatNavigationHostMode } from "./navigation/chatNavigation";
import { parseChatRoute } from "./navigation/chatRoutes";
import {
  buildTvDashboardHostContext,
  type ChatHostContext,
  type TvCopilotPreviewPatchPayload,
  type TvCopilotSideEffectHint,
} from "./hostSurfaceContext";
import { buildEmbeddedSessionScopeKey } from "./embeddedSessionPersistence";

export type TvWorkspaceContext = {
  playlistId?: string | null;
  slideId?: string | null;
  selectedBlockIds?: string[];
  /** Tipos dos blocos selecionados (resumo do foco). */
  selectedBlockTypes?: string[];
  /** Primeiro bloco em foco. */
  focusBlockId?: string | null;
  focusBlockType?: string | null;
  /** operationId da fonte em foco / primeira fonte do slide. */
  operationId?: string | null;
  /** Id do bloco data_source em foco. */
  dataSourceId?: string | null;
  selectedDataSourceId?: string | null;
  selectedVisualId?: string | null;
  dataSources?: Array<{ id: string; operationId: string; label: string }>;
  hasLocalDraft?: boolean;
  /** Preset do slide, quando o host souber. */
  presetKey?: string | null;
  /** Resumo do native_config sem resolved — só metadados. */
  nativeConfigSummary?: {
    blockCount?: number;
    dataSourceOperationIds?: string[];
  } | null;
};

export type EmbeddedChatHostCallbacks = {
  /** Persiste drafts do host antes de o chat planejar/executar uma mutação. */
  flushBeforeMutation?: () => Promise<void>;
  /** Preview do patch aplicado ao draft local do editor (sem persistir). */
  onPreviewPatch?: (payload: TvCopilotPreviewPatchPayload) => void;
  onApplyPatchResult?: (payload: {
    ok: boolean;
    persisted?: boolean;
    target?: { playlistId?: string | null; slideId?: string | null };
    sideEffectHints?: TvCopilotSideEffectHint[] | null;
    sideEffects?: Record<string, unknown> | null;
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
 *
 * Contexto ambient: surface + playlist/slide + seleção vão em todo send/stream via hostContext —
 * o usuário não precisa lembrar o chat de que está no TV Dashboard.
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

  useEffect(() => {
    if (typeof window === "undefined") return;
    const win = window as unknown as {
      __DELPI_TV_COPILOT_HOST__?: EmbeddedChatHostCallbacks;
    };
    if (hostCallbacks) {
      win.__DELPI_TV_COPILOT_HOST__ = hostCallbacks;
    }
    return () => {
      if (win.__DELPI_TV_COPILOT_HOST__ === hostCallbacks) {
        delete win.__DELPI_TV_COPILOT_HOST__;
      }
    };
  }, [hostCallbacks]);

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
