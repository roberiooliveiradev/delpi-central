/** Resolve TopBar active item from internal pathname (E20). */

export type MyRequestsTopBarId = "mine" | "work_queue" | "new" | "admin";

const BASE = "/apps/my-requests";

export function resolveTopBarActiveId(pathname: string): MyRequestsTopBarId {
  const normalized = pathname.replace(/\/+$/, "") || BASE;
  if (normalized === `${BASE}/work-queue`) return "work_queue";
  if (normalized === `${BASE}/new` || normalized.startsWith(`${BASE}/new/`)) {
    return "new";
  }
  if (normalized === `${BASE}/admin`) return "admin";
  // /mine, /, /requests/:id → mine (sem origem de fila)
  return "mine";
}
