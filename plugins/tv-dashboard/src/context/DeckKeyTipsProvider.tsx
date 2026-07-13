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
  activateDeckKeyTipTarget,
  isDeckKeyTipActionKey,
  type DeckKeyTipMode,
} from "../utils/deckKeyTips";

type DeckKeyTipsContextValue = {
  mode: DeckKeyTipMode;
  enterTabs: () => void;
  exit: () => void;
  /** true quando balões de aba devem aparecer. */
  showTabTips: boolean;
  /** true quando balões de ação da ribbon devem aparecer. */
  showActionTips: boolean;
};

const DeckKeyTipsContext = createContext<DeckKeyTipsContextValue | null>(null);

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

function isKeyTipFKey(event: KeyboardEvent): boolean {
  return event.key === "f" || event.key === "F" || event.code === "KeyF";
}

/**
 * KeyTips do chrome (estilo Office):
 * - F → mostra letras das abas
 * - letra → ativa aba e mostra letras das ações
 * - letra → dispara ação e sai
 * - Esc → volta um nível / sai
 */
export function DeckKeyTipsProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<DeckKeyTipMode>("idle");

  const exit = useCallback(() => setMode("idle"), []);
  const enterTabs = useCallback(() => setMode("tabs"), []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (isEditableTarget(event.target)) return;

      if (event.key === "Escape") {
        if (mode === "actions") {
          event.preventDefault();
          setMode("tabs");
          return;
        }
        if (mode === "tabs") {
          event.preventDefault();
          setMode("idle");
        }
        return;
      }

      if (isKeyTipFKey(event) && !event.ctrlKey && !event.metaKey && !event.altKey) {
        if (event.repeat) return;
        event.preventDefault();
        setMode((current) => (current === "idle" ? "tabs" : "idle"));
        return;
      }

      if (mode === "idle") return;
      if (!isDeckKeyTipActionKey(event)) return;

      event.preventDefault();
      event.stopPropagation();

      if (mode === "tabs") {
        const ok = activateDeckKeyTipTarget("tabs", event.key);
        if (ok) {
          // Próximo frame: ribbon da aba já montou.
          window.requestAnimationFrame(() => setMode("actions"));
        }
        return;
      }

      if (mode === "actions") {
        const ok = activateDeckKeyTipTarget("actions", event.key);
        if (ok) setMode("idle");
      }
    }

    function onVisibility() {
      if (document.visibilityState !== "visible") setMode("idle");
    }

    window.addEventListener("keydown", onKeyDown, true);
    window.addEventListener("blur", exit);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("keydown", onKeyDown, true);
      window.removeEventListener("blur", exit);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [exit, mode]);

  const value = useMemo<DeckKeyTipsContextValue>(
    () => ({
      mode,
      enterTabs,
      exit,
      showTabTips: mode === "tabs",
      showActionTips: mode === "actions",
    }),
    [enterTabs, exit, mode],
  );

  return createElement(DeckKeyTipsContext.Provider, { value }, children);
}

export function useDeckKeyTips(): DeckKeyTipsContextValue {
  const ctx = useContext(DeckKeyTipsContext);
  if (!ctx) {
    return {
      mode: "idle",
      enterTabs: () => undefined,
      exit: () => undefined,
      showTabTips: false,
      showActionTips: false,
    };
  }
  return ctx;
}
