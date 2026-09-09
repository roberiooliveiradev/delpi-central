/** Admin hub UI state — single source for map layers (no boolean explosion). */

export type AdminEntityRef =
  | { type: "device"; id: string }
  | { type: "firmware"; id: string }
  | { type: "job"; id: string };

export type AdminHubPanel = "devices" | "firmwares" | "jobs" | "fleet-health";

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
  | "cancel-job"
  | "unlink";

export type AdminHubOpenLayer =
  | "none"
  | "summary"
  | "menu"
  | "inspector"
  | "panel"
  | "drawer"
  | "confirm";

export type AdminHubUiState = {
  selectedEntity: AdminEntityRef | null;
  openLayer: AdminHubOpenLayer;
  panel: AdminHubPanel | null;
  drawer: AdminHubDrawer | null;
  confirm: { kind: AdminHubConfirmKind; id: string } | null;
  filters: { q: string; status: string };
  popoverAnchorId: string | null;
};

export const INITIAL_ADMIN_HUB_UI: AdminHubUiState = {
  selectedEntity: null,
  openLayer: "none",
  panel: null,
  drawer: null,
  confirm: null,
  filters: { q: "", status: "" },
  popoverAnchorId: null,
};

export function parseAdminEntity(raw: string | null | undefined): AdminEntityRef | null {
  if (!raw?.trim()) return null;
  const [type, ...rest] = raw.split(":");
  const id = rest.join(":").trim();
  if (!id) return null;
  if (type === "device" || type === "firmware" || type === "job") {
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
    raw === "fleet-health"
  ) {
    return raw;
  }
  return null;
}

export function parseAdminDrawer(raw: string | null | undefined): AdminHubDrawer | null {
  if (
    raw === "device-create" ||
    raw === "device-edit" ||
    raw === "firmware-create" ||
    raw === "firmware-version" ||
    raw === "firmware-edit" ||
    raw === "ota-schedule" ||
    raw === "ota-confirm"
  ) {
    return raw;
  }
  return null;
}

export function hubFocusToPanel(
  focus: string | null | undefined,
): AdminHubPanel | null {
  if (focus === "catalog") return "firmwares";
  if (focus === "jobs") return "jobs";
  return null;
}
