// src/utils/theme.ts

export type Theme = "light" | "dark" | "system";

export const THEME_STORAGE_KEY = "theme";

const mediaQuery =
  typeof window !== "undefined"
    ? window.matchMedia("(prefers-color-scheme: dark)")
    : null;

export function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";

  const saved = localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === "light" || saved === "dark" || saved === "system") {
    return saved;
  }
  return "system";
}

export function resolveTheme(theme: Theme): "light" | "dark" {
  if (theme === "light") return "light";
  if (theme === "dark") return "dark";
  if (!mediaQuery) return "light";
  return mediaQuery.matches ? "dark" : "light";
}

export function applyThemeToDocument(value: Theme) {
  if (typeof document === "undefined") return;

  document.documentElement.setAttribute("data-theme", resolveTheme(value));
}

export function buildThemeMessage() {
  const theme = getStoredTheme();
  return {
    type: "DELPI_THEME" as const,
    theme,
    resolved: resolveTheme(theme),
  };
}
