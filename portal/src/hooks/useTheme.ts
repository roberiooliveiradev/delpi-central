// src/hooks/useTheme.ts

import { useEffect, useState } from "react";

export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "theme";
const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

function resolveSystemTheme(): "light" | "dark" {
  return mediaQuery.matches ? "dark" : "light";
}

function applyThemeToDocument(value: Theme) {
  const root = document.documentElement;

  const resolved =
    value === "system" ? resolveSystemTheme() : value;

  root.setAttribute("data-theme", resolved);
}

export const useTheme = () => {
  const getInitialTheme = (): Theme => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark" || saved === "system") {
      return saved;
    }
    return "system";
  };

  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  const setTheme = (value: Theme) => {
    localStorage.setItem(STORAGE_KEY, value);
    setThemeState(value);
  };

  // Aplica sempre que o theme mudar
  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  // Escuta mudança do sistema SOMENTE se estiver em system
  useEffect(() => {
    if (theme !== "system") return;

    const handleChange = () => {
      applyThemeToDocument("system");
    };

    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [theme]);

  return { theme, setTheme };
};