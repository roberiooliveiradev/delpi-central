import {
  createContext,
  useCallback,
  useContext,
  type ReactNode,
} from "react";
import {
  createFloatingNoticeStack,
  useFloatingNotices,
  type FloatingNoticeInput,
} from "@delpi/plugin-ui/index";

type FloatingNoticeContextValue = {
  /** Empilha aviso flutuante (substitui item com o mesmo `id`). */
  notice: (input: FloatingNoticeInput | string) => string;
};

const FloatingNoticeContext = createContext<FloatingNoticeContextValue | null>(null);

const TransformometroFloatingNotices = createFloatingNoticeStack({
  prefix: "ds",
  portalScopeClassName: "dashboard-transformometro",
  labels: {
    stackAriaLabel: "Avisos",
    dismissAriaLabel: "Fechar aviso",
  },
});

/**
 * Toasts flutuantes do Transformômetro (`FloatingNoticeStack` do kit).
 * Sucesso/info fecham sozinhos; erro/aviso permanecem até dismiss.
 */
export function FloatingNoticeProvider({ children }: { children: ReactNode }) {
  const { items, push, dismiss } = useFloatingNotices();

  const notice = useCallback(
    (input: FloatingNoticeInput | string) => push(input),
    [push],
  );

  return (
    <FloatingNoticeContext.Provider value={{ notice }}>
      {children}
      <TransformometroFloatingNotices items={items} onDismiss={dismiss} />
    </FloatingNoticeContext.Provider>
  );
}

export function useFloatingNotice() {
  const context = useContext(FloatingNoticeContext);
  if (!context) {
    throw new Error("useFloatingNotice deve ser usado dentro de FloatingNoticeProvider");
  }
  return context.notice;
}
