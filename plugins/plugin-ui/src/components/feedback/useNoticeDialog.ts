import { useCallback, useRef, useState, type ReactNode } from "react";

export type NoticeDialogOptions = {
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  /** success | error → tipografia do banner no host, se aplicável. */
  variant?: "default" | "success" | "error";
};

export type PendingNoticeDialog = NoticeDialogOptions & {
  resolve: () => void;
};

/** Controlador de avisos (substitui window.alert) — um OK via ModalShell. */
export function useNoticeDialogController() {
  const [pending, setPending] = useState<PendingNoticeDialog | null>(null);
  const pendingRef = useRef<PendingNoticeDialog | null>(null);

  const notice = useCallback((options: NoticeDialogOptions | string) => {
    const normalized: NoticeDialogOptions =
      typeof options === "string" ? { message: options } : options;
    return new Promise<void>((resolve) => {
      const next: PendingNoticeDialog = { ...normalized, resolve };
      pendingRef.current = next;
      setPending(next);
    });
  }, []);

  const dismiss = useCallback(() => {
    const current = pendingRef.current;
    if (!current) return;
    pendingRef.current = null;
    setPending(null);
    current.resolve();
  }, []);

  return {
    notice,
    pending,
    isOpen: pending !== null,
    dismiss,
  };
}
