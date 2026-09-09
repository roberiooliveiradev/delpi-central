import type { FirmwareListItem } from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";

export type FirmwareLinkEdgeKind = "explicit" | "inherited";

export type FirmwareLinkGraphNode = {
  id: string;
  kind: "firmware" | "device";
  label: string;
  subtitle?: string;
  firmwareKey?: string;
  deviceId?: string;
  latestVersion?: string | null;
  linkedCount?: number;
  installedFirmwareVersion?: string | null;
  ipAddress?: string | null;
  position: { x: number; y: number };
};

export type FirmwareLinkGraphEdge = {
  id: string;
  source: string;
  target: string;
  kind: FirmwareLinkEdgeKind;
};

export type FirmwareFamilyNode = {
  firmwareKey: string;
  driverKey: string;
  displayName: string;
  latestVersion: string | null;
  linkedCount: number;
};

/** Ordem canônica de release: publishedAt vence; sem data, versão semântica. */
export type FirmwareReleaseRef = Pick<FirmwareListItem, "version" | "publishedAt">;

export function isNewerFirmwareRelease(
  candidate: FirmwareReleaseRef,
  current: FirmwareReleaseRef,
): boolean {
  if (candidate.publishedAt && current.publishedAt) {
    return candidate.publishedAt > current.publishedAt;
  }
  if (candidate.publishedAt && !current.publishedAt) return true;
  if (!candidate.publishedAt && current.publishedAt) return false;
  return candidate.version.localeCompare(current.version, undefined, { numeric: true }) > 0;
}

export function uniqueFirmwareFamilies(
  items: FirmwareListItem[],
  devices: DeviceListItem[] = [],
): FirmwareFamilyNode[] {
  const byKey = new Map<string, { family: FirmwareFamilyNode; source: FirmwareListItem }>();
  for (const item of items) {
    if (item.archivedAt) continue;
    const prev = byKey.get(item.firmwareKey);
    if (!prev) {
      byKey.set(item.firmwareKey, {
        source: item,
        family: {
          firmwareKey: item.firmwareKey,
          driverKey: item.driverKey,
          displayName: item.displayName || item.firmwareKey,
          latestVersion: item.version,
          linkedCount: 0,
        },
      });
      continue;
    }
    if (!isNewerFirmwareRelease(item, prev.source)) {
      continue;
    }
    byKey.set(item.firmwareKey, {
      source: item,
      family: {
        firmwareKey: item.firmwareKey,
        driverKey: item.driverKey,
        displayName: item.displayName || prev.family.displayName,
        latestVersion: item.version,
        linkedCount: 0,
      },
    });
  }

  const families = [...byKey.values()].map((entry) => entry.family);
  for (const family of families) {
    family.linkedCount = devices.filter(
      (device) => explicitFirmwareKey(device) === family.firmwareKey,
    ).length;
  }
  return families.sort((a, b) => a.firmwareKey.localeCompare(b.firmwareKey));
}

/** Effective assigned family for canvas solid edge (explicit column only). */
export function explicitFirmwareKey(device: DeviceListItem): string | null {
  const assigned = device.assignedFirmwareKey;
  if (assigned && String(assigned).trim()) return String(assigned).trim();
  return null;
}

/**
 * Build graph: firmware nodes left, devices right.
 * At most one solid (explicit) edge per device; inherited dashed when
 * assignedFirmwareKey is null and driverKey matches a family.
 */
export function buildFirmwareLinkGraph(input: {
  families: FirmwareFamilyNode[];
  devices: DeviceListItem[];
}): { nodes: FirmwareLinkGraphNode[]; edges: FirmwareLinkGraphEdge[] } {
  const nodes: FirmwareLinkGraphNode[] = [];
  const edges: FirmwareLinkGraphEdge[] = [];
  const familyKeys = new Set(input.families.map((f) => f.firmwareKey));

  input.families.forEach((family, index) => {
    const versionLabel = family.latestVersion ? `v${family.latestVersion}` : "sem versão";
    nodes.push({
      id: `fw:${family.firmwareKey}`,
      kind: "firmware",
      label: family.displayName,
      subtitle: `${family.firmwareKey} · ${versionLabel} · ${family.linkedCount} ligado(s)`,
      firmwareKey: family.firmwareKey,
      latestVersion: family.latestVersion,
      linkedCount: family.linkedCount,
      position: { x: 40, y: 40 + index * 130 },
    });
  });

  input.devices.forEach((device, index) => {
    const nodeId = `dev:${device.id}`;
    const installed = device.installedFirmwareVersion?.trim() || "—";
    nodes.push({
      id: nodeId,
      kind: "device",
      label: device.name,
      subtitle: `${device.ipAddress} · ${installed}`,
      deviceId: device.id,
      ipAddress: device.ipAddress,
      installedFirmwareVersion: device.installedFirmwareVersion ?? null,
      position: { x: 420, y: 40 + index * 110 },
    });

    const explicit = explicitFirmwareKey(device);
    if (explicit && familyKeys.has(explicit)) {
      edges.push({
        id: `e-explicit-${device.id}`,
        source: `fw:${explicit}`,
        target: nodeId,
        kind: "explicit",
      });
      return;
    }

    if (!explicit && familyKeys.has(device.driverKey)) {
      edges.push({
        id: `e-inherited-${device.id}`,
        source: `fw:${device.driverKey}`,
        target: nodeId,
        kind: "inherited",
      });
    }
  });

  return { nodes, edges };
}

/** Ensure at most one solid edge per device target (replace semantics). */
export function replaceExplicitEdge(
  edges: FirmwareLinkGraphEdge[],
  params: { deviceNodeId: string; firmwareNodeId: string },
): FirmwareLinkGraphEdge[] {
  const { deviceNodeId, firmwareNodeId } = params;
  const deviceId = deviceNodeId.replace(/^dev:/, "");
  const next = edges.filter(
    (edge) => !(edge.target === deviceNodeId && edge.kind === "explicit"),
  );
  next.push({
    id: `e-explicit-${deviceId}`,
    source: firmwareNodeId,
    target: deviceNodeId,
    kind: "explicit",
  });
  return next.filter(
    (edge) => !(edge.target === deviceNodeId && edge.kind === "inherited"),
  );
}
