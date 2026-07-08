import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

type Mode = "light" | "dark";

const STORAGE_KEY = "cx-form-preview-theme";

function systemMode(): Mode {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function storedMode(): Mode | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function initialMode(): Mode {
  return storedMode() ?? systemMode();
}

type PreviewThemeToggleProps = {
  mode: Mode;
  onChange: (mode: Mode) => void;
};

/**
 * Alterna claro/escuro só na prévia do formulário (não altera o tema do portal).
 */
export function PreviewThemeToggle({ mode, onChange }: PreviewThemeToggleProps) {
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const onMediaChange = () => {
      if (!storedMode()) onChange(systemMode());
    };
    mq.addEventListener("change", onMediaChange);
    return () => mq.removeEventListener("change", onMediaChange);
  }, [onChange]);

  const toggle = () => {
    const next: Mode = mode === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* storage indisponível */
    }
    onChange(next);
  };

  const isDark = mode === "dark";

  return (
    <button
      type="button"
      className="cx-form-preview-theme-toggle"
      onClick={toggle}
      aria-label={isDark ? "Ativar modo claro" : "Ativar modo escuro"}
      title={isDark ? "Modo claro" : "Modo escuro"}
    >
      {isDark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

export function usePreviewThemeMode(): [Mode, (mode: Mode) => void] {
  const [mode, setMode] = useState<Mode>(() => initialMode());
  return [mode, setMode];
}
