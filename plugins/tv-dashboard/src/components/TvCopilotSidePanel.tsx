import { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { BranchScope } from "../api/tvDashboardApi";
import { getAccessToken as getTvAccessToken } from "../api/httpClient";
import { TV_COPILOT_CONTENT as C } from "../content/tvCopilotContent";
import { hasLocalComunicadoEdits } from "../utils/comunicadoSlideDraftPreferences";
import { flushRegisteredEditorAutosave } from "../utils/previewHandoff";
import { applyTvCopilotPreviewSideEffects } from "../utils/tvCopilotSideEffects";
import { useOptionalComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  playlistId?: string;
  slideId?: string | null;
  branchScope?: BranchScope | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  /** Oculta título/hint (quando o dock já tem FormatPaneShell). */
  embedded?: boolean;
};

type EmbeddedMountApi = {
  mount: (el: HTMLElement, props?: Record<string, unknown>) => void;
  update?: (el: HTMLElement, props?: Record<string, unknown>) => void;
  unmount?: (el?: HTMLElement) => void;
};

const CHAT_EMBEDDED_REMOTE_ENTRY =
  (typeof import.meta !== "undefined" &&
    (import.meta as { env?: { VITE_MINHA_DELPI_CHAT_REMOTE?: string } }).env
      ?.VITE_MINHA_DELPI_CHAT_REMOTE) ||
  "/apps/minha-delpi-chat/assets/remoteEntry.js";

async function loadEmbeddedChatModule(): Promise<EmbeddedMountApi> {
  const mod: Record<string, unknown> = await import(
    /* @vite-ignore */ CHAT_EMBEDDED_REMOTE_ENTRY
  );
  const container = (mod.get ? mod : (mod.default as Record<string, unknown> | undefined)) as
    | {
        get?: (module: string) => Promise<() => unknown>;
        init?: (shareScope: unknown) => Promise<void> | void;
      }
    | undefined;

  if (!container?.get) {
    throw new Error(`remoteEntry sem container.get(): ${CHAT_EMBEDDED_REMOTE_ENTRY}`);
  }

  const shareScope =
    (window as unknown as { __federation_shared__?: { default?: unknown } }).__federation_shared__
      ?.default ??
    (window as unknown as { __federation_shared__?: unknown }).__federation_shared__ ??
    {};

  if (typeof container.init === "function") {
    try {
      await container.init(shareScope);
    } catch {
      // init idempotente — ignore se o share scope já foi inicializado
    }
  }

  const factory = await container.get("./EmbeddedChat");
  const exposed = factory();
  const api = (exposed && typeof exposed === "object" ? exposed : {}) as EmbeddedMountApi;
  if (typeof api.mount !== "function") {
    throw new Error("EmbeddedChat não expôs mount()");
  }
  return api;
}

/**
 * Host do remote `./EmbeddedChat` (minha-delpi-chat) via remoteEntry em runtime.
 * Não declara o chat como remote no vite.config do TV (evita regressão MF no plugin-ui).
 * Mutações persistidas atualizam o editor pelo WS `presentation_updated`.
 */
export function TvCopilotSidePanel({
  playlistId: playlistIdProp,
  slideId: slideIdProp,
  getAccessToken: getAccessTokenProp,
  embedded = false,
}: Props) {
  const editor = useOptionalComunicadoEditor();
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const apiRef = useRef<EmbeddedMountApi | null>(null);
  const resolveAccessToken = useCallback(() => {
    if (getAccessTokenProp) return getAccessTokenProp();
    return getTvAccessToken();
  }, [getAccessTokenProp]);

  const playlistId = playlistIdProp ?? editor?.playlistId ?? "";
  const slideId = slideIdProp ?? editor?.appliedSlideId ?? null;
  const blocks = editor?.blocks;
  const selectedIds = editor?.selectedIds ?? [];
  const selectedBlocks = editor?.selectedBlocks ?? [];

  const workspaceContext = useMemo(() => {
    const dataSources = (blocks || [])
      .filter((b) => b.type === "data_source")
      .map((b) => {
        const binding = "dataBinding" in b ? b.dataBinding : null;
        const operationId =
          binding && typeof binding === "object" && "operationId" in binding
            ? String((binding as { operationId?: string }).operationId || "")
            : "";
        const label =
          binding && typeof binding === "object" && "label" in binding
            ? String((binding as { label?: string }).label || "")
            : "";
        return {
          id: String(b.id || ""),
          operationId,
          label: label || operationId,
        };
      })
      .filter((item) => item.id && item.operationId);

    const dataSourceOperationIds = dataSources.map((item) => item.operationId);

    const selectedBlockTypes: string[] = [];
    const seenTypes = new Set<string>();
    for (const id of selectedIds) {
      const block = selectedBlocks.find((b) => b.id === id) ?? blocks?.find((b) => b.id === id);
      const type = block?.type ? String(block.type) : "";
      if (!type || seenTypes.has(type)) continue;
      seenTypes.add(type);
      selectedBlockTypes.push(type);
    }

    const focusBlockId = selectedIds[selectedIds.length - 1] ?? null;
    const focusBlock =
      (focusBlockId
        ? selectedBlocks.find((b) => b.id === focusBlockId) ??
          blocks?.find((b) => b.id === focusBlockId)
        : null) ?? null;

    const focusBlockType = focusBlock?.type ? String(focusBlock.type) : selectedBlockTypes[0] ?? null;
    const isDataView =
      focusBlockType === "kpi_view" ||
      focusBlockType === "chart_view" ||
      focusBlockType === "table_view";

    let focusDataSourceId: string | null = null;
    let focusOperationId: string | null = null;
    let selectedDataSourceId: string | null = null;
    let selectedVisualId: string | null = null;

    if (focusBlock?.type === "data_source") {
      focusDataSourceId = String(focusBlock.id || "") || null;
      selectedDataSourceId = focusDataSourceId;
      const binding = "dataBinding" in focusBlock ? focusBlock.dataBinding : null;
      if (binding && typeof binding === "object" && "operationId" in binding) {
        focusOperationId =
          String((binding as { operationId?: string }).operationId || "") || null;
      }
    } else if (focusBlock && isDataView) {
      selectedVisualId = String(focusBlock.id || "") || null;
      const linked = String((focusBlock as { dataSourceId?: string }).dataSourceId || "");
      if (linked) {
        focusDataSourceId = linked;
        const match = dataSources.find((item) => item.id === linked);
        focusOperationId = match?.operationId || null;
      }
    } else if (focusBlock && "dataSourceId" in focusBlock) {
      const linked = String((focusBlock as { dataSourceId?: string }).dataSourceId || "");
      if (linked) {
        focusDataSourceId = linked;
        const match = dataSources.find((item) => item.id === linked);
        focusOperationId = match?.operationId || null;
      }
    }

    const operationId = focusOperationId || dataSourceOperationIds[0] || null;
    const dataSourceId = focusDataSourceId || dataSources[0]?.id || null;
    const hasLocalDraft = Boolean(
      playlistId &&
        slideId &&
        hasLocalComunicadoEdits({
          playlistId,
          slideId,
        }),
    );

    return {
      playlistId,
      slideId,
      selectedBlockIds: selectedIds,
      selectedBlockTypes,
      focusBlockId,
      focusBlockType,
      operationId,
      dataSourceId,
      selectedDataSourceId,
      selectedVisualId,
      dataSources,
      hasLocalDraft,
      presetKey: null,
      nativeConfigSummary: {
        blockCount: blocks?.length ?? 0,
        dataSourceOperationIds,
      },
    };
  }, [playlistId, slideId, blocks, selectedIds, selectedBlocks]);

  const hostCallbacks = useMemo(
    () => ({
      onPreviewPatch: (payload: {
        nativeConfig?: Record<string, unknown> | null;
        sideEffects?: Record<string, unknown> | null;
        sideEffectHints?: string[] | null;
      }) => {
        const result = applyTvCopilotPreviewSideEffects(payload, {
          replaceNativeConfig: (nativeConfig) => {
            if (editor?.replaceSlideNativeConfig) {
              editor.replaceSlideNativeConfig(nativeConfig);
              // Seleciona visual ligado ou fonte criada (paridade preferredView).
              const blocks = Array.isArray(nativeConfig.blocks)
                ? (nativeConfig.blocks as Array<Record<string, unknown>>)
                : [];
              const views = blocks.filter((b) => {
                const t = String(b.type || "");
                return (
                  (t === "kpi_view" || t === "chart_view" || t === "table_view") &&
                  String(b.dataSourceId || "").trim()
                );
              });
              const sources = blocks.filter((b) => String(b.type || "") === "data_source");
              const pick = views[views.length - 1] || sources[sources.length - 1];
              const pickId = pick ? String(pick.id || "").trim() : "";
              if (pickId && editor.selectBlocksByIds) {
                editor.selectBlocksByIds([pickId]);
              }
              return true;
            }
            if (editor?.applySlideTemplate) {
              editor.applySlideTemplate(nativeConfig);
              return true;
            }
            return false;
          },
          removeBlockIds: (ids) => {
            if (!editor?.selectBlocksByIds || !editor?.removeSelected) return false;
            editor.selectBlocksByIds(ids);
            editor.removeSelected();
            return true;
          },
          // Preview não persiste — não recarrega filmstrip do servidor.
          refreshFilmstrip: () => false,
        });

        if (result.appliedReplace || result.appliedRemove) {
          setStatus(C.previewAppliedLocal);
          return;
        }
        if (result.wantsRefreshFilmstrip) {
          setStatus(C.previewSlideReady);
          return;
        }
        setStatus(C.previewNeedsCustomSlide);
      },
      onApplyPatchResult: (payload: {
        ok: boolean;
        persisted?: boolean;
        target?: { playlistId?: string | null; slideId?: string | null };
        sideEffectHints?: string[] | null;
        sideEffects?: Record<string, unknown> | null;
      }) => {
        // Recibo apenas: o CRUD canônico publica `presentation_updated`.
        setStatus(payload.ok ? C.applyOk : C.applyFailed);
      },
      flushBeforeMutation: () => flushRegisteredEditorAutosave(),
    }),
    [editor],
  );

  const mountProps = useMemo(
    () => ({
      getAccessToken: resolveAccessToken,
      surface: "tv-dashboard",
      workspaceContext,
      hostCallbacks,
    }),
    [resolveAccessToken, workspaceContext, hostCallbacks],
  );

  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    let cancelled = false;

    void (async () => {
      try {
        const api = apiRef.current ?? (await loadEmbeddedChatModule());
        if (cancelled) return;
        apiRef.current = api;
        if (apiRef.current && typeof api.update === "function" && el.dataset.mounted === "1") {
          api.update(el, mountProps);
        } else {
          api.mount(el, mountProps);
          el.dataset.mounted = "1";
        }
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : C.remoteUnavailable);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [mountProps]);

  useEffect(() => {
    return () => {
      const el = hostRef.current;
      const api = apiRef.current;
      if (el && api?.unmount) {
        try {
          api.unmount(el);
        } catch {
          /* ignore */
        }
      }
    };
  }, []);

  return (
    <div className={["td-tv-copilot-panel", embedded ? "td-tv-copilot-panel--embedded" : null].filter(Boolean).join(" ")}>
      {embedded ? null : (
        <header className="td-tv-copilot-panel__header">
          <h3>{C.panelTitle}</h3>
          <p className="td-tv-copilot-panel__hint">{C.panelHint}</p>
        </header>
      )}
      {status ? <p className="td-tv-copilot-panel__status">{status}</p> : null}
      {embedded ? <p className="td-tv-copilot-panel__hint">{C.panelHint}</p> : null}
      {error ? (
        <div className="td-tv-copilot-panel__fallback" role="alert">
          <p>{C.remoteUnavailable}</p>
          <p className="td-tv-copilot-panel__fallback-detail">{error}</p>
          <p>{C.usePortalChat}</p>
          <ul>
            <li>
              playlistId: <code>{playlistId || "—"}</code>
            </li>
            <li>
              slideId: <code>{slideId || "—"}</code>
            </li>
            <li>
              seleção:{" "}
              <code>
                {(workspaceContext.selectedBlockIds || []).length > 0
                  ? workspaceContext.selectedBlockIds.join(", ")
                  : "—"}
              </code>
            </li>
          </ul>
        </div>
      ) : (
        <div className="td-tv-copilot-panel__mount" ref={hostRef} />
      )}
    </div>
  );
}

export const TvCopilotSidePanelLazy = lazy(async () => ({
  default: TvCopilotSidePanel,
}));

export function TvCopilotSidePanelSuspense(props: Props) {
  return (
    <Suspense fallback={<div className="td-tv-copilot-panel__loading">{C.loading}</div>}>
      <TvCopilotSidePanelLazy {...props} embedded={props.embedded ?? true} />
    </Suspense>
  );
}
