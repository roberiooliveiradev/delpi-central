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

export function consumeEmbeddedDeepLink(): EmbeddedPendingNavigate | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (raw) {
    sessionStorage.removeItem(STORAGE_KEY);
    try {
      const parsed = JSON.parse(raw) as EmbeddedPendingNavigate;
      if (parsed?.deepPath) {
        return {
          portalRoute: normalizeAppPath(parsed.portalRoute || ""),
          deepPath: normalizeAppPath(parsed.deepPath),
          source: parsed.source,
        };
      }
    } catch {
      // ignore JSON inválido
    }
  }

  const legacy = sessionStorage.getItem(LEGACY_CONTROLE_MP_KEY);
  if (legacy) {
    sessionStorage.removeItem(LEGACY_CONTROLE_MP_KEY);
    return {
      portalRoute: "/controle-mp",
      deepPath: normalizeAppPath(legacy),
      source: "controle_mp",
    };
  }

  return null;
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
