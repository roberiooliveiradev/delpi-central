/**
 * Resolve `createPortal` sob Module Federation.
 *
 * Prioridade: global semeado pelo host (`__DELPI_MF_REACT_DOM__`) → named → default.
 * Nunca lança no import do módulo — a página pública de assinatura não pode
 * white-screen se o share estiver incompleto.
 */
import type { ReactNode, ReactPortal } from "react";

/** Espelha `DELPI_MF_REACT_DOM_GLOBAL` em plugins/vite/federationReactProxyFix.ts */
const DELPI_MF_REACT_DOM_GLOBAL = "__DELPI_MF_REACT_DOM__";

type CreatePortalFn = (
  children: ReactNode,
  container: Element | DocumentFragment,
  key?: string | null,
) => ReactPortal;

function readCreatePortal(mod: unknown): CreatePortalFn | null {
  if (!mod || typeof mod !== "object") return null;
  const record = mod as {
    createPortal?: unknown;
    default?: { createPortal?: unknown; default?: { createPortal?: unknown } };
  };
  const candidates = [
    record.createPortal,
    record.default?.createPortal,
    record.default?.default?.createPortal,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === "function") {
      return candidate as CreatePortalFn;
    }
  }
  return null;
}

/** Resolve ou `null` — não lança. */
export function tryResolveCreatePortal(reactDomModule?: unknown): CreatePortalFn | null {
  const g = globalThis as Record<string, unknown>;
  return (
    readCreatePortal(g[DELPI_MF_REACT_DOM_GLOBAL]) ??
    readCreatePortal(reactDomModule) ??
    null
  );
}

/**
 * @throws se createPortal indisponível (só use quando o portal for obrigatório).
 */
export function resolveCreatePortal(reactDomModule?: unknown): CreatePortalFn {
  const resolved = tryResolveCreatePortal(reactDomModule);
  if (resolved) return resolved;
  throw new Error(
    "react-dom createPortal indisponível no share MF (default/named). Rebuild plugin-ui + host com federationReactProxyFix ≥ v11.",
  );
}
