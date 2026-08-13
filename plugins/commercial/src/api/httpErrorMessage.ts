import { HTTP_ERROR_CONTENT } from "../content/httpErrorContent";

const HTML_OR_GATEWAY_MARKERS = [
  "<!doctype",
  "<html",
  "cloudflare",
  "bad gateway",
  "origin web server",
  "cf-ray",
] as const;

export function looksLikeGatewayOrHtmlNoise(text: string): boolean {
  const normalized = text.trim().toLowerCase();
  if (!normalized) return false;
  return HTML_OR_GATEWAY_MARKERS.some((marker) => normalized.includes(marker));
}

/** Mensagem segura para UI — nunca propaga HTML/Cloudflare cru. */
export function resolveHttpErrorMessage(
  status: number,
  rawMessage: string | null | undefined,
): string {
  const fallback = HTTP_ERROR_CONTENT.httpFallback(status);
  if (status >= 502 && status <= 504) {
    return HTTP_ERROR_CONTENT.gatewayUnavailable;
  }
  const candidate = (rawMessage ?? "").trim();
  if (!candidate) return fallback;
  if (looksLikeGatewayOrHtmlNoise(candidate)) {
    return HTTP_ERROR_CONTENT.gatewayUnavailable;
  }
  return candidate;
}

export function formatApiErrorBody(errorBody: unknown, fallback: string): string {
  if (!errorBody || typeof errorBody !== "object") {
    return fallback;
  }

  const record = errorBody as Record<string, unknown>;
  const base =
    (typeof record.message === "string" && record.message) ||
    (typeof record.detail === "string" && record.detail) ||
    fallback;
  const error = record.error;

  if (error && typeof error === "object") {
    const code = (error as { code?: unknown }).code;
    if (typeof code === "string" && code) {
      return `[${code}] ${base}`;
    }
  }

  return base;
}
