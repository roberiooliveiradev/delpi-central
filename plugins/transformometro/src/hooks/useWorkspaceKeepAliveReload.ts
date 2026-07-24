import { useEffect, useRef } from "react";

import { subscribeWorkspaceTreeRefresh } from "../utils/navigation";

type Options = {
  /** Painel montado em keep-alive no workspace. */
  embedded?: boolean;
  /** True quando o painel está visível/ativo. */
  embeddedActive?: boolean;
  /** Recarrega dados do painel (lista, matriz, comparativo…). */
  reload: () => void;
};

/**
 * Keep-alive: ao reativar o painel ou receber tree-refresh (mutação em filho / outra aba),
 * refetcha — evita UI stale até F5 (mesmo padrão da melhoria/revisão).
 */
export function useWorkspaceKeepAliveReload({
  embedded = false,
  embeddedActive = true,
  reload,
}: Options): void {
  const wasEmbeddedActive = useRef(embeddedActive);

  useEffect(() => {
    const becameActive = embedded && embeddedActive && !wasEmbeddedActive.current;
    wasEmbeddedActive.current = embeddedActive;
    if (becameActive) {
      reload();
    }
  }, [embedded, embeddedActive, reload]);

  useEffect(() => {
    return subscribeWorkspaceTreeRefresh(reload);
  }, [reload]);
}
