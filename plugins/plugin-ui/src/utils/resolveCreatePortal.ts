/**
 * Resolve `createPortal` sob Module Federation.
 *
 * O chunk `__federation_shared_react-dom` exporta só `default`. Se o flatten
 * não copiar named exports, `const { createPortal } = await importShared("react-dom")`
 * fica `undefined` → HelpTooltip «X is not a function» (ex.: ao abrir o balão
 * ao sair da tela cheia).
 */
import type { ReactNode, ReactPortal } from "react";

type CreatePortalFn = (
  children: ReactNode,
  container: Element | DocumentFragment,
  key?: string | null,
) => ReactPortal;

export function resolveCreatePortal(reactDomModule: unknown): CreatePortalFn {
  const mod = reactDomModule as {
    createPortal?: unknown;
    default?: { createPortal?: unknown };
  } | null;

  const candidates = [mod?.createPortal, mod?.default?.createPortal];
  for (const candidate of candidates) {
    if (typeof candidate === "function") {
      return candidate as CreatePortalFn;
    }
  }

  throw new Error(
    "react-dom createPortal indisponível no share MF (default/named). Rebuild plugin-ui + host com federationReactProxyFix ≥ v11.",
  );
}
