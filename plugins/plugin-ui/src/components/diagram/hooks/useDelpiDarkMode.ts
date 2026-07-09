import { useEffect, useState } from "react";

export function resolveDelpiIsDark(): boolean {
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
export function useDelpiDarkMode(): boolean {
  const [isDark, setIsDark] = useState(resolveDelpiIsDark);

  useEffect(() => {
    const sync = () => setIsDark(resolveDelpiIsDark());

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
