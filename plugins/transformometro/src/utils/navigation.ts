import { normalizeTransformometroPath } from "./routeParser";

export const TRANSFORMOMETRO_WORKSPACE_HASH_EVENT = "transformometro:workspace-hash";
/** Árvore do processo (melhorias/revisões) ficou desatualizada após mutação. */
export const TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT =
  "transformometro:workspace-tree-refresh";

const TREE_REFRESH_CHANNEL = "transformometro-workspace";

function splitPathAndHash(path: string): { pathname: string; hash: string } {
  const hashIndex = path.indexOf("#");
  if (hashIndex === -1) {
    return { pathname: normalizeTransformometroPath(path), hash: "" };
  }
  return {
    pathname: normalizeTransformometroPath(path.slice(0, hashIndex)),
    hash: path.slice(hashIndex),
  };
}

export function notifyWorkspaceHashChange() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event("hashchange"));
  window.dispatchEvent(new Event(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT));
}

function publishTreeRefreshToOtherTabs() {
  if (typeof window === "undefined" || typeof BroadcastChannel === "undefined") return;
  try {
    const channel = new BroadcastChannel(TREE_REFRESH_CHANNEL);
    channel.postMessage({ type: TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT });
    channel.close();
  } catch {
    /* BroadcastChannel indisponível — same-tab event ainda funciona */
  }
}

/** Pede ao ProcessoWorkspacePage para recarregar processo/instâncias/revisões da sidebar. */
export function requestWorkspaceTreeRefresh() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT));
  publishTreeRefreshToOtherTabs();
}

/**
 * Escuta tree-refresh na mesma aba (CustomEvent) e em outras abas (BroadcastChannel).
 * Retorna cleanup.
 */
export function subscribeWorkspaceTreeRefresh(handler: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;

  const onWindow = () => handler();
  window.addEventListener(TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT, onWindow);

  let channel: BroadcastChannel | null = null;
  if (typeof BroadcastChannel !== "undefined") {
    try {
      channel = new BroadcastChannel(TREE_REFRESH_CHANNEL);
      channel.onmessage = (event) => {
        const data = event.data as { type?: string } | null;
        if (data?.type === TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT) {
          handler();
        }
      };
    } catch {
      channel = null;
    }
  }

  return () => {
    window.removeEventListener(TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT, onWindow);
    channel?.close();
  };
}

export function navigateTransformometro(path: string) {
  if (typeof window === "undefined") return;

  const { pathname: targetPath, hash: targetHash } = splitPathAndHash(path);
  const currentPath = window.location.pathname;
  const currentHash = window.location.hash;

  if (currentPath === targetPath && currentHash === targetHash) {
    return;
  }

  const nextUrl = `${targetPath}${targetHash}`;

  if (currentPath === targetPath) {
    window.history.pushState(null, "", nextUrl);
    notifyWorkspaceHashChange();
    return;
  }

  window.history.pushState(null, "", nextUrl);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
