const STORAGE_KEY = "transformometro-client-id";

export function getTransformometroClientId(): string {
  if (typeof window === "undefined") {
    return "server";
  }

  const existing = window.sessionStorage.getItem(STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const created =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `client-${Date.now()}-${Math.random().toString(36).slice(2)}`;

  window.sessionStorage.setItem(STORAGE_KEY, created);
  return created;
}
