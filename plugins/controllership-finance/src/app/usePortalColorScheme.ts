import { useEffect, useState } from "react";

/**
 * Mesmo sinal do Portal/kit (`data-theme` no documentElement, senão prefers-color-scheme).
 * Local ao MFE — não importa hook interno do plugin-ui (U15: sem mexer no kit).
 */
export function resolvePortalIsDark(): boolean {
  if (typeof document === "undefined") return false;
  const theme = document.documentElement.getAttribute("data-theme");
  if (theme === "dark") return true;
  if (theme === "light") return false;
  if (typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function usePortalColorScheme(): "dark" | "light" {
  const [scheme, setScheme] = useState<"dark" | "light">(() =>
    resolvePortalIsDark() ? "dark" : "light",
  );

  useEffect(() => {
    const sync = () => setScheme(resolvePortalIsDark() ? "dark" : "light");
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    const media =
      typeof window.matchMedia === "function"
        ? window.matchMedia("(prefers-color-scheme: dark)")
        : null;
    media?.addEventListener("change", sync);
    return () => {
      observer.disconnect();
      media?.removeEventListener("change", sync);
    };
  }, []);

  return scheme;
}
