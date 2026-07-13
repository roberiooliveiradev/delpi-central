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
  isDeckKeyTipFunctionKey,
  type DeckKeyTipMode,
} from "../utils/deckKeyTips";
import { useKeyboardShortcutsTips } from "./KeyboardShortcutsTipsProvider";

type DeckKeyTipsContextValue = {
  mode: DeckKeyTipMode;
  enterTabs: () => void;
  exit: () => void;
  /** true quando balões de ação da ribbon devem aparecer (com Alt). */
  showActionTips: boolean;
};

const DeckKeyTipsContext = createContext<DeckKeyTipsContextValue | null>(null);

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

/**
 * KeyTips do chrome (visual pelo Alt):
 * - Alt (KeyboardShortcutsTipsProvider) revela F1…Fn nas abas e atalhos Ctrl
 * - F1…Fn → ativa a aba e entra no modo de letras das ações
 * - letra/dígito → dispara ação e sai do modo de ações
 * - Esc → sai do modo de ações
 */
export function DeckKeyTipsProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<DeckKeyTipMode>("idle");
  const { altTipsActive } = useKeyboardShortcutsTips();

  const exit = useCallback(() => setMode("idle"), []);
  const enterTabs = useCallback(() => setMode("tabs"), []);

  useEffect(() => {
    if (!altTipsActive) setMode("idle");
  }, [altTipsActive]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (isEditableTarget(event.target)) return;

      if (event.key === "Escape") {
        if (mode === "actions") {
          event.preventDefault();
          setMode("idle");
        }
        return;
      }

      if (isDeckKeyTipFunctionKey(event)) {
        if (event.repeat) return;
        event.preventDefault();
        event.stopPropagation();
        const ok = activateDeckKeyTipTarget("tabs", event.key);
        if (ok) {
          window.requestAnimationFrame(() => setMode("actions"));
        }
        return;
      }

      if (mode !== "actions") return;
      if (!isDeckKeyTipActionKey(event)) return;

      event.preventDefault();
      event.stopPropagation();
      const ok = activateDeckKeyTipTarget("actions", event.key);
      if (ok) setMode("idle");
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
      showActionTips: mode === "actions" && altTipsActive,
    }),
    [altTipsActive, enterTabs, exit, mode],
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
      showActionTips: false,
    };
  }
  return ctx;
}
