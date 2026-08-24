/** Chave única — entry + chunks lazy do public-hub compartilham a mesma trava de recuperação. */
export const DELPI_PUBLIC_HUB_RECOVER_KEY = "delpi-public-hub-asset-recover";

export const STALE_MODULE_LOAD_ERROR =
  /Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module/i;

export function isStaleModuleLoadError(message: string): boolean {
  return STALE_MODULE_LOAD_ERROR.test(message);
}

export function clearAssetRecoverLock(): void {
  try {
    sessionStorage.removeItem(DELPI_PUBLIC_HUB_RECOVER_KEY);
  } catch {
    /* WebView sem sessionStorage */
  }
}

/**
 * Redireciona uma vez com `?_recover=` para o entry revalidar HTML/JS.
 * `force` limpa a trava (botão «Tentar novamente» na UI).
 */
export function requestAssetRecover(options?: { force?: boolean }): boolean {
  if (options?.force) {
    clearAssetRecoverLock();
    try {
      void fetch(location.href, { cache: "reload" });
    } catch {
      /* WebView sem fetch */
    }
  }
  try {
    if (sessionStorage.getItem(DELPI_PUBLIC_HUB_RECOVER_KEY)) {
      return false;
    }
    sessionStorage.setItem(DELPI_PUBLIC_HUB_RECOVER_KEY, "1");
  } catch {
    return false;
  }
  const url = new URL(location.href);
  url.searchParams.set("_recover", String(Date.now()));
  location.replace(url.toString());
  return true;
}

/** Registra listener global para falhas de `import()` fora do React lazy. */
export function registerStaleModuleRecoverListener(): void {
  if (typeof window === "undefined") return;
  const onRejection = (event: PromiseRejectionEvent) => {
    const reason = event.reason;
    const message = reason instanceof Error ? reason.message : String(reason ?? "");
    if (!isStaleModuleLoadError(message)) return;
    if (requestAssetRecover()) {
      event.preventDefault();
    }
  };
  window.addEventListener("unhandledrejection", onRejection);
}
