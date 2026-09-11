import type { FirmwareListItem } from "../api/productionPulseApi";
import { isPublishedFirmware } from "./hubOtaKpis";
import { latestPublishedFirmwareForFamily } from "./latestPublishedFirmware";

export type FirmwareVersionRoleLabel =
  | "latest"
  | "installed"
  | "selected"
  | "published"
  | "draft"
  | "archived";

/** Canonical short PT labels for version rows (no ambiguous «atual»). */
export function firmwareVersionRoleLabelPt(role: FirmwareVersionRoleLabel): string {
  switch (role) {
    case "latest":
      return "Mais recente";
    case "installed":
      return "Instalada";
    case "selected":
      return "Selecionada";
    case "published":
      return "Publicada";
    case "draft":
      return "Rascunho";
    case "archived":
      return "Arquivada";
  }
}

export function resolveFirmwareVersionRowRoles(args: {
  item: FirmwareListItem;
  familyItems: FirmwareListItem[];
  installedVersion?: string | null;
  selectedId?: string | null;
}): FirmwareVersionRoleLabel[] {
  const { item, familyItems, installedVersion, selectedId } = args;
  const roles: FirmwareVersionRoleLabel[] = [];
  const latest = latestPublishedFirmwareForFamily(familyItems, item.firmwareKey);
  if (latest && latest.id === item.id) roles.push("latest");
  if (installedVersion && item.version === installedVersion) roles.push("installed");
  if (selectedId && item.id === selectedId) roles.push("selected");
  if (item.archivedAt || item.lifecycle === "archived") {
    roles.push("archived");
  } else if (item.lifecycle === "draft" || !isPublishedFirmware(item)) {
    roles.push("draft");
  } else if (!roles.includes("latest")) {
    roles.push("published");
  }
  return roles;
}

export function formatFirmwareVersionMenuLabel(
  item: FirmwareListItem,
  roles: FirmwareVersionRoleLabel[],
): string {
  const roleText = roles
    .filter((role) => role !== "selected")
    .map(firmwareVersionRoleLabelPt)
    .join(" · ");
  return roleText ? `v${item.version} · ${roleText}` : `v${item.version}`;
}
