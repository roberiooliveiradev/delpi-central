/** Admin hub UI state — single source for map layers (no boolean explosion). */

export type AdminEntityRef =
  | { type: "device"; id: string }
  | { type: "firmware"; id: string }
  | { type: "job"; id: string }
  | { type: "driver"; id: string };

export type AdminHubPanel = "devices" | "firmwares" | "jobs" | "fleet-health" | "drivers";

/** Canonical modal layer keys (URL `modal=`). */
export type AdminHubModal =
  | "device-create"
  | "device-edit"
  | "device-detail"
  | "firmware-create"
  | "firmware-version"
  | "firmware-detail"
  | "driver-create"
  | "driver-detail"
  | "ota-schedule"
  | "job-detail";

/**
 * @deprecated Prefer `AdminHubModal`. Kept for typed alias of legacy `drawer=` values.
 * `firmware-edit` maps to `firmware-detail`.
 */
export type AdminHubDrawer =
  | "device-create"
  | "device-edit"
  | "firmware-create"
  | "firmware-version"
  | "firmware-edit"
  | "ota-schedule"
  | "ota-confirm";

export type AdminHubConfirmKind =
  | "disable-device"
  | "archive-firmware"
  | "archive-driver"
  | "cancel-job"
  | "unlink";

export type AdminHubOpenLayer =
  | "none"
  | "summary"
  | "menu"
  | "inspector"
  | "panel"
  | "modal"
  | "confirm";

export type AdminHubUiState = {
  selectedEntity: AdminEntityRef | null;
  openLayer: AdminHubOpenLayer;
  panel: AdminHubPanel | null;
  modal: AdminHubModal | null;
  confirm: { kind: AdminHubConfirmKind; id: string } | null;
  filters: { q: string; status: string };
  popoverAnchorId: string | null;
};

export const INITIAL_ADMIN_HUB_UI: AdminHubUiState = {
  selectedEntity: null,
  openLayer: "none",
  panel: null,
  modal: null,
  confirm: null,
  filters: { q: "", status: "" },
  popoverAnchorId: null,
};

const ADMIN_HUB_MODALS = new Set<AdminHubModal>([
  "device-create",
  "device-edit",
  "device-detail",
  "firmware-create",
  "firmware-version",
  "firmware-detail",
  "driver-create",
  "driver-detail",
  "ota-schedule",
  "job-detail",
]);

/** Legacy `drawer=` → canonical `modal=`. */
const LEGACY_DRAWER_TO_MODAL: Record<string, AdminHubModal> = {
  "device-create": "device-create",
  "device-edit": "device-edit",
  "firmware-create": "firmware-create",
  "firmware-version": "firmware-version",
  "firmware-edit": "firmware-detail",
  "ota-schedule": "ota-schedule",
};

export function parseAdminEntity(raw: string | null | undefined): AdminEntityRef | null {
  if (!raw?.trim()) return null;
  const [type, ...rest] = raw.split(":");
  const id = rest.join(":").trim();
  if (!id) return null;
  if (type === "device" || type === "firmware" || type === "job" || type === "driver") {
    return { type, id };
  }
  return null;
}

export function formatAdminEntity(entity: AdminEntityRef | null | undefined): string | null {
  if (!entity) return null;
  return `${entity.type}:${entity.id}`;
}

export function parseAdminPanel(raw: string | null | undefined): AdminHubPanel | null {
  if (
    raw === "devices" ||
    raw === "firmwares" ||
    raw === "jobs" ||
    raw === "fleet-health" ||
    raw === "drivers"
  ) {
    return raw;
  }
  return null;
}

export function parseAdminModal(raw: string | null | undefined): AdminHubModal | null {
  if (!raw?.trim()) return null;
  if (ADMIN_HUB_MODALS.has(raw as AdminHubModal)) {
    return raw as AdminHubModal;
  }
  return LEGACY_DRAWER_TO_MODAL[raw] ?? null;
}

/**
 * @deprecated Prefer `parseAdminModal`. Accepts legacy drawer query values.
 */
export function parseAdminDrawer(raw: string | null | undefined): AdminHubModal | null {
  return parseAdminModal(raw);
}

export function hubFocusToPanel(
  focus: string | null | undefined,
): AdminHubPanel | null {
  if (focus === "catalog") return "firmwares";
  if (focus === "jobs") return "jobs";
  return null;
}

/** Resolve modal from URL: prefer `modal=`, fall back to legacy `drawer=`. */
export function resolveAdminModalFromQuery(opts: {
  modal?: string | null;
  drawer?: string | null;
}): AdminHubModal | null {
  return parseAdminModal(opts.modal) ?? parseAdminModal(opts.drawer);
}
