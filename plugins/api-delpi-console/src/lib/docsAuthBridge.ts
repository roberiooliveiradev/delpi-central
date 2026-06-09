import { getAuthToken, getMessageTargetOrigin } from "./auth";

/** Envia JWT à documentação interativa da api-delpi (main.py → DELPI_AUTH). */
export function postAuthToDocsIframe(iframe: HTMLIFrameElement | null): void {
  if (!iframe?.contentWindow) return;

  const token = getAuthToken();
  if (!token) return;

  iframe.contentWindow.postMessage(
    { type: "DELPI_AUTH", token },
    getMessageTargetOrigin(),
  );
}

export function setupDocsMessageListener(
  iframe: HTMLIFrameElement | null,
  onUnauthorized?: () => void,
): () => void {
  const handler = (event: MessageEvent) => {
    if (event.origin !== getMessageTargetOrigin()) return;

    if (event.data?.type === "DELPI_AUTH_READY") {
      postAuthToDocsIframe(iframe);
      return;
    }

    if (event.data?.type === "DELPI_REFRESH_REQUEST") {
      onUnauthorized?.();
      window.setTimeout(() => postAuthToDocsIframe(iframe), 300);
    }
  };

  window.addEventListener("message", handler);
  return () => window.removeEventListener("message", handler);
}
