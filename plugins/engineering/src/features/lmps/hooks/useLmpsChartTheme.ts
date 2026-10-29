import { useEffect, useState } from "react";

/**
 * Resolve os tokens visuais do Portal Engenharia para o Recharts, que
 * exige valores de cor em JS. As cores seguem `--en-*`/`--delpi-ui-*`
 * (mapeados dos tokens globais do Portal), então os gráficos acompanham
 * automaticamente o tema claro/escuro do host — sem paleta paralela.
 */
export type LmpsChartTheme = {
  accent: string;
  title: string;
  textMuted: string;
  border: string;
  surface: string;
  danger: string;
  fontSize: number;
};

const FALLBACK: LmpsChartTheme = {
  accent: "#089bdb",
  title: "#003866",
  textMuted: "rgba(17, 17, 17, 0.68)",
  border: "#e6e6e6",
  surface: "#ffffff",
  danger: "#b91c1c",
  fontSize: 13,
};

function readToken(el: Element, name: string, fallback: string): string {
  const value = getComputedStyle(el).getPropertyValue(name).trim();
  return value || fallback;
}

function resolveTheme(): LmpsChartTheme {
  if (typeof document === "undefined") return FALLBACK;
  const scope =
    document.querySelector(".portal-engineering") ?? document.documentElement;
  return {
    accent: readToken(scope, "--en-accent", FALLBACK.accent),
    title: readToken(scope, "--delpi-ui-title", FALLBACK.title),
    textMuted: readToken(scope, "--en-text-muted", FALLBACK.textMuted),
    border: readToken(scope, "--en-border", FALLBACK.border),
    surface: readToken(scope, "--en-surface", FALLBACK.surface),
    danger: readToken(scope, "--en-danger", FALLBACK.danger),
    fontSize: FALLBACK.fontSize,
  };
}

export function useLmpsChartTheme(): LmpsChartTheme {
  const [theme, setTheme] = useState<LmpsChartTheme>(FALLBACK);

  useEffect(() => {
    const update = () => setTheme(resolveTheme());
    update();

    // O tema da plataforma é controlado pelo host via `data-theme` no
    // <html>; observamos a troca para repintar os gráficos.
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme", "class"],
    });
    return () => observer.disconnect();
  }, []);

  return theme;
}
