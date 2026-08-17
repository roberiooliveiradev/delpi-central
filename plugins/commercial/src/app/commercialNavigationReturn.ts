/**
 * Navegação de retorno canônica do Portal Comercial (`returnTo` + `returnLabel`).
 * Evita open-redirect e caminhos fora do prefixo do plugin.
 */

import { normalizeBasePath, normalizePathname } from "./pluginRoutes";

export const RETURN_TO_PARAM = "returnTo";
export const RETURN_LABEL_PARAM = "returnLabel";

export type CommercialBackNav = {
  href: string;
  label: string;
};

export type ReturnNavOptions = {
  returnTo?: string | null;
  returnLabel?: string | null;
};

function isUnsafeReturnCandidate(raw: string): boolean {
  const trimmed = raw.trim();
  if (!trimmed) return true;
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)) return true;
  if (trimmed.startsWith("//")) return true;
  if (trimmed.includes("\\")) return true;
  return false;
}

/**
 * Aceita path absoluto sob o basePath do plugin (ex.: `/apps/commercial/customers/...`)
 * ou path relativo ao plugin (ex.: `customers/0001/01?secao=pedidos`).
 */
export function sanitizeReturnTo(
  raw: string | null | undefined,
  basePath?: string,
): string | null {
  if (raw == null) return null;
  let value = String(raw).trim();
  if (!value || isUnsafeReturnCandidate(value)) return null;

  try {
    value = decodeURIComponent(value);
  } catch {
    return null;
  }
  if (isUnsafeReturnCandidate(value)) return null;

  const base = normalizeBasePath(basePath);
  let pathWithSearch = value;
  if (!pathWithSearch.startsWith("/")) {
    pathWithSearch = `${base}/${pathWithSearch.replace(/^\/+/, "")}`;
  }

  const qIndex = pathWithSearch.indexOf("?");
  const pathOnly = qIndex >= 0 ? pathWithSearch.slice(0, qIndex) : pathWithSearch;
  const search = qIndex >= 0 ? pathWithSearch.slice(qIndex) : "";
  const normalized = normalizePathname(pathOnly);

  if (normalized !== base && !normalized.startsWith(`${base}/`)) {
    return null;
  }
  return `${normalized}${search}`;
}

export function sanitizeReturnLabel(raw: string | null | undefined): string | null {
  if (raw == null) return null;
  const label = String(raw).trim().replace(/\s+/g, " ");
  if (!label) return null;
  if (label.length > 80) return label.slice(0, 80).trim();
  return label;
}

export function parseReturnNavFromSearch(
  search: string | null | undefined,
  basePath?: string,
): ReturnNavOptions {
  const params = new URLSearchParams(
    (search || "").startsWith("?") ? (search || "").slice(1) : search || "",
  );
  return {
    returnTo: sanitizeReturnTo(params.get(RETURN_TO_PARAM), basePath),
    returnLabel: sanitizeReturnLabel(params.get(RETURN_LABEL_PARAM)),
  };
}

export function resolvePagePathBack(
  search: string | null | undefined,
  fallback: CommercialBackNav,
  basePath?: string,
): CommercialBackNav {
  const parsed = parseReturnNavFromSearch(search, basePath);
  if (parsed.returnTo) {
    return {
      href: parsed.returnTo,
      label: parsed.returnLabel || fallback.label,
    };
  }
  return fallback;
}

/** Anexa returnTo/returnLabel a um href de detalhe (preserva query existente). */
export function buildHrefWithReturn(
  targetHref: string,
  options: ReturnNavOptions,
  basePath?: string,
): string {
  const safeTo = sanitizeReturnTo(options.returnTo, basePath);
  const safeLabel = sanitizeReturnLabel(options.returnLabel);
  if (!safeTo && !safeLabel) return targetHref;

  const qIndex = targetHref.indexOf("?");
  const path = qIndex >= 0 ? targetHref.slice(0, qIndex) : targetHref;
  const params = new URLSearchParams(qIndex >= 0 ? targetHref.slice(qIndex + 1) : "");
  if (safeTo) params.set(RETURN_TO_PARAM, safeTo);
  else params.delete(RETURN_TO_PARAM);
  if (safeLabel) params.set(RETURN_LABEL_PARAM, safeLabel);
  else params.delete(RETURN_LABEL_PARAM);
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

/** returnTo a partir da URL atual (pathname + search). */
export function currentLocationAsReturnTo(): string {
  if (typeof window === "undefined") return "";
  return `${normalizePathname(window.location.pathname)}${window.location.search || ""}`;
}

/** Pacote returnNav a partir da URL atual + rótulo do Path. */
export function currentReturnNav(returnLabel: string): ReturnNavOptions {
  return {
    returnTo: currentLocationAsReturnTo(),
    returnLabel: sanitizeReturnLabel(returnLabel),
  };
}
