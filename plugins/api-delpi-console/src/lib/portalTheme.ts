export type PortalThemePreference = "light" | "dark" | "system";
export type ResolvedPortalTheme = "light" | "dark";

const THEME_STORAGE_KEY = "theme";

export function resolvePortalTheme(): ResolvedPortalTheme {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "light" || attr === "dark") return attr;

  const saved = localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === "light" || saved === "dark") return saved;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function getPortalThemePreference(): PortalThemePreference {
  const saved = localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === "light" || saved === "dark" || saved === "system") return saved;
  return "system";
}

export function buildThemeMessage() {
  return {
    type: "DELPI_THEME" as const,
    theme: getPortalThemePreference(),
    resolved: resolvePortalTheme(),
  };
}
