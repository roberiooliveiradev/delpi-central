import {
  isStaleModuleLoadError,
  requestAssetRecover,
} from "./assetRecover";

/**
 * Envolve `import()` de chunk lazy: em falha de deploy (hash antigo), redireciona
 * uma vez com `?_recover=` para o entry revalidar HTML/JS (ver `cacheBustEntryPlugin`).
 */
export function lazyImportWithRecover<T>(factory: () => Promise<T>): () => Promise<T> {
  return () =>
    factory().catch((error: unknown) => {
      const message = error instanceof Error ? error.message : String(error ?? "");
      if (!isStaleModuleLoadError(message)) {
        throw error;
      }
      if (requestAssetRecover()) {
        return new Promise<T>(() => {
          /* navegação em curso */
        });
      }
      throw error;
    });
}


