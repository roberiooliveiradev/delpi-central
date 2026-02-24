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

export function resolveIcon(iconName?: string | null): IconComponent | null {
  if (!iconName) return null;

  const normalized = iconName.trim().toLowerCase();
  if (!normalized) return null;

  if (iconCache[normalized] !== undefined) {
    return iconCache[normalized];
  }

  const pascal = normalized.includes("-")
    ? toPascalCaseFromKebab(normalized)
    : normalized;

  const Component =
    (LucideIcons as any)[pascal] ||
    (LucideIcons as any)[
      pascal.charAt(0).toUpperCase() + pascal.slice(1)
    ] ||
    null;

  iconCache[normalized] = Component;

  return Component;
}