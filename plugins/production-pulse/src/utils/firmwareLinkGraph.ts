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
  outdatedCount?: number;
  installedFirmwareVersion?: string | null;
  availableVersion?: string | null;
  ipAddress?: string | null;
  status?: string | null;
  counter?: number | null;
  counterDay?: number | null;
  counterShift?: number | null;
  lastSeenAt?: string | null;
  dimmed?: boolean;
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
  outdatedCount: number;
  /** Latest published firmware row id for this family (for entity selection). */
  latestFirmwareId?: string | null;
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
          outdatedCount: 0,
          latestFirmwareId: item.id,
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
        outdatedCount: 0,
        latestFirmwareId: item.id,
      },
    });
  }

  const families = [...byKey.values()].map((entry) => entry.family);
  for (const family of families) {
    const linked = devices.filter(
      (device) => explicitFirmwareKey(device) === family.firmwareKey,
    );
    family.linkedCount = linked.length;
    family.outdatedCount = linked.filter((device) => {
      const installed = device.installedFirmwareVersion?.trim() || null;
      return installed !== (family.latestVersion ?? null);
    }).length;
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
  /** Optional search/status filter — matching nodes stay bright; others dim. */
  filterQuery?: string;
  filterStatus?: string;
}): { nodes: FirmwareLinkGraphNode[]; edges: FirmwareLinkGraphEdge[] } {
  const nodes: FirmwareLinkGraphNode[] = [];
  const edges: FirmwareLinkGraphEdge[] = [];
  const familyKeys = new Set(input.families.map((f) => f.firmwareKey));
  const query = input.filterQuery?.trim().toLowerCase() ?? "";
  const statusFilter = input.filterStatus?.trim() ?? "";

  const matchesQuery = (haystack: string) =>
    !query || haystack.toLowerCase().includes(query);

  input.families.forEach((family, index) => {
    const versionLabel = family.latestVersion ? `v${family.latestVersion}` : "sem versão";
    const dimmed =
      Boolean(query) &&
      !matchesQuery(
        `${family.displayName} ${family.firmwareKey} ${family.latestVersion ?? ""}`,
      );
    nodes.push({
      id: `fw:${family.firmwareKey}`,
      kind: "firmware",
      label: family.displayName,
      subtitle: `${family.firmwareKey} · ${versionLabel}`,
      firmwareKey: family.firmwareKey,
      latestVersion: family.latestVersion,
      linkedCount: family.linkedCount,
      outdatedCount: family.outdatedCount,
      dimmed,
      position: { x: 40, y: 40 + index * 160 },
    });
  });

  input.devices.forEach((device, index) => {
    const nodeId = `dev:${device.id}`;
    const installed = device.installedFirmwareVersion?.trim() || null;
    const familyKey = explicitFirmwareKey(device);
    const family = input.families.find((item) => item.firmwareKey === familyKey);
    const available = family?.latestVersion ?? null;
    const counter =
      typeof device.lastMetrics?.counter === "number"
        ? device.lastMetrics.counter
        : typeof device.lastMetrics?.counter === "string"
          ? Number(device.lastMetrics.counter)
          : null;
    const counterDay = device.periodDeltas?.day?.counter ?? null;
    const counterShift = device.periodDeltas?.shift?.counter ?? null;
    const statusMatch = !statusFilter || device.status === statusFilter;
    const dimmed =
      (!statusMatch) ||
      (Boolean(query) &&
        !matchesQuery(
          `${device.name} ${device.ipAddress} ${installed ?? ""} ${device.driverKey}`,
        ));
    nodes.push({
      id: nodeId,
      kind: "device",
      label: device.name,
      subtitle: device.ipAddress,
      deviceId: device.id,
      ipAddress: device.ipAddress,
      installedFirmwareVersion: installed,
      availableVersion: available,
      status: device.status,
      counter: Number.isFinite(counter) ? counter : null,
      counterDay,
      counterShift,
      lastSeenAt: device.lastSeenAt,
      dimmed,
      position: { x: 460, y: 40 + index * 170 },
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
