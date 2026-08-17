/**
 * Decide se um clique em <a> deve virar navigate() do React Router
 * (mesmo app federado/embedded) em vez de reload completo do documento.
 */

export type SameAppAnchorClickInput = {
  defaultPrevented: boolean;
  button: number;
  metaKey: boolean;
  ctrlKey: boolean;
  shiftKey: boolean;
  altKey: boolean;
};

export type SameAppAnchorResolveOptions = {
  appBasePath: string;
  currentOrigin: string;
  currentPathname: string;
  currentSearch: string;
  currentHash: string;
};

function normalizeBasePath(basePath: string): string {
  const withSlash = basePath.startsWith("/") ? basePath : `/${basePath}`;
  return withSlash.replace(/\/+$/, "") || "/";
}

function isModifiedClick(event: SameAppAnchorClickInput): boolean {
  return (
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  );
}

function pathIsWithinApp(pathname: string, appBasePath: string): boolean {
  const base = normalizeBasePath(appBasePath);
  if (base === "/") return true;
  return pathname === base || pathname.startsWith(`${base}/`);
}

/**
 * Retorna o destino (`pathname + search + hash`) para `navigate()`, ou `null`
 * se o clique deve seguir o comportamento nativo do browser.
 */
export function resolveSameAppSpaNavigation(
  event: SameAppAnchorClickInput,
  anchor: Pick<
    HTMLAnchorElement,
    "href" | "target" | "hasAttribute" | "getAttribute"
  >,
  options: SameAppAnchorResolveOptions,
): string | null {
  if (event.defaultPrevented || isModifiedClick(event)) return null;
  if (anchor.hasAttribute("download")) return null;

  const target = (anchor.getAttribute("target") || "").trim();
  if (target && target.toLowerCase() !== "_self") return null;

  let url: URL;
  try {
    url = new URL(anchor.href, options.currentOrigin);
  } catch {
    return null;
  }

  if (url.origin !== options.currentOrigin) return null;
  if (!pathIsWithinApp(url.pathname, options.appBasePath)) return null;

  const next = `${url.pathname}${url.search}${url.hash}`;
  const current = `${options.currentPathname}${options.currentSearch}${options.currentHash}`;
  if (next === current) {
    // Evita reload no-op no mesmo endereço.
    return next;
  }

  return next;
}
