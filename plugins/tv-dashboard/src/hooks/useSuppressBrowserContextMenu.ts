import { useEffect } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";

/**
 * True quando o alvo do clique direito está no MFE TV Dashboard
 * (root `.dashboard-tv-dashboard` ou portal com a mesma classe de escopo).
 */
export function shouldSuppressBrowserContextMenu(
  target: EventTarget | null,
  rootClass: string = TV_DASHBOARD_ROOT_CLASS,
): boolean {
  if (!(target instanceof Element)) return false;
  return Boolean(target.closest(`.${rootClass}`));
}

/**
 * Desativa o menu de contexto nativo do navegador enquanto o plugin estiver montado.
 * Ao desmontar (sair do MFE), o listener é removido e o menu volta ao normal.
 */
export function useSuppressBrowserContextMenu(enabled = true) {
  useEffect(() => {
    if (!enabled || typeof document === "undefined") return;

    const onContextMenu = (event: Event) => {
      if (!shouldSuppressBrowserContextMenu(event.target)) return;
      event.preventDefault();
    };

    document.addEventListener("contextmenu", onContextMenu, true);
    return () => document.removeEventListener("contextmenu", onContextMenu, true);
  }, [enabled]);
}
