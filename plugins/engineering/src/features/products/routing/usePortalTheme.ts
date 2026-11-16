import { useEffect, useState } from "react";

/** Tema do Portal lido do host — `data-theme` no <html> para o modo e
 * `--en-surface` (token já mapeado claro/escuro em index.css) para o
 * fundo da área do gráfico. Mesmo mecanismo de `useLmpsChartTheme`:
 * sem paleta paralela nem cor hardcoded. */
export type PortalChartTheme = {
  mode: "light" | "dark";
  surface: string;
};

const FALLBACK_SURFACE = "#ffffff";

function resolveTheme(): PortalChartTheme {
  if (typeof document === "undefined") {
    return { mode: "light", surface: FALLBACK_SURFACE };
  }
  const scope =
    document.querySelector(".portal-engineering") ??
    document.documentElement;
  const surface =
    getComputedStyle(scope).getPropertyValue("--en-surface").trim() ||
    FALLBACK_SURFACE;
  return {
    mode:
      document.documentElement.dataset.theme === "dark"
        ? "dark"
        : "light",
    surface,
  };
}

export function usePortalTheme(): PortalChartTheme {
  const [theme, setTheme] = useState<PortalChartTheme>(resolveTheme);

  useEffect(() => {
    const update = () => setTheme(resolveTheme());
    update();
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
  }, []);

  return theme;
}
