import type { FirmwareLifecycle, FirmwareListItem } from "../api/productionPulseApi";
import { PP_HELP } from "../content/helpTooltips";

export function firmwareLifecycleLabel(lifecycle: FirmwareLifecycle | string): string {
  if (lifecycle === "draft") return PP_HELP.ota.status.draft;
  if (lifecycle === "archived") return PP_HELP.ota.statusArchived;
  return PP_HELP.ota.statusPublished;
}

export function firmwareLifecycleBadgeClass(lifecycle: FirmwareLifecycle | string): string {
  if (lifecycle === "draft") return "pp-lifecycle-badge pp-lifecycle-badge--draft";
  if (lifecycle === "archived") return "pp-lifecycle-badge pp-lifecycle-badge--archived";
  return "pp-lifecycle-badge pp-lifecycle-badge--published";
}

export function formatFirmwareArtifactBytes(bytes: number | null | undefined): string | null {
  if (bytes == null || !Number.isFinite(bytes) || bytes < 0) return null;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(bytes < 10_240 ? 1 : 0)} KiB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
}

export function summarizeFirmwareCatalogItem(item: FirmwareListItem): {
  title: string;
  familyKey: string;
  version: string;
  driverKey: string;
  lifecycle: FirmwareLifecycle | string;
  lifecycleLabel: string;
  hasArtifact: boolean;
  artifactSizeLabel: string | null;
  hasSource: boolean;
} {
  const title = item.displayName?.trim() || item.firmwareKey;
  return {
    title,
    familyKey: item.firmwareKey,
    version: item.version,
    driverKey: item.driverKey,
    lifecycle: item.lifecycle,
    lifecycleLabel: firmwareLifecycleLabel(item.lifecycle),
    hasArtifact: Boolean(item.hasArtifact),
    artifactSizeLabel: formatFirmwareArtifactBytes(item.artifactSizeBytes),
    hasSource: Boolean(item.hasSource),
  };
}
