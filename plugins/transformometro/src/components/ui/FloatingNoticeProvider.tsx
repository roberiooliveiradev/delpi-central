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

const PAGE_ERROR_NOTICE_ID = "tm-page-error";

type FloatingNoticeContextValue = {
  /** Empilha aviso flutuante (substitui item com o mesmo `id`). */
  notice: (input: FloatingNoticeInput | string) => string;
  /** Sucesso — fecha sozinho (~6s). */
  notifySuccess: (title: string, message: string, id?: string) => string;
  /**
   * Erro — permanece até o usuário fechar (sem barra de auto-dismiss).
   * Usa `id` estável para substituir o aviso anterior.
   */
  notifyError: (
    message: string,
    options?: {
      title?: string;
      id?: string;
      actionLabel?: string;
      onAction?: () => void;
      onClose?: () => void;
    },
  ) => string;
  dismiss: (id: string) => void;
  dismissPageError: () => void;
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
 * Canal único para sucesso e erro: sucesso/info fecham sozinhos;
 * erro/aviso permanecem até o usuário fechar.
 */
export function FloatingNoticeProvider({ children }: { children: ReactNode }) {
  const { items, push, dismiss } = useFloatingNotices();

  const notice = useCallback(
    (input: FloatingNoticeInput | string) => {
      if (typeof input === "string") {
        return push({ message: input, variant: "error", autoDismissMs: null });
      }
      const variant = input.variant ?? "error";
      if (variant === "error" || variant === "warning") {
        return push({ ...input, variant, autoDismissMs: null });
      }
      return push(input);
    },
    [push],
  );

  const notifySuccess = useCallback(
    (title: string, message: string, id = "tm-feedback") =>
      notice({ id, variant: "success", title, message }),
    [notice],
  );

  const notifyError = useCallback(
    (
      message: string,
      options?: {
        title?: string;
        id?: string;
        actionLabel?: string;
        onAction?: () => void;
        onClose?: () => void;
      },
    ) =>
      notice({
        id: options?.id ?? PAGE_ERROR_NOTICE_ID,
        variant: "error",
        title: options?.title ?? "Não foi possível concluir",
        message,
        autoDismissMs: null,
        onClose: options?.onClose,
        action:
          options?.onAction && options.actionLabel
            ? { label: options.actionLabel, onClick: options.onAction }
            : undefined,
      }),
    [notice],
  );

  const dismissPageError = useCallback(() => {
    dismiss(PAGE_ERROR_NOTICE_ID);
  }, [dismiss]);

  return (
    <FloatingNoticeContext.Provider
      value={{ notice, notifySuccess, notifyError, dismiss, dismissPageError }}
    >
      {children}
      <TransformometroFloatingNotices
        items={items}
        onDismiss={dismiss}
        defaultAutoDismissMs={{ error: null, warning: null }}
      />
    </FloatingNoticeContext.Provider>
  );
}

export function useFloatingNotice() {
  const context = useContext(FloatingNoticeContext);
  if (!context) {
    throw new Error("useFloatingNotice deve ser usado dentro de FloatingNoticeProvider");
  }
  return context;
}

export { PAGE_ERROR_NOTICE_ID };
