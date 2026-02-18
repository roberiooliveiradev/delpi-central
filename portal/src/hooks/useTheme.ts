// src/hooks/useTheme.ts

import { useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";

export const useTheme = () => {
  const getInitialTheme = (): Theme => {
    const saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark" || saved === "system") {
      return saved;
    }
    return "system";
  };

  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    const root = document.documentElement;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const applyTheme = (value: Theme) => {
      if (value === "dark") {
        root.setAttribute("data-theme", "dark");
      } else if (value === "light") {
        root.setAttribute("data-theme", "light");
      } else {
        // system
        if (mediaQuery.matches) {
          root.setAttribute("data-theme", "dark");
        } else {
          root.setAttribute("data-theme", "light");
        }
      }
    };

    applyTheme(theme);
    localStorage.setItem("theme", theme);

    // Se estiver em "system", escutar mudança do sistema
    const handleChange = () => {
      if (theme === "system") {
        applyTheme("system");
      }
    };

    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [theme]);

  return { theme, setTheme };
};
