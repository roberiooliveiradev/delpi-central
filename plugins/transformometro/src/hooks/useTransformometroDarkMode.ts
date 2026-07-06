import { useEffect, useState } from "react";

function resolveIsDark(): boolean {
  if (typeof document === "undefined") {
    return false;
  }

  const theme = document.documentElement.getAttribute("data-theme");
  if (theme === "dark") {
    return true;
  }
  if (theme === "light") {
    return false;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Segue `data-theme` do shell Delpi (light / dark / system). */
export function useTransformometroDarkMode(): boolean {
  const [isDark, setIsDark] = useState(resolveIsDark);

  useEffect(() => {
    const sync = () => setIsDark(resolveIsDark());

    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", sync);

    return () => {
      observer.disconnect();
      media.removeEventListener("change", sync);
    };
  }, []);

  return isDark;
}

export function resolveMermaidTheme(isDark: boolean): "dark" | "neutral" {
  return isDark ? "dark" : "neutral";
}
