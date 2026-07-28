import { useEffect, useState } from "react";

export type PublicThemeMode = "light" | "dark";

const STORAGE_KEY = "pub-theme";

function systemMode(): PublicThemeMode {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function storedMode(): PublicThemeMode | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

/** Tema efetivo do hub (attr → storage → SO). */
export function resolvePublicThemeMode(): PublicThemeMode {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "light" || attr === "dark") return attr;
  return storedMode() ?? systemMode();
}

/** Reage a toggle (`data-theme`) e a mudança do SO quando não há preferência fixada. */
export function usePublicThemeMode(): PublicThemeMode {
  const [mode, setMode] = useState<PublicThemeMode>(() => resolvePublicThemeMode());

  useEffect(() => {
    const root = document.documentElement;
    const sync = () => setMode(resolvePublicThemeMode());
    const observer = new MutationObserver(sync);
    observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });

    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    const onMq = () => {
      if (!storedMode() && !root.getAttribute("data-theme")) sync();
    };
    mq?.addEventListener("change", onMq);

    return () => {
      observer.disconnect();
      mq?.removeEventListener("change", onMq);
    };
  }, []);

  return mode;
}

/**
 * Alterna claro/escuro no public-hub. Sem preferência fixada, segue o SO
 * (inclusive reagindo a mudanças em tempo real). Ao clicar, fixa a escolha
 * em `data-theme` no <html> e persiste em localStorage.
 */
export function ThemeToggle() {
  const mode = usePublicThemeMode();

  const toggle = () => {
    const next: PublicThemeMode = mode === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* modo privado / storage indisponível — só não persiste */
    }
  };

  const isDark = mode === "dark";

  return (
    <button
      type="button"
      className="pub-theme-toggle"
      onClick={toggle}
      aria-label={isDark ? "Ativar modo claro" : "Ativar modo escuro"}
      title={isDark ? "Modo claro" : "Modo escuro"}
    >
      {isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}
