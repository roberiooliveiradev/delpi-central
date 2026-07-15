import type { LucideIcon } from "lucide-react";
import * as LucideIcons from "lucide-react";

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

function isPascalCaseLucideExport(name: string): boolean {
  return (
    /^[A-Z][A-Za-z0-9]*$/.test(name) &&
    !name.endsWith("Icon") &&
    !name.startsWith("Lucide")
  );
}

function isIconComponent(value: unknown): value is LucideIcon {
  return (
    typeof value === "function" ||
    (typeof value === "object" && value !== null)
  );
}

/** Lista PascalCase do catálogo Lucide bundled no MFE. */
export function listLucideIconNames(): string[] {
  return Object.keys(LucideIcons)
    .filter(isPascalCaseLucideExport)
    .filter((name) =>
      isIconComponent((LucideIcons as Record<string, unknown>)[name]),
    )
    .sort((a, b) => a.localeCompare(b));
}

export function resolveLucideIcon(iconName?: string | null): LucideIcon | null {
  const normalized = String(iconName ?? "")
    .trim()
    .toLowerCase();
  if (!normalized) return null;
  if (iconCache.has(normalized)) {
    return iconCache.get(normalized) ?? null;
  }

  const withoutIconSuffix = normalized.endsWith("-icon")
    ? normalized.slice(0, -"-icon".length)
    : normalized;
  const pascal = withoutIconSuffix.includes("-")
    ? toPascalCaseFromKebab(withoutIconSuffix)
    : withoutIconSuffix.charAt(0).toUpperCase() + withoutIconSuffix.slice(1);

  const candidate = (LucideIcons as unknown as Record<string, unknown>)[pascal];
  const component = isIconComponent(candidate) ? (candidate as LucideIcon) : null;
  iconCache.set(normalized, component);
  return component;
}

/** Catálogo curado para departamentos (kebab). */
export const DEPARTMENT_ICON_CATALOG = [
  "book-open",
  "receipt",
  "building-2",
  "factory",
  "briefcase",
  "clipboard-list",
  "clipboard-check",
  "file-text",
  "files",
  "folder-open",
  "users",
  "user-cog",
  "handshake",
  "wrench",
  "settings",
  "shield-check",
  "badge-check",
  "truck",
  "package",
  "warehouse",
  "shopping-cart",
  "calculator",
  "landmark",
  "scale",
  "gavel",
  "heart-pulse",
  "stethoscope",
  "microscope",
  "cpu",
  "monitor",
  "network",
  "globe",
  "map-pin",
  "chart-column",
  "chart-line",
  "pie-chart",
  "megaphone",
  "bell",
  "mail",
  "phone",
  "calendar",
  "clock",
  "lightbulb",
  "graduation-cap",
  "award",
  "star",
  "flag",
  "layers",
  "boxes",
  "cog",
] as const;
