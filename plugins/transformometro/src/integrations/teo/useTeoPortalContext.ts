import { useMemo } from "react";
import { useSyncExternalStore } from "react";

import { TRANSFORMOMETRO_WORKSPACE_HASH_EVENT } from "../../utils/navigation";
import { parseTransformometroPath } from "../../utils/routeParser";
import { resolveWorkspacePanelView } from "../../ui/processes/processWorkspaceNav";
import {
  resolveTeoPortalContext,
  type TeoPortalContext,
} from "./teoPortalContext";
import {
  readTeoWorkspaceSelection,
  subscribeTeoWorkspaceSelection,
  type TeoWorkspaceSelection,
} from "./teoWorkspaceSelection";

function subscribeLocationHash(onStoreChange: () => void) {
  window.addEventListener("hashchange", onStoreChange);
  window.addEventListener("popstate", onStoreChange);
  window.addEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("hashchange", onStoreChange);
    window.removeEventListener("popstate", onStoreChange);
    window.removeEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onStoreChange);
  };
}

function readLocationHash(): string {
  return window.location.hash;
}

export type TeoPortalContextState = {
  context: TeoPortalContext;
  /** View de rota canônica — usada só para rotular a área na UI. */
  view: string;
};

/**
 * Contexto TÉO derivado da navegação atual. Reativo a mudanças de rota
 * (pathname do host) e de hash (seções do workspace) — sem cache e sem
 * fetch de domínio.
 */
export function useTeoPortalContext(pathname: string): TeoPortalContextState {
  const hash = useSyncExternalStore(
    subscribeLocationHash,
    readLocationHash,
    () => "",
  );
  const selection = useSyncExternalStore<TeoWorkspaceSelection | null>(
    subscribeTeoWorkspaceSelection,
    readTeoWorkspaceSelection,
    () => null,
  );

  return useMemo(() => {
    const route = parseTransformometroPath(pathname);
    // View efetiva do painel — usada só para rotular a área na UI.
    const view =
      route.view === "instancia" || route.view === "revisao"
        ? resolveWorkspacePanelView({ view: route.view, hash })
        : route.view;
    return {
      context: resolveTeoPortalContext(pathname, hash, selection),
      view,
    };
  }, [pathname, hash, selection]);
}
