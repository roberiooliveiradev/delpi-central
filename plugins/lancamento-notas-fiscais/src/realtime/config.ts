import { getLnfApiBase } from "../data/api/invoicePostingApi";

const BFF_MARKER = "/apps/controllership-finance-api/lancamento-notas-fiscais";

export function isLnfRealtimeFlagOn(): boolean {
  const raw =
    typeof import.meta !== "undefined"
      ? import.meta.env?.VITE_LNF_REALTIME_ENABLED
      : undefined;
  if (raw === true) return true;
  if (typeof raw !== "string") return false;
  const normalized = raw.trim().toLowerCase();
  return normalized === "true" || normalized === "1" || normalized === "yes";
}

export function isLnfApiBaseOnBff(apiBase = getLnfApiBase()): boolean {
  return apiBase.replace(/\/+$/, "").includes(BFF_MARKER);
}

/** Conecta só com flag on E base = BFF (contrato §2.3). */
export function shouldConnectLnfRealtime(): boolean {
  return isLnfRealtimeFlagOn() && isLnfApiBaseOnBff();
}

export function buildLnfRealtimeWsUrl(token: string): string {
  const hasWindow = typeof window !== "undefined";
  const protocol =
    hasWindow && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = hasWindow ? window.location.host : "localhost";
  const url = new URL(
    `${protocol}//${host}/apps/controllership-finance-api/lancamento-notas-fiscais/realtime`,
  );
  url.searchParams.set("token", token);
  return url.toString();
}

/**
 * Política de reconexão do LNF.
 *
 * Handshake recusado sem token responde HTTP 401 no servidor; no navegador
 * isso chega como close 1006 (não 1008). Só 1008 + mesma URL encerra.
 */
export function shouldReconnectLnfRealtime({
  closeCode,
  sameUrl,
}: {
  closeCode: number;
  sameUrl: boolean;
}): boolean {
  if (closeCode === 1008 && sameUrl) return false;
  return true;
}
