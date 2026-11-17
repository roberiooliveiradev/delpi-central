import { useEffect } from "react";

/**
 * Aviso nativo de saída enquanto `active` (há respostas não enviadas).
 * Registra `beforeunload`; remove ao desativar ou desmontar.
 */
export function useUnsavedChangesWarning(active: boolean): void {
  useEffect(() => {
    if (!active) return;
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [active]);
}
