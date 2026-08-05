// src/utils/iconResolver.ts


import * as LucideIcons from "lucide-react";

type IconComponent = React.ComponentType<{ size?: number }>;

// Cache interno para evitar reprocessamento
const iconCache: Record<string, IconComponent | null> = {};

function toPascalCaseFromKebab(kebab: string): string {
  return kebab
    .split("-")
    .filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join("");
}

/**
 * Nome do export lucide correspondente ao valor gravado no manifesto
 * (`award`, `line-chart`, `lucide-line-chart`, `LineChart`, `line-chart-icon`).
 */
export function resolveIconExportName(iconName?: string | null): string | null {
  if (!iconName) return null;

  const raw = iconName.trim();
  if (raw && (LucideIcons as any)[raw]) return raw;

  const normalized = raw.toLowerCase();
  if (!normalized) return null;

  const withoutIconSuffix = normalized.endsWith("-icon")
    ? normalized.slice(0, -"-icon".length)
    : normalized;

  // Manifestos gravam tanto `line-chart` quanto `lucide-line-chart`.
  const bare = withoutIconSuffix.startsWith("lucide-")
    ? withoutIconSuffix.slice("lucide-".length)
    : withoutIconSuffix;

  const pascal = toPascalCaseFromKebab(bare);
  return (LucideIcons as any)[pascal] ? pascal : null;
}

export function resolveIcon(iconName?: string | null): IconComponent | null {
  if (!iconName) return null;

  const key = iconName.trim();
  if (!key) return null;

  if (iconCache[key] !== undefined) {
    return iconCache[key];
  }

  const exportName = resolveIconExportName(key);
  const Component = exportName ? (LucideIcons as any)[exportName] : null;

  iconCache[key] = Component;

  return Component;
}

/** `LineChart` → `line-chart` (formato gravado no manifesto). */
export function iconExportNameToKebab(name: string): string {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/_/g, "-")
    .toLowerCase();
}