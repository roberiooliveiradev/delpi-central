/** Session-tab guard so a failed OAuth return does not redirect-loop. */

export const HELPDESK_GLPI_AUTO_LINK_KEY = "helpdesk.glpiAutoLink";

function sessionStore(): Storage | null {
  try {
    if (typeof sessionStorage === "undefined") return null;
    return sessionStorage;
  } catch {
    return null;
  }
}

export function shouldAutoStartGlpiLink(storage: Storage | null = sessionStore()): boolean {
  if (!storage) return true;
  try {
    return storage.getItem(HELPDESK_GLPI_AUTO_LINK_KEY) !== "1";
  } catch {
    return true;
  }
}

export function markGlpiAutoLinkAttempted(storage: Storage | null = sessionStore()): void {
  if (!storage) return;
  try {
    storage.setItem(HELPDESK_GLPI_AUTO_LINK_KEY, "1");
  } catch {
    /* private mode */
  }
}

export function clearGlpiAutoLinkAttempt(storage: Storage | null = sessionStore()): void {
  if (!storage) return;
  try {
    storage.removeItem(HELPDESK_GLPI_AUTO_LINK_KEY);
  } catch {
    /* private mode */
  }
}
