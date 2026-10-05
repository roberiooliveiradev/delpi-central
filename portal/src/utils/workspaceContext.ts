/**
 * Workspace context registry — host side of the provider-neutral
 * contract (ledger §6.130). Embedded apps publish a bounded view of
 * what the user is looking at via `delpi:workspace-context`
 * CustomEvents on `window`; the Portal keeps the latest published
 * context per host app and hands it to DÉLIA as an untrusted hint.
 *
 * This context is NEVER authority: it carries only host app identity,
 * route/surface hints, and entity references. It never authorizes
 * anything — the backend resolves and enforces.
 *
 * Stale-context safety: the registry is cleared whenever the Portal
 * route changes, so a context published on screen A can never bleed
 * into screen B.
 */

export const DELPI_WORKSPACE_CONTEXT_EVENT = "delpi:workspace-context";

export type DeliaWorkspaceEntityRef = {
  entity_type: string;
  entity_id: string;
  source_system: string;
  label?: string;
};

export type DeliaWorkspaceContext = {
  host_app_id: string;
  route?: string;
  view_ref?: string;
  selected_entity_ref?: DeliaWorkspaceEntityRef;
  entity_refs?: DeliaWorkspaceEntityRef[];
};

const MAX_FIELD_CHARS = 200;
const MAX_REFS = 4;

let latest: DeliaWorkspaceContext | null = null;
let initialized = false;

function isEntityRef(value: unknown): value is DeliaWorkspaceEntityRef {
  if (!value || typeof value !== "object") return false;
  const r = value as Record<string, unknown>;
  return (
    typeof r.entity_type === "string" &&
    r.entity_type.length <= MAX_FIELD_CHARS &&
    typeof r.entity_id === "string" &&
    r.entity_id.length <= MAX_FIELD_CHARS &&
    typeof r.source_system === "string" &&
    r.source_system.length <= MAX_FIELD_CHARS &&
    (r.label === undefined ||
      (typeof r.label === "string" && r.label.length <= MAX_FIELD_CHARS))
  );
}

function isContext(value: unknown): value is DeliaWorkspaceContext {
  if (!value || typeof value !== "object") return false;
  const r = value as Record<string, unknown>;
  if (
    typeof r.host_app_id !== "string" ||
    !r.host_app_id.trim() ||
    r.host_app_id.length > MAX_FIELD_CHARS
  ) {
    return false;
  }
  if (r.selected_entity_ref !== undefined && !isEntityRef(r.selected_entity_ref)) {
    return false;
  }
  if (r.entity_refs !== undefined) {
    if (!Array.isArray(r.entity_refs) || r.entity_refs.length > MAX_REFS) {
      return false;
    }
    if (!r.entity_refs.every(isEntityRef)) return false;
  }
  for (const key of ["route", "view_ref"] as const) {
    const v = r[key];
    if (v !== undefined && (typeof v !== "string" || v.length > MAX_FIELD_CHARS)) {
      return false;
    }
  }
  return true;
}

/** Install the workspace-context listener once (host runtime). */
export function initWorkspaceContextListener(): void {
  if (initialized || typeof window === "undefined") return;
  initialized = true;
  window.addEventListener(DELPI_WORKSPACE_CONTEXT_EVENT, (event) => {
    const detail = (event as CustomEvent).detail;
    if (!isContext(detail)) return;
    latest = detail;
  });
}

/** Latest published context — or null. Never mutates the publisher. */
export function getWorkspaceContext(): DeliaWorkspaceContext | null {
  return latest ? { ...latest } : null;
}

/** Clear the registry — called on every Portal route change. */
export function clearWorkspaceContext(): void {
  latest = null;
}
