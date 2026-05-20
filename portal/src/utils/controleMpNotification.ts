/**
 * @deprecated Importe de `embeddedAppNotification.ts`. Mantido para compatibilidade.
 */
export type { EmbeddedAppNotificationMetadata as ControleMpNotificationMetadata } from "./embeddedAppNotification";

export {
  portalPathMatchesAppBase,
  dispatchEmbeddedNotificationNavigate as dispatchControleMpNotificationNavigate,
  stashEmbeddedDeepLink as stashControleMpDeepPath,
  consumeEmbeddedDeepLink as consumeControleMpDeepPath,
  resolvePortalRoute as normalizeControleMpPortalRoute,
} from "./embeddedAppNotification";

import { isEmbeddedDeepLinkNotification } from "./embeddedAppNotification";

export function isControleMpNotification(
  metadata: Record<string, unknown> | null | undefined
): boolean {
  return (
    isEmbeddedDeepLinkNotification(metadata) && metadata?.source === "controle_mp"
  );
}
