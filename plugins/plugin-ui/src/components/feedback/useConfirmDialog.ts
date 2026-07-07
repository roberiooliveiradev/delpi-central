import { useCallback, useRef, useState, type ReactNode } from "react";

export type ConfirmDialogOptions = {
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "default" | "danger";
};

export type PendingConfirmDialog = ConfirmDialogOptions & {
  resolve: (confirmed: boolean) => void;
};

export function useConfirmDialogController() {
  const [pending, setPending] = useState<PendingConfirmDialog | null>(null);
  const pendingRef = useRef<PendingConfirmDialog | null>(null);

  const confirm = useCallback((options: ConfirmDialogOptions) => {
    return new Promise<boolean>((resolve) => {
      const next: PendingConfirmDialog = { ...options, resolve };
      pendingRef.current = next;
      setPending(next);
    });
  }, []);

  const settle = useCallback((confirmed: boolean) => {
    const current = pendingRef.current;
    if (!current) return;
    pendingRef.current = null;
    setPending(null);
    current.resolve(confirmed);
  }, []);

  return {
    confirm,
    pending,
    isOpen: pending !== null,
    settle,
    confirmPending: () => settle(true),
    cancelPending: () => settle(false),
  };
}
