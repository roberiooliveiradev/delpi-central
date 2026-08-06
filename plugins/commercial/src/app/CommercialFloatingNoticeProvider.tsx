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

import { UI_PREFIX } from "./commercialUi";

const FORM_VALIDATION_NOTICE_ID = "cm-form-validation";
const PAGE_ERROR_NOTICE_ID = "cm-page-error";
const PAGE_SUCCESS_NOTICE_ID = "cm-page-success";

/** Toast de validação de formulário (temporário). */
export const FORM_VALIDATION_AUTO_DISMISS_MS = 6500;

type CommercialFloatingNoticeContextValue = {
  notice: (input: FloatingNoticeInput | string) => string;
  notifySuccess: (message: string, options?: { title?: string; id?: string }) => string;
  notifyError: (
    message: string,
    options?: { title?: string; id?: string; autoDismissMs?: number | null },
  ) => string;
  /**
   * Campos obrigatórios faltando — toast flutuante temporário.
   * Retorna `false` se houver faltantes (para early-return no submit).
   */
  notifyMissingRequired: (fieldLabels: string[]) => boolean;
  dismiss: (id: string) => void;
};

const CommercialFloatingNoticeContext =
  createContext<CommercialFloatingNoticeContextValue | null>(null);

const CommercialFloatingNotices = createFloatingNoticeStack({
  prefix: UI_PREFIX,
  portalScopeClassName: "dashboard-commercial",
  labels: {
    stackAriaLabel: "Avisos do Comercial",
    dismissAriaLabel: "Fechar aviso",
  },
});

export function formatMissingRequiredMessage(fieldLabels: string[]): string {
  const labels = fieldLabels.map((label) => label.trim()).filter(Boolean);
  if (labels.length === 0) return "Preencha os campos obrigatórios.";
  if (labels.length === 1) {
    return `Informe o campo obrigatório: ${labels[0]}.`;
  }
  if (labels.length === 2) {
    return `Preencha os campos obrigatórios: ${labels[0]} e ${labels[1]}.`;
  }
  const head = labels.slice(0, -1).join(", ");
  const last = labels[labels.length - 1];
  return `Preencha os campos obrigatórios: ${head} e ${last}.`;
}

export function CommercialFloatingNoticeProvider({ children }: { children: ReactNode }) {
  const { items, push, dismiss } = useFloatingNotices();

  const notice = useCallback(
    (input: FloatingNoticeInput | string) => {
      if (typeof input === "string") {
        return push({ message: input, variant: "error" });
      }
      return push({ variant: "error", ...input });
    },
    [push],
  );

  const notifySuccess = useCallback(
    (message: string, options?: { title?: string; id?: string }) =>
      notice({
        id: options?.id ?? PAGE_SUCCESS_NOTICE_ID,
        variant: "success",
        title: options?.title ?? "Pronto",
        message,
      }),
    [notice],
  );

  const notifyError = useCallback(
    (
      message: string,
      options?: { title?: string; id?: string; autoDismissMs?: number | null },
    ) =>
      notice({
        id: options?.id ?? PAGE_ERROR_NOTICE_ID,
        variant: "error",
        title: options?.title ?? "Não foi possível concluir",
        message,
        autoDismissMs: options?.autoDismissMs,
      }),
    [notice],
  );

  const notifyMissingRequired = useCallback(
    (fieldLabels: string[]) => {
      const missing = fieldLabels.map((label) => label.trim()).filter(Boolean);
      if (missing.length === 0) return true;
      notice({
        id: FORM_VALIDATION_NOTICE_ID,
        variant: "error",
        title: "Campos obrigatórios",
        message: formatMissingRequiredMessage(missing),
        autoDismissMs: FORM_VALIDATION_AUTO_DISMISS_MS,
      });
      return false;
    },
    [notice],
  );

  return (
    <CommercialFloatingNoticeContext.Provider
      value={{ notice, notifySuccess, notifyError, notifyMissingRequired, dismiss }}
    >
      {children}
      <CommercialFloatingNotices items={items} onDismiss={dismiss} />
    </CommercialFloatingNoticeContext.Provider>
  );
}

export function useCommercialFloatingNotice(): CommercialFloatingNoticeContextValue {
  const context = useContext(CommercialFloatingNoticeContext);
  if (!context) {
    throw new Error(
      "useCommercialFloatingNotice deve ser usado dentro de CommercialFloatingNoticeProvider.",
    );
  }
  return context;
}

export {
  FORM_VALIDATION_NOTICE_ID,
  PAGE_ERROR_NOTICE_ID,
  PAGE_SUCCESS_NOTICE_ID,
};
