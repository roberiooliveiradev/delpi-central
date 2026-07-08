import * as LucideIcons from "lucide-react";
import type { LucideIcon } from "lucide-react";

const iconCache = new Map<string, LucideIcon | null>();

export function toPascalCaseFromKebab(kebab: string): string {
  return kebab
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

export function toKebabCase(name: string): string {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/([A-Za-z])([0-9])/g, "$1-$2")
    .replace(/_/g, "-")
    .toLowerCase();
}

export function isPascalCaseLucideExport(name: string): boolean {
  return /^[A-Z][A-Za-z0-9]*$/.test(name);
}

/** Lista completa de exports Lucide em PascalCase (para picker genérico). */
export function listLucideIconNames(): string[] {
  return Object.keys(LucideIcons).filter(isPascalCaseLucideExport).sort();
}

export function resolveLucideIcon(iconName?: string | null): LucideIcon | null {
  const normalized = String(iconName ?? "")
    .trim()
    .toLowerCase();

  if (!normalized) {
    return null;
  }

  if (iconCache.has(normalized)) {
    return iconCache.get(normalized) ?? null;
  }

  const withoutIconSuffix = normalized.endsWith("-icon")
    ? normalized.slice(0, -"-icon".length)
    : normalized;

  const pascal = withoutIconSuffix.includes("-")
    ? toPascalCaseFromKebab(withoutIconSuffix)
    : withoutIconSuffix.charAt(0).toUpperCase() + withoutIconSuffix.slice(1);

  const component =
    (LucideIcons as unknown as Record<string, LucideIcon | undefined>)[pascal] ?? null;

  iconCache.set(normalized, component);
  return component;
}

export function isLucideIconName(iconName?: string | null): boolean {
  return resolveLucideIcon(iconName) !== null;
}

/**
 * Catálogo curado para formulários / experiência do cliente (kebab-case).
 * Mantém o picker leve e alinhado a casos de uso de negócio.
 */
export const CURATED_LUCIDE_ICON_NAMES = [
  "eye",
  "heart",
  "star",
  "smile",
  "thumbs-up",
  "thumbs-down",
  "handshake",
  "users",
  "user",
  "user-round",
  "building-2",
  "factory",
  "map-pin",
  "globe",
  "clipboard-list",
  "clipboard-check",
  "check-circle-2",
  "circle-alert",
  "triangle-alert",
  "info",
  "search",
  "message-circle",
  "mail",
  "phone",
  "calendar",
  "clock",
  "award",
  "shield-check",
  "sparkles",
  "lightbulb",
  "target",
  "trending-up",
  "bar-chart-3",
  "line-chart",
  "package",
  "truck",
  "wrench",
  "settings",
  "sliders-horizontal",
  "file-text",
  "folder-open",
  "image",
  "camera",
  "headphones",
  "megaphone",
  "flag",
  "bookmark",
  "coffee",
  "leaf",
  "sun",
  "moon",
  "zap",
] as const;

export type CuratedLucideIconName = (typeof CURATED_LUCIDE_ICON_NAMES)[number];
