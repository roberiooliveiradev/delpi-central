/**
 * Deep link de notificações → apps embedded (iframe) no portal.
 *
 * Contrato (qualquer integração externa / Core API):
 * - action.type = "portal_route"
 * - action.target = basePath do app no portal (ex.: /controle-mp, /apps/foo)
 * - metadata.deepPath = rota interna do filho (ex.: /conversations/109)
 * - metadata.source = id lógico do app (opcional, ex.: controle_mp)
 *
 * O filho deve escutar postMessage { type: "DELPI_NAVIGATE", path: deepPath }.
 */

const STORAGE_KEY = "delpi.embedded_app.pending_navigate";
const LEGACY_CONTROLE_MP_KEY = "delpi.controle_mp.pending_navigate";

export type EmbeddedAppNotificationMetadata = {
  source?: string;
  deepPath?: string;
  event?: string;
  dedupeKey?: string;
  [key: string]: unknown;
};

export type EmbeddedPendingNavigate = {
  portalRoute: string;
  deepPath: string;
  source?: string;
};

export function normalizeAppPath(path: string): string {
  const value = String(path || "").trim();
  if (!value) return "/";
  return value.startsWith("/") ? value : `/${value}`;
}

/** URL do portal = basePath + rota interna do iframe (ex.: /controle-mp/conversations/12). */
export function buildPortalEmbeddedPath(portalRoute: string, deepPath: string): string {
  const base = normalizeAppPath(portalRoute).replace(/\/+$/, "") || "/";
  const deep = normalizeAppPath(deepPath);

  if (deep === "/" || portalPathsEquivalent(deep, base)) {
    return base;
  }

  if (deep.startsWith(`${base}/`)) {
    return deep.replace(/\/+$/, "") || base;
  }

  const suffix = deep.startsWith("/") ? deep : `/${deep}`;
  return `${base}${suffix}`.replace(/\/+$/, "") || base;
}

/** Extrai a rota interna do iframe a partir da URL do portal. */
export function extractEmbeddedDeepPath(
  pathname: string,
  appBasePath: string
): string | null {
  const base = normalizeAppPath(appBasePath).replace(/\/+$/, "") || "/";
  const path = normalizeAppPath(pathname).replace(/\/+$/, "") || "/";

  if (portalPathsEquivalent(path, base)) {
    return "/";
  }

  if (!path.startsWith(`${base}/`)) {
    return null;
  }

  const suffix = path.slice(base.length) || "/";
  return normalizeAppPath(suffix);
}

/** Compara rotas tolerando _ vs - (legado controle_mp vs controle-mp). */
export function portalPathsEquivalent(a: string, b: string): boolean {
  const left = normalizeAppPath(a).replace(/\/+$/, "") || "/";
  const right = normalizeAppPath(b).replace(/\/+$/, "") || "/";
  if (left === right) return true;
  if (left.replace(/_/g, "-") === right.replace(/_/g, "-")) return true;
  return (
    left.startsWith(`${right}/`) ||
    right.startsWith(`${left}/`) ||
    left.replace(/_/g, "-").startsWith(`${right.replace(/_/g, "-")}/`)
  );
}

export function portalPathMatchesAppBase(pathname: string, appBasePath: string): boolean {
  return portalPathsEquivalent(pathname, appBasePath);
}

/**
 * Resolve action.target para o basePath registrado no portal (Admin → Apps).
 */
export function resolvePortalRoute(
  target: string,
  registeredBasePaths: string[] = []
): string {
  const normalized = normalizeAppPath(target);
  const match = registeredBasePaths.find((base) =>
    portalPathsEquivalent(normalized, base)
  );
  return match ? normalizeAppPath(match) : normalized;
}

export function isEmbeddedDeepLinkNotification(
  metadata: Record<string, unknown> | null | undefined,
  actionType?: string | null
): metadata is EmbeddedAppNotificationMetadata & { deepPath: string } {
  if (actionType && actionType !== "portal_route") {
    return false;
  }
  const deepPath = metadata?.deepPath;
  return typeof deepPath === "string" && deepPath.trim().length > 0;
}

export function stashEmbeddedDeepLink(payload: EmbeddedPendingNavigate) {
  const item: EmbeddedPendingNavigate = {
    portalRoute: resolvePortalRoute(payload.portalRoute),
    deepPath: normalizeAppPath(payload.deepPath),
    source: payload.source,
  };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(item));
}

function parseStoredPending(raw: string): EmbeddedPendingNavigate | null {
  try {
    const parsed = JSON.parse(raw) as EmbeddedPendingNavigate;
    if (!parsed?.deepPath) return null;
    return {
      portalRoute: normalizeAppPath(parsed.portalRoute || ""),
      deepPath: normalizeAppPath(parsed.deepPath),
      source: parsed.source,
    };
  } catch {
    return null;
  }
}

/** Lê o deep link pendente sem remover (para retentar até o iframe estar pronto). */
export function peekEmbeddedDeepLink(): EmbeddedPendingNavigate | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (raw) {
    const parsed = parseStoredPending(raw);
    if (parsed) return parsed;
  }

  const legacy = sessionStorage.getItem(LEGACY_CONTROLE_MP_KEY);
  if (legacy) {
    return {
      portalRoute: "/controle-mp",
      deepPath: normalizeAppPath(legacy),
      source: "controle_mp",
    };
  }

  return null;
}

export function clearEmbeddedDeepLink() {
  sessionStorage.removeItem(STORAGE_KEY);
  sessionStorage.removeItem(LEGACY_CONTROLE_MP_KEY);
}

export function consumeEmbeddedDeepLink(): EmbeddedPendingNavigate | null {
  const pending = peekEmbeddedDeepLink();
  if (!pending) return null;
  clearEmbeddedDeepLink();
  return pending;
}

export function dispatchEmbeddedNotificationNavigate(detail: EmbeddedPendingNavigate) {
  window.dispatchEvent(
    new CustomEvent("DELPI_NOTIFICATION_NAVIGATE", {
      detail: {
        portalRoute: resolvePortalRoute(detail.portalRoute),
        deepPath: normalizeAppPath(detail.deepPath),
        source: detail.source,
      },
    })
  );
}

export function pendingMatchesCurrentApp(
  pending: EmbeddedPendingNavigate,
  appBasePath: string
): boolean {
  if (!pending.portalRoute) {
    return true;
  }
  return portalPathsEquivalent(pending.portalRoute, appBasePath);
}
