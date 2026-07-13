import {
  createContext,
  useContext,
  useEffect,
  type ReactNode,
} from "react";
import {
  configureExportAlert,
  useNoticeDialogController,
  type NoticeDialogOptions,
} from "@delpi/plugin-ui/index";

import { ConfirmModal } from "../components/ui/ConfirmModal";

export type { NoticeDialogOptions };

type NoticeDialogContextValue = {
  notice: (options: NoticeDialogOptions | string) => Promise<void>;
};

const NoticeDialogContext = createContext<NoticeDialogContextValue | null>(null);

/**
 * Substitui window.alert / exportAlert por modal Delpi (plugin-ui).
 * Ligar `configureExportAlert` no mount para `tvDashboardNotice` e exports.
 */
export function NoticeDialogProvider({ children }: { children: ReactNode }) {
  const { notice, pending, dismiss } = useNoticeDialogController();

  useEffect(() => {
    configureExportAlert((message) => {
      void notice({ title: "Aviso", message, confirmLabel: "OK" });
    });
  }, [notice]);

  const title =
    pending?.title ??
    (pending?.variant === "error"
      ? "Erro"
      : pending?.variant === "success"
        ? "Sucesso"
        : "Aviso");

  return (
    <NoticeDialogContext.Provider value={{ notice }}>
      {children}
      <ConfirmModal
        open={pending !== null}
        title={title}
        message={pending?.message ?? ""}
        confirmLabel={pending?.confirmLabel ?? "OK"}
        showCancel={false}
        variant={pending?.variant === "error" ? "danger" : "default"}
        onConfirm={dismiss}
        onCancel={dismiss}
      />
    </NoticeDialogContext.Provider>
  );
}

export function useNotice() {
  const context = useContext(NoticeDialogContext);
  if (!context) {
    throw new Error("useNotice deve ser usado dentro de NoticeDialogProvider");
  }
  return context.notice;
}
