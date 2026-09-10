import type { FirmwareListItem } from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";

export type FirmwareLinkEdgeKind = "explicit";

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
  /**
   * Driver keys accepted by the API for this family:
   * `{ firmwareKey } ∪ driverKey of every catalog version (incl. archived/draft)`.
   */
  compatibleDriverKeys: string[];
};

export type LinkMode =
  | { origin: "firmware"; firmwareKey: string }
  | { origin: "device"; deviceId: string };

export type ConnectionCandidateState =
  | "origin"
  | "compatible"
  | "incompatible"
  | "already-linked"
  | "replace-link"
  | "neutral";

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

/**
 * Mirrors API `_assert_compatible`:
 * compatible = { firmwareKey } ∪ { driver_key of every version with that firmware_key }.
 */
export function buildCompatibleDriverKeys(
  firmwares: FirmwareListItem[],
  firmwareKey: string,
): string[] {
  const keys = new Set<string>([firmwareKey]);
  for (const row of firmwares) {
    if (row.firmwareKey !== firmwareKey) continue;
    const dk = String(row.driverKey || "").trim();
    if (dk) keys.add(dk);
  }
  return [...keys].sort();
}

export function isFirmwareDeviceCompatible(
  deviceDriverKey: string,
  compatibleDriverKeys: readonly string[],
): boolean {
  const driver = String(deviceDriverKey || "").trim();
  if (!driver) return false;
  return compatibleDriverKeys.includes(driver);
}

/** Effective assigned family for canvas solid edge (explicit column only). */
export function explicitFirmwareKey(device: DeviceListItem): string | null {
  const assigned = device.assignedFirmwareKey;
  if (assigned && String(assigned).trim()) return String(assigned).trim();
  return null;
}

/**
 * Classify a graph node during Connection Mode.
 * `filterDimmed` is orthogonal and must not be folded into these states.
 */
export function resolveConnectionCandidateState(input: {
  linkMode: LinkMode | null;
  nodeKind: "firmware" | "device";
  firmwareKey?: string | null;
  deviceId?: string | null;
  deviceDriverKey?: string | null;
  assignedFirmwareKey?: string | null;
  familyByKey: ReadonlyMap<string, FirmwareFamilyNode>;
}): ConnectionCandidateState {
  const { linkMode } = input;
  if (!linkMode) return "neutral";

  if (linkMode.origin === "firmware") {
    if (input.nodeKind === "firmware") {
      return input.firmwareKey === linkMode.firmwareKey ? "origin" : "neutral";
    }
    const family = input.familyByKey.get(linkMode.firmwareKey);
    if (!family) return "incompatible";
    const assigned = input.assignedFirmwareKey?.trim() || null;
    if (assigned === linkMode.firmwareKey) return "already-linked";
    const compatible = isFirmwareDeviceCompatible(
      input.deviceDriverKey ?? "",
      family.compatibleDriverKeys,
    );
    if (!compatible) return "incompatible";
    if (assigned && assigned !== linkMode.firmwareKey) return "replace-link";
    return "compatible";
  }

  // origin === "device" — deviceDriverKey / assignedFirmwareKey refer to the origin IoT.
  if (input.nodeKind === "device") {
    return input.deviceId === linkMode.deviceId ? "origin" : "neutral";
  }
  const family = input.firmwareKey
    ? input.familyByKey.get(input.firmwareKey)
    : undefined;
  if (!family) return "incompatible";
  const assigned = input.assignedFirmwareKey?.trim() || null;
  if (assigned === input.firmwareKey) return "already-linked";
  const compatible = isFirmwareDeviceCompatible(
    input.deviceDriverKey ?? "",
    family.compatibleDriverKeys,
  );
  if (!compatible) return "incompatible";
  if (assigned && assigned !== input.firmwareKey) return "replace-link";
  return "compatible";
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
          compatibleDriverKeys: [],
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
        compatibleDriverKeys: [],
      },
    });
  }

  const families = [...byKey.values()].map((entry) => entry.family);
  for (const family of families) {
    family.compatibleDriverKeys = buildCompatibleDriverKeys(items, family.firmwareKey);
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

/**
 * Build graph: firmware nodes left, devices right.
 * Only explicit OTA links (`assignedFirmwareKey`) produce edges.
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
      !statusMatch ||
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
  return next;
}
