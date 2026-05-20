// src/hooks/useTheme.ts

import { useEffect, useState } from "react";
import {
  applyThemeToDocument,
  getStoredTheme,
  resolveTheme,
  type Theme,
  THEME_STORAGE_KEY,
} from "../utils/theme";

const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

function notifyThemeChange(theme: Theme) {
  window.dispatchEvent(
    new CustomEvent("DELPI_THEME_CHANGE", {
      detail: {
        theme,
        resolved: resolveTheme(theme),
      },
    }),
  );
}

export type { Theme };

export const useTheme = () => {
  const [theme, setThemeState] = useState<Theme>(getStoredTheme);

  const setTheme = (value: Theme) => {
    localStorage.setItem(THEME_STORAGE_KEY, value);
    setThemeState(value);
  };

  useEffect(() => {
    applyThemeToDocument(theme);
    notifyThemeChange(theme);
  }, [theme]);

  useEffect(() => {
    if (theme !== "system") return;

    const handleChange = () => {
      applyThemeToDocument("system");
      notifyThemeChange("system");
    };

    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [theme]);

  return { theme, setTheme };
};
