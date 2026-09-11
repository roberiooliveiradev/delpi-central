/**
 * Canonical SemVer direction for OTA UX (upgrade / rollback).
 * Does NOT use publishedAt — an older SemVer published later is still a downgrade.
 */

export type FirmwareChangeDirection = "upgrade" | "downgrade" | "same" | "unknown";

type SemVerParts = {
  major: number;
  minor: number;
  patch: number;
};

/** Strip leading `v`/`V` and optional firmware-key prefix before the last SemVer-ish segment. */
export function normalizeFirmwareVersionToken(raw: string | null | undefined): string {
  const text = String(raw ?? "").trim();
  if (!text) return "";
  // Prefer trailing X.Y.Z if present (e.g. esp8266_counter_v1.3.2 → 1.3.2)
  const trailing = text.match(/(\d+\.\d+\.\d+)(?:[-+].*)?$/);
  if (trailing) return trailing[1];
  return text.replace(/^v/i, "");
}

export function parseSemVer(raw: string | null | undefined): SemVerParts | null {
  const token = normalizeFirmwareVersionToken(raw);
  if (!token) return null;
  const match = token.match(/^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$/);
  if (!match) return null;
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
  };
}

function compareSemVerParts(a: SemVerParts, b: SemVerParts): number {
  if (a.major !== b.major) return a.major < b.major ? -1 : 1;
  if (a.minor !== b.minor) return a.minor < b.minor ? -1 : 1;
  if (a.patch !== b.patch) return a.patch < b.patch ? -1 : 1;
  return 0;
}

export function resolveFirmwareChangeDirection(
  installedVersion: string | null | undefined,
  destinationVersion: string | null | undefined,
): FirmwareChangeDirection {
  const fromRaw = String(installedVersion ?? "").trim();
  const toRaw = String(destinationVersion ?? "").trim();
  if (!fromRaw || !toRaw) return "unknown";
  if (fromRaw === toRaw) return "same";

  const from = parseSemVer(fromRaw);
  const to = parseSemVer(toRaw);
  if (!from || !to) {
    // Same normalized token after strip → same; else unknown (no false upgrade/downgrade).
    const nFrom = normalizeFirmwareVersionToken(fromRaw);
    const nTo = normalizeFirmwareVersionToken(toRaw);
    if (nFrom && nTo && nFrom === nTo) return "same";
    return "unknown";
  }

  const cmp = compareSemVerParts(from, to);
  if (cmp === 0) return "same";
  return cmp < 0 ? "upgrade" : "downgrade";
}
