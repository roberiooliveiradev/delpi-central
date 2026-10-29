/** Rotas internas da feature NC sob `/apps/engineering/nonconformities`.
 * Caminho standalone (doc 45) — não aninhado em `/lmps`. */

export const NC_BASE_PATH = "/apps/engineering/nonconformities";

export type NcView =
  | { kind: "list" }
  | { kind: "new" }
  | { kind: "detail"; recordId: string }
  | { kind: "edit"; recordId: string }
  | { kind: "not_found" };

export const NC_PATHS = {
  list: NC_BASE_PATH,
  new: `${NC_BASE_PATH}/new`,
  detail: (recordId: string) =>
    `${NC_BASE_PATH}/${encodeURIComponent(recordId)}`,
  edit: (recordId: string) =>
    `${NC_BASE_PATH}/${encodeURIComponent(recordId)}/edit`,
} as const;

export function resolveNcPath(relativePath: string): NcView {
  const path = relativePath.replace(/^\/+|\/+$/g, "");
  if (path === "" || path === "nonconformities") return { kind: "list" };
  const rest = path.startsWith("nonconformities/")
    ? path.slice("nonconformities/".length)
    : path;
  if (rest === "new") return { kind: "new" };
  const segments = rest.split("/").filter(Boolean);
  if (segments.length === 1 && segments[0]) {
    return { kind: "detail", recordId: decodeURIComponent(segments[0]) };
  }
  if (segments.length === 2 && segments[1] === "edit" && segments[0]) {
    return { kind: "edit", recordId: decodeURIComponent(segments[0]) };
  }
  return { kind: "not_found" };
}

export function navigateNc(path: string, options?: { replace?: boolean }) {
  if (typeof window === "undefined") return;
  if (options?.replace) {
    window.history.replaceState(window.history.state, "", path);
  } else {
    window.history.pushState(window.history.state, "", path);
  }
  window.dispatchEvent(
    new PopStateEvent("popstate", { state: window.history.state }),
  );
}
