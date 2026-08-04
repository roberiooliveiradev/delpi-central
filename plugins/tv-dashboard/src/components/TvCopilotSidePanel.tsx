import { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { BranchScope } from "../api/tvDashboardApi";
import { getAccessToken as getTvAccessToken } from "../api/httpClient";
import { TV_COPILOT_CONTENT as C } from "../content/tvCopilotContent";
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

  const workspaceContext = useMemo(() => {
    const dataSourceOperationIds = (blocks || [])
      .filter((b) => b.type === "data_source")
      .map((b) => {
        const binding = "dataBinding" in b ? b.dataBinding : null;
        return binding && typeof binding === "object" && "operationId" in binding
          ? String((binding as { operationId?: string }).operationId || "")
          : "";
      })
      .filter(Boolean);
    return {
      playlistId,
      slideId,
      selectedBlockIds: selectedIds,
      nativeConfigSummary: {
        blockCount: blocks?.length ?? 0,
        dataSourceOperationIds,
      },
    };
  }, [playlistId, slideId, blocks, selectedIds]);

  const hostCallbacks = useMemo(
    () => ({
      onPreviewPatch: (payload: {
        nativeConfig?: Record<string, unknown> | null;
      }) => {
        if (payload.nativeConfig && editor?.applySlideTemplate) {
          editor.applySlideTemplate(payload.nativeConfig);
          setStatus(C.previewAppliedLocal);
          return;
        }
        setStatus(C.previewNeedsCustomSlide);
      },
      onApplyPatchResult: (payload: { ok: boolean; persisted?: boolean }) => {
        setStatus(payload.ok ? C.applyOk : C.applyFailed);
      },
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
