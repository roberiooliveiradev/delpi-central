import { useEffect, useRef } from "react";
import { useSyncExternalStore } from "react";

import { TRANSFORMOMETRO_WORKSPACE_HASH_EVENT } from "../../utils/navigation";
import { parseTransformometroPath } from "../../utils/routeParser";
import { resolveTeoPortalContext } from "./teoPortalContext";
import {
  readTeoWorkspaceSelection,
  subscribeTeoWorkspaceSelection,
} from "./teoWorkspaceSelection";
import {
  buildWorkspaceContextPayload,
  publishWorkspaceContext,
  unpublishWorkspaceContext,
  workspaceContextSignature,
} from "./workspaceContextPublisher";

function subscribeNavigation(onChange: () => void) {
  window.addEventListener("hashchange", onChange);
  window.addEventListener("popstate", onChange);
  window.addEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onChange);
  return () => {
    window.removeEventListener("hashchange", onChange);
    window.removeEventListener("popstate", onChange);
    window.removeEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onChange);
  };
}

function readHash(): string {
  return window.location.hash;
}

function readFocused(): boolean {
  return document.visibilityState === "visible" && document.hasFocus();
}

function subscribeFocus(onChange: () => void) {
  window.addEventListener("focus", onChange);
  window.addEventListener("blur", onChange);
  document.addEventListener("visibilitychange", onChange);
  return () => {
    window.removeEventListener("focus", onChange);
    window.removeEventListener("blur", onChange);
    document.removeEventListener("visibilitychange", onChange);
  };
}

/**
 * Publica o workspace_context_v1 no Core em eventos semânticos:
 * mudança de rota/hash/seleção (nova ref ou área) e foco/visibilidade
 * (evidência de foreground). Dedupe por assinatura impede flood HTTP.
 * Falha de publicação nunca quebra o Portal — erro é engolido após
 * log bounded; o contexto apenas fica indisponível para o TÉO.
 * No unmount/pagehide o contexto desta aba é removido (DELETE keepalive).
 */
export function useWorkspaceContextPublisher(options: {
  getAccessToken?: () => string | undefined;
  pathname: string;
}): void {
  const { getAccessToken, pathname } = options;
  const hash = useSyncExternalStore(subscribeNavigation, readHash, () => "");
  const selection = useSyncExternalStore(
    subscribeTeoWorkspaceSelection,
    readTeoWorkspaceSelection,
    () => null,
  );
  const focused = useSyncExternalStore(subscribeFocus, readFocused, () => false);

  const lastSignatureRef = useRef<string | null>(null);
  const getAccessTokenRef = useRef(getAccessToken);
  getAccessTokenRef.current = getAccessToken;

  useEffect(() => {
    const route = parseTransformometroPath(pathname);
    const context = resolveTeoPortalContext(pathname, hash, selection);
    const payload = buildWorkspaceContextPayload(context, route.view, focused);
    const signature = workspaceContextSignature(payload);
    if (signature === lastSignatureRef.current) return;
    lastSignatureRef.current = signature;
    publishWorkspaceContext(payload, getAccessTokenRef.current).catch(
      (error: unknown) => {
        // Conveniência contextual — nunca quebrar o Portal por isso.
        console.debug("workspace-context publish failed", error);
      },
    );
  }, [pathname, hash, selection, focused]);

  useEffect(() => {
    const onPageHide = () => unpublishWorkspaceContext(getAccessTokenRef.current);
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      unpublishWorkspaceContext(getAccessTokenRef.current);
    };
  }, []);
}
