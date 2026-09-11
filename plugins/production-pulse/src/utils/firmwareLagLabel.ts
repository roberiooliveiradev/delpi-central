import { normalizeFirmwareVersionToken } from "./firmwareVersionDirection";

export type FirmwareLagKind = "current" | "behind" | "unknown" | "no-install" | "no-target";

export type FirmwareLagInfo = {
  kind: FirmwareLagKind;
  installedDisplay: string;
  availableDisplay: string;
  /** Compact map line, e.g. "1.3.2 → 2.0.0" or "2.0.0". */
  shortLabel: string;
  /** Slightly longer for popover/ARIA. */
  detailLabel: string;
};

function displayToken(raw: string | null | undefined): string {
  const normalized = normalizeFirmwareVersionToken(raw);
  if (normalized) return normalized;
  const text = String(raw ?? "").trim();
  return text || "—";
}

/** True when installed SemVer (or token) differs from available catalog version. */
export function isFirmwareBehind(
  installedVersion: string | null | undefined,
  availableVersion: string | null | undefined,
): boolean {
  const available = normalizeFirmwareVersionToken(availableVersion);
  if (!available) return false;
  const installed = normalizeFirmwareVersionToken(installedVersion);
  if (!installed) return true; // linked family has a release; chip never reported
  return installed !== available;
}

/**
 * Human labels for map/summary: prefer short SemVer and show installed → available
 * instead of a bare "desatualizado".
 */
export function resolveFirmwareLagInfo(
  installedVersion: string | null | undefined,
  availableVersion: string | null | undefined,
): FirmwareLagInfo {
  const installedRaw = String(installedVersion ?? "").trim();
  const availableRaw = String(availableVersion ?? "").trim();
  const installedDisplay = displayToken(installedRaw || null);
  const availableDisplay = displayToken(availableRaw || null);

  if (!availableRaw) {
    return {
      kind: "no-target",
      installedDisplay,
      availableDisplay,
      shortLabel: installedRaw ? `FW ${installedDisplay}` : "FW —",
      detailLabel: installedRaw
        ? `Em execução ${installedDisplay}`
        : "Sem versão publicada na família",
    };
  }

  if (!installedRaw) {
    return {
      kind: "no-install",
      installedDisplay: "—",
      availableDisplay,
      shortLabel: `FW — → ${availableDisplay}`,
      detailLabel: `Chip ainda não reportou versão · catálogo ${availableDisplay}`,
    };
  }

  const installedNorm = normalizeFirmwareVersionToken(installedRaw);
  const availableNorm = normalizeFirmwareVersionToken(availableRaw);
  if (installedNorm && availableNorm && installedNorm === availableNorm) {
    return {
      kind: "current",
      installedDisplay,
      availableDisplay,
      shortLabel: `FW ${installedDisplay}`,
      detailLabel: `Em execução ${installedDisplay} (catálogo)`,
    };
  }

  if (installedNorm && availableNorm) {
    return {
      kind: "behind",
      installedDisplay,
      availableDisplay,
      shortLabel: `FW ${installedDisplay} → ${availableDisplay}`,
      detailLabel: `Em execução ${installedDisplay} · catálogo ${availableDisplay}`,
    };
  }

  return {
    kind: "unknown",
    installedDisplay,
    availableDisplay,
    shortLabel: `FW ${installedDisplay} → ${availableDisplay}`,
    detailLabel: `Em execução ${installedDisplay} · catálogo ${availableDisplay}`,
  };
}

export function formatFamilyOutdatedSummary(outdatedCount: number, latestVersion: string | null): string {
  if (outdatedCount <= 0) return "";
  const latest = displayToken(latestVersion);
  if (latest === "—") return ` · ${outdatedCount} atrás`;
  return ` · ${outdatedCount} atrás (→${latest})`;
}
