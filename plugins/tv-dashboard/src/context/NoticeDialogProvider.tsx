import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  type ReactNode,
} from "react";
import {
  configureExportAlert,
  createFloatingNoticeStack,
  useFloatingNotices,
  type FloatingNoticeVariant,
  type NoticeDialogOptions,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";

export type { NoticeDialogOptions };

type NoticeDialogContextValue = {
  notice: (options: NoticeDialogOptions | string) => Promise<void>;
};

const NoticeDialogContext = createContext<NoticeDialogContextValue | null>(null);

const TvDashboardFloatingNotices = createFloatingNoticeStack({
  prefix: "td",
  portalScopeClassName: TV_DASHBOARD_ROOT_CLASS,
  labels: {
    stackAriaLabel: "Avisos",
    dismissAriaLabel: "Fechar aviso",
  },
});

function mapNoticeVariant(
  variant: NoticeDialogOptions["variant"],
): FloatingNoticeVariant {
  if (variant === "error") return "error";
  if (variant === "success") return "success";
  return "info";
}

/**
 * Avisos não bloqueantes: `FloatingNoticeStack` no topo (plugin-ui).
 * Sucesso/info fecham sozinhos; erro permanece até o usuário fechar.
 * Confirmações destrutivas continuam em `ConfirmModal` / `useConfirm`.
 */
export function NoticeDialogProvider({ children }: { children: ReactNode }) {
  const { items, push, dismiss } = useFloatingNotices();

  const notice = useCallback(
    (options: NoticeDialogOptions | string) => {
      const normalized: NoticeDialogOptions =
        typeof options === "string" ? { message: options } : options;
      push({
        message: normalized.message,
        title: normalized.title,
        variant: mapNoticeVariant(normalized.variant),
      });
      return Promise.resolve();
    },
    [push],
  );

  useEffect(() => {
    configureExportAlert((message) => {
      void notice(message);
    });
  }, [notice]);

  return (
    <NoticeDialogContext.Provider value={{ notice }}>
      {children}
      <TvDashboardFloatingNotices items={items} onDismiss={dismiss} />
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
