import type { DeviceListItem } from "../types/device";
import type { PanelAnchorTypeFilter, PanelGroupBy, PanelStatusFilter } from "./panelFilterUrl";

export type DeviceGroup = {
  key: string;
  title: string;
  anchorType: string | null;
  devices: DeviceListItem[];
  onlineCount: number;
};

const UNBOUND_GROUP_KEY = "__unbound__";

export function groupDevices(
  devices: DeviceListItem[],
  groupBy: PanelGroupBy,
): DeviceGroup[] {
  const map = new Map<string, DeviceGroup>();

  for (const device of devices) {
    const { key, title, anchorType } = resolveGroupMeta(device, groupBy);
    const existing = map.get(key);
    if (existing) {
      existing.devices.push(device);
      if (device.status === "online") existing.onlineCount += 1;
      continue;
    }
    map.set(key, {
      key,
      title,
      anchorType,
      devices: [device],
      onlineCount: device.status === "online" ? 1 : 0,
    });
  }

  return Array.from(map.values()).sort((a, b) => {
    if (a.key === UNBOUND_GROUP_KEY) return 1;
    if (b.key === UNBOUND_GROUP_KEY) return -1;
    return a.title.localeCompare(b.title, "pt-BR");
  });
}

function resolveGroupMeta(
  device: DeviceListItem,
  groupBy: PanelGroupBy,
): { key: string; title: string; anchorType: string | null } {
  const binding = device.binding;
  if (!binding) {
    return {
      key: UNBOUND_GROUP_KEY,
      title: "Sem amarração",
      anchorType: null,
    };
  }

  if (binding.anchorType === "standalone") {
    return {
      key: binding.placementKey,
      title: device.name,
      anchorType: binding.anchorType,
    };
  }

  if (groupBy === "work_center") {
    const code = binding.workCenterCode ?? "";
    const name = binding.workCenterName ?? binding.placementLabel;
    return {
      key: `wc:${code || binding.placementKey}`,
      title: code ? `${code} · ${name}` : name,
      anchorType: binding.anchorType,
    };
  }

  if (groupBy === "machine") {
    const label = binding.machineLabel ?? binding.placementLabel;
    return {
      key: `machine:${binding.placementKey}`,
      title: label,
      anchorType: binding.anchorType,
    };
  }

  if (groupBy === "equipment") {
    const label = binding.equipmentLabel ?? binding.placementLabel;
    return {
      key: `equipment:${binding.placementKey}`,
      title: label,
      anchorType: binding.anchorType,
    };
  }

  const label = binding.areaLabel ?? binding.placementLabel;
  return {
    key: `area:${binding.placementKey}`,
    title: label,
    anchorType: binding.anchorType,
  };
}

export function applyClientFilters(
  devices: DeviceListItem[],
  filters: {
    status: PanelStatusFilter;
    anchorType: PanelAnchorTypeFilter;
  },
): DeviceListItem[] {
  return devices.filter((device) => {
    if (filters.status && device.status !== filters.status) return false;
    if (filters.anchorType) {
      if (!device.binding) return filters.anchorType === "standalone" && device.status === "no_binding";
      return device.binding.anchorType === filters.anchorType;
    }
    return true;
  });
}

export function paginateDevices<T>(items: T[], page: number, pageSize: number): T[] {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

export function totalPages(count: number, pageSize: number): number {
  return Math.max(1, Math.ceil(count / pageSize));
}
