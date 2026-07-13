import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  formatShortcutKeys,
  getKeyboardShortcut,
  type KeyboardShortcutEntry,
} from "../content/keyboardShortcuts";

type KeyboardShortcutsTipsContextValue = {
  altTipsActive: boolean;
  catalogOpen: boolean;
  openCatalog: () => void;
  closeCatalog: () => void;
  getShortcut: (id: string) => KeyboardShortcutEntry | undefined;
  formatKeys: (keys: string) => string;
};

const KeyboardShortcutsTipsContext = createContext<KeyboardShortcutsTipsContextValue | null>(null);

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

export function isAltKey(event: Pick<KeyboardEvent, "key" | "code">): boolean {
  return event.key === "Alt" || event.code === "AltLeft" || event.code === "AltRight";
}

/**
 * Detecta toque em Alt (sem outros modificadores) para ligar/desligar balões de atalho.
 * Esc, blur e troca de aba limpam o modo.
 */
export function KeyboardShortcutsTipsProvider({ children }: { children: ReactNode }) {
  const [altTipsActive, setAltTipsActive] = useState(false);
  const [catalogOpen, setCatalogOpen] = useState(false);

  const clearTips = useCallback(() => setAltTipsActive(false), []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && altTipsActive) {
        setAltTipsActive(false);
        return;
      }

      if (!isAltKey(event)) {
        // Combinação Ctrl/⌘ em uso: esconde os balões.
        if (altTipsActive && (event.ctrlKey || event.metaKey)) {
          setAltTipsActive(false);
        }
        return;
      }
      if (event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (isEditableTarget(event.target)) return;
      if (event.repeat) return;
      // Impede menu do navegador / foco na barra ao tocar Alt (KeyTips).
      event.preventDefault();
      setAltTipsActive((prev) => !prev);
    }

    function onVisibility() {
      if (document.visibilityState !== "visible") clearTips();
    }

    window.addEventListener("keydown", onKeyDown, true);
    window.addEventListener("blur", clearTips);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      window.removeEventListener("keydown", onKeyDown, true);
      window.removeEventListener("blur", clearTips);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [altTipsActive, clearTips]);

  const value = useMemo<KeyboardShortcutsTipsContextValue>(
    () => ({
      altTipsActive,
      catalogOpen,
      openCatalog: () => setCatalogOpen(true),
      closeCatalog: () => setCatalogOpen(false),
      getShortcut: getKeyboardShortcut,
      formatKeys: formatShortcutKeys,
    }),
    [altTipsActive, catalogOpen],
  );

  return createElement(KeyboardShortcutsTipsContext.Provider, { value }, children);
}

export function useKeyboardShortcutsTips(): KeyboardShortcutsTipsContextValue {
  const ctx = useContext(KeyboardShortcutsTipsContext);
  if (!ctx) {
    return {
      altTipsActive: false,
      catalogOpen: false,
      openCatalog: () => undefined,
      closeCatalog: () => undefined,
      getShortcut: getKeyboardShortcut,
      formatKeys: formatShortcutKeys,
    };
  }
  return ctx;
}
