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

import { isEditableKeyboardTarget, useEditorShortcut } from "../keyboard";
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

/**
 * KeyTips do chrome (visual pelo Alt):
 * - Alt (KeyboardShortcutsTipsProvider) revela F1…Fn nas abas e atalhos Ctrl
 * - Com Alt ativo, F1…Fn → ativa a aba e entra no modo de letras das ações
 * - letra/dígito → dispara ação e sai do modo de ações
 * - Esc → sai do modo de ações
 *
 * Nunca engole F-keys do browser (F5/F11/F12) sem Alt ou sem alvo — handled só se claim.
 */
export function DeckKeyTipsProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<DeckKeyTipMode>("idle");
  const { altTipsActive } = useKeyboardShortcutsTips();

  const exit = useCallback(() => setMode("idle"), []);
  const enterTabs = useCallback(() => setMode("tabs"), []);

  useEffect(() => {
    if (!altTipsActive) setMode("idle");
  }, [altTipsActive]);

  useEditorShortcut(
    "deck-keytips",
    (event) => {
      if (isEditableKeyboardTarget(event.target)) return;

      if (event.key === "Escape") {
        if (mode !== "actions") return;
        setMode("idle");
        return { handled: true };
      }

      // F-keys de aba só com KeyTips (Alt) ativos — libera DevTools (F12), refresh (F5), etc.
      if (isDeckKeyTipFunctionKey(event)) {
        if (!altTipsActive || event.repeat) return;
        const ok = activateDeckKeyTipTarget("tabs", event.key);
        if (!ok) return;
        window.requestAnimationFrame(() => setMode("actions"));
        return { handled: true };
      }

      if (mode !== "actions") return;
      if (!isDeckKeyTipActionKey(event)) return;

      const ok = activateDeckKeyTipTarget("actions", event.key);
      if (!ok) return;
      setMode("idle");
      return { handled: true };
    },
    { phase: "capture", priority: 100 },
  );

  useEffect(() => {
    function onVisibility() {
      if (document.visibilityState !== "visible") setMode("idle");
    }
    window.addEventListener("blur", exit);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("blur", exit);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [exit]);

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
