import type { FirmwareCatalogItem } from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";

export type FirmwareLinkEdgeKind = "explicit" | "inherited";

export type FirmwareLinkGraphNode = {
  id: string;
  kind: "firmware" | "device";
  label: string;
  subtitle?: string;
  firmwareKey?: string;
  deviceId?: string;
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
};

export function uniqueFirmwareFamilies(items: FirmwareCatalogItem[]): FirmwareFamilyNode[] {
  const byKey = new Map<string, FirmwareFamilyNode>();
  for (const item of items) {
    const prev = byKey.get(item.firmwareKey);
    if (!prev) {
      byKey.set(item.firmwareKey, {
        firmwareKey: item.firmwareKey,
        driverKey: item.driverKey,
        displayName: item.displayName || item.firmwareKey,
      });
      continue;
    }
    // Keep latest published when duplicate keys appear.
    byKey.set(item.firmwareKey, {
      firmwareKey: item.firmwareKey,
      driverKey: item.driverKey,
      displayName: item.displayName || prev.displayName,
    });
  }
  return [...byKey.values()].sort((a, b) => a.firmwareKey.localeCompare(b.firmwareKey));
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
    nodes.push({
      id: `fw:${family.firmwareKey}`,
      kind: "firmware",
      label: family.displayName,
      subtitle: family.firmwareKey,
      firmwareKey: family.firmwareKey,
      position: { x: 40, y: 40 + index * 110 },
    });
  });

  input.devices.forEach((device, index) => {
    const nodeId = `dev:${device.id}`;
    nodes.push({
      id: nodeId,
      kind: "device",
      label: device.name,
      subtitle: device.ipAddress,
      deviceId: device.id,
      position: { x: 420, y: 40 + index * 90 },
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
