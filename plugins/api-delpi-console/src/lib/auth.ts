let accessTokenGetter: (() => string | undefined) | null = null;

export function configureAuth(getAccessToken?: () => string | undefined) {
  accessTokenGetter = getAccessToken ?? null;
}

export function getAuthToken(): string | null {
  const fromPortal = accessTokenGetter?.();
  if (fromPortal) return fromPortal;

  if (typeof window === "undefined") return null;

  return (
    localStorage.getItem("delpi_token") ??
    localStorage.getItem("token") ??
    sessionStorage.getItem("delpi_token") ??
    sessionStorage.getItem("token")
  );
}

export function getMessageTargetOrigin(): string {
  return window.location.origin;
}
