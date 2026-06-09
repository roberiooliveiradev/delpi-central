import { getAuthToken, getMessageTargetOrigin } from "./auth";

/** Envia JWT ao Swagger UI customizado da api-delpi (main.py → DELPI_AUTH). */
export function postAuthToSwaggerIframe(iframe: HTMLIFrameElement | null): void {
  if (!iframe?.contentWindow) return;

  const token = getAuthToken();
  if (!token) return;

  iframe.contentWindow.postMessage(
    { type: "DELPI_AUTH", token },
    getMessageTargetOrigin(),
  );
}

export function setupSwaggerMessageListener(
  iframe: HTMLIFrameElement | null,
  onUnauthorized?: () => void,
): () => void {
  const handler = (event: MessageEvent) => {
    if (event.origin !== getMessageTargetOrigin()) return;

    if (event.data?.type === "DELPI_AUTH_READY") {
      postAuthToSwaggerIframe(iframe);
      return;
    }

    if (event.data?.type === "DELPI_REFRESH_REQUEST") {
      onUnauthorized?.();
      window.setTimeout(() => postAuthToSwaggerIframe(iframe), 300);
    }
  };

  window.addEventListener("message", handler);
  return () => window.removeEventListener("message", handler);
}
