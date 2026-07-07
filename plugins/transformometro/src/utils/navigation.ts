import { normalizeTransformometroPath } from "./routeParser";

export const TRANSFORMOMETRO_WORKSPACE_HASH_EVENT = "transformometro:workspace-hash";

function splitPathAndHash(path: string): { pathname: string; hash: string } {
  const hashIndex = path.indexOf("#");
  if (hashIndex === -1) {
    return { pathname: normalizeTransformometroPath(path), hash: "" };
  }
  return {
    pathname: normalizeTransformometroPath(path.slice(0, hashIndex)),
    hash: path.slice(hashIndex),
  };
}

export function notifyWorkspaceHashChange() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event("hashchange"));
  window.dispatchEvent(new Event(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT));
}

export function navigateTransformometro(path: string) {
  if (typeof window === "undefined") return;

  const { pathname: targetPath, hash: targetHash } = splitPathAndHash(path);
  const currentPath = window.location.pathname;
  const currentHash = window.location.hash;

  if (currentPath === targetPath && currentHash === targetHash) {
    return;
  }

  const nextUrl = `${targetPath}${targetHash}`;

  if (currentPath === targetPath) {
    window.history.pushState(null, "", nextUrl);
    notifyWorkspaceHashChange();
    return;
  }

  window.history.pushState(null, "", nextUrl);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
