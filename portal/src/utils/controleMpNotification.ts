// Navegação pós-clique em notificações originadas do Controle MP.

const STORAGE_KEY = "delpi.controle_mp.pending_navigate";

export type ControleMpNotificationMetadata = {
  source?: string;
  deepPath?: string;
  event?: string;
  dedupeKey?: string;
  conversationId?: number;
  messageId?: number;
  requestId?: number;
  requestItemId?: number;
};

export function isControleMpNotification(
  metadata: Record<string, unknown> | null | undefined
): metadata is ControleMpNotificationMetadata {
  return metadata?.source === "controle_mp" && typeof metadata?.deepPath === "string";
}

export function stashControleMpDeepPath(deepPath: string) {
  const normalized = deepPath.startsWith("/") ? deepPath : `/${deepPath}`;
  sessionStorage.setItem(STORAGE_KEY, normalized);
}

export function consumeControleMpDeepPath(): string | null {
  const value = sessionStorage.getItem(STORAGE_KEY);
  if (!value) return null;
  sessionStorage.removeItem(STORAGE_KEY);
  return value;
}

export function dispatchControleMpNotificationNavigate(detail: {
  portalRoute: string;
  deepPath: string;
}) {
  window.dispatchEvent(
    new CustomEvent("DELPI_NOTIFICATION_NAVIGATE", { detail })
  );
}
