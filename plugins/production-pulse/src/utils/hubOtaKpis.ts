import type { FirmwareListItem, FirmwareUpdateSummary } from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";
import { explicitFirmwareKey, isNewerFirmwareRelease } from "./firmwareLinkGraph";

export type HubOtaKpis = {
  /** Versões elegíveis para OTA (published e não arquivadas). */
  publishedFirmwares: number;
  /** IoTs com vínculo explícito de família. */
  linkedDevices: number;
  /** IoTs vinculados cuja versão instalada difere da última publicada da família. */
  outdatedDevices: number;
  updatingDevices: number;
  failedDevices: number;
};

export const EMPTY_HUB_OTA_KPIS: HubOtaKpis = {
  publishedFirmwares: 0,
  linkedDevices: 0,
  outdatedDevices: 0,
  updatingDevices: 0,
  failedDevices: 0,
};

export function isPublishedFirmware(item: FirmwareListItem): boolean {
  if (item.archivedAt) return false;
  return item.lifecycle === "published" || Boolean(item.publishedAt);
}

export function countPublishedFirmwares(firmwares: FirmwareListItem[]): number {
  return firmwares.filter(isPublishedFirmware).length;
}

/** Última versão publicada por família — mesma ordem de release do canvas. */
export function latestPublishedVersionByFamily(
  firmwares: FirmwareListItem[],
): Map<string, string> {
  const latest = new Map<string, FirmwareListItem>();
  for (const item of firmwares) {
    if (!isPublishedFirmware(item)) continue;
    const current = latest.get(item.firmwareKey);
    if (!current || isNewerFirmwareRelease(item, current)) {
      latest.set(item.firmwareKey, item);
    }
  }
  return new Map([...latest].map(([key, item]) => [key, item.version]));
}

export function linkedDevices(devices: DeviceListItem[]): DeviceListItem[] {
  return devices.filter((device) => explicitFirmwareKey(device) !== null);
}

export function countLinkedDevices(devices: DeviceListItem[]): number {
  return linkedDevices(devices).length;
}

/**
 * Desatualizado = vinculado + família com versão publicada + instalada ≠ publicada.
 * Sem versão instalada reportada, o IoT conta como desatualizado (nunca aplicou OTA).
 */
export function countOutdatedDevices(
  devices: DeviceListItem[],
  firmwares: FirmwareListItem[],
): number {
  const latestByFamily = latestPublishedVersionByFamily(firmwares);
  return linkedDevices(devices).filter((device) => {
    const family = explicitFirmwareKey(device);
    if (!family) return false;
    const latest = latestByFamily.get(family);
    if (!latest) return false;
    return (device.installedFirmwareVersion?.trim() || null) !== latest;
  }).length;
}

export function computeHubOtaKpis(input: {
  firmwares: FirmwareListItem[];
  devices: DeviceListItem[];
  updateSummary: FirmwareUpdateSummary | null;
}): HubOtaKpis {
  return {
    publishedFirmwares: countPublishedFirmwares(input.firmwares),
    linkedDevices: countLinkedDevices(input.devices),
    outdatedDevices: countOutdatedDevices(input.devices, input.firmwares),
    updatingDevices: input.updateSummary?.updating ?? 0,
    failedDevices: input.updateSummary?.failed ?? 0,
  };
}
