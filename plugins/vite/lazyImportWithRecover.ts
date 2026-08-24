const CHUNK_LOAD_ERROR =
  /Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module/i;

export type LazyImportRecoverOptions = {
  sessionKey?: string;
};

/**
 * Envolve `import()` de chunk lazy: em falha de deploy (hash antigo), redireciona
 * uma vez com `?_recover=` para o entry revalidar HTML/JS (ver `cacheBustEntryPlugin`).
 */
export function lazyImportWithRecover<T>(
  factory: () => Promise<T>,
  options?: LazyImportRecoverOptions,
): () => Promise<T> {
  const sessionKey = options?.sessionKey ?? "delpi-public-hub-chunk-recover";

  return () =>
    factory().catch((error: unknown) => {
      const message = error instanceof Error ? error.message : String(error ?? "");
      if (!CHUNK_LOAD_ERROR.test(message)) {
        throw error;
      }
      try {
        if (sessionStorage.getItem(sessionKey)) {
          throw error;
        }
        sessionStorage.setItem(sessionKey, "1");
      } catch {
        throw error;
      }
      const url = new URL(location.href);
      url.searchParams.set("_recover", String(Date.now()));
      location.replace(url.toString());
      return new Promise<T>(() => {
        /* navegação em curso */
      });
    });
}
