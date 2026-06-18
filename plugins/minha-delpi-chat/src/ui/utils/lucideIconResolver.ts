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
    .replace(/_/g, "-")
    .toLowerCase();
}

export function isPascalCaseLucideExport(name: string): boolean {
  return /^[A-Z][A-Za-z0-9]*$/.test(name);
}

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
    (LucideIcons as unknown as Record<string, LucideIcon | undefined>)[pascal] ??
    (LucideIcons as unknown as Record<string, LucideIcon | undefined>)[
      pascal.charAt(0).toUpperCase() + pascal.slice(1)
    ] ??
    null;

  iconCache.set(normalized, component);

  return component;
}

export function isLucideIconName(iconName?: string | null): boolean {
  return resolveLucideIcon(iconName) !== null;
}
