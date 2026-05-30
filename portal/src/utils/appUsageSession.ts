/** Alinhado ao APP_USAGE_TTL_SECONDS padrão (90s) da Core API. */
export const EXTERNAL_USAGE_GRACE_MS = 90_000;

export type ActiveAppUsage = {
  appId: string;
  routePath: string;
  external?: boolean;
  openedAt?: number;
  /** Usuário saiu do portal — provavelmente está na aba externa. */
  leftPortal?: boolean;
};

export function shouldPingExternalUsage(active: ActiveAppUsage): boolean {
  if (!active.external) return true;

  const elapsed = Date.now() - (active.openedAt ?? 0);

  if (document.visibilityState === "hidden") {
    return true;
  }

  // Portal visível: renova só na janela de graça após o clique (antes de trocar de aba).
  return !active.leftPortal && elapsed <= EXTERNAL_USAGE_GRACE_MS;
}

export function shouldCloseExternalUsage(active: ActiveAppUsage): boolean {
  if (!active.external) return false;

  const elapsed = Date.now() - (active.openedAt ?? 0);

  if (active.leftPortal && document.visibilityState === "visible") {
    return true;
  }

  return !active.leftPortal && elapsed > EXTERNAL_USAGE_GRACE_MS;
}
