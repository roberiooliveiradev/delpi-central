import { getAuthToken, getMessageTargetOrigin } from "./auth";
import { buildThemeMessage } from "./portalTheme";

function postToDocsIframe(iframe: HTMLIFrameElement | null, payload: unknown): void {
  if (!iframe?.contentWindow) return;
  iframe.contentWindow.postMessage(payload, getMessageTargetOrigin());
}

/** Envia JWT à documentação interativa da api-delpi (main.py → DELPI_AUTH). */
export function postAuthToDocsIframe(iframe: HTMLIFrameElement | null): void {
  const token = getAuthToken();
  if (!token) return;
  postToDocsIframe(iframe, { type: "DELPI_AUTH", token });
}

/** Sincroniza tema claro/escuro do portal com o Swagger embutido. */
export function postThemeToDocsIframe(iframe: HTMLIFrameElement | null): void {
  postToDocsIframe(iframe, buildThemeMessage());
}

export function syncDocsIframeBridge(iframe: HTMLIFrameElement | null): void {
  postThemeToDocsIframe(iframe);
  postAuthToDocsIframe(iframe);
}

type DocsIframeTarget = HTMLIFrameElement | null | (() => HTMLIFrameElement | null);

function resolveDocsIframe(target: DocsIframeTarget): HTMLIFrameElement | null {
  return typeof target === "function" ? target() : target;
}

export function setupDocsMessageListener(
  iframe: DocsIframeTarget,
  onUnauthorized?: () => void,
): () => void {
  const handler = (event: MessageEvent) => {
    if (event.origin !== getMessageTargetOrigin()) return;

    const frame = resolveDocsIframe(iframe);

    if (event.data?.type === "DELPI_AUTH_READY") {
      syncDocsIframeBridge(frame);
      return;
    }

    if (event.data?.type === "DELPI_REFRESH_REQUEST") {
      onUnauthorized?.();
      window.setTimeout(() => syncDocsIframeBridge(frame), 300);
    }
  };

  window.addEventListener("message", handler);
  return () => window.removeEventListener("message", handler);
}

export function setupDocsThemeObserver(
  iframe: HTMLIFrameElement | null,
): () => void {
  const sync = () => postThemeToDocsIframe(iframe);

  const observer = new MutationObserver(sync);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });

  const onStorage = (event: StorageEvent) => {
    if (event.key === "theme") sync();
  };
  window.addEventListener("storage", onStorage);

  return () => {
    observer.disconnect();
    window.removeEventListener("storage", onStorage);
  };
}
