import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ConfirmDialog } from "./ConfirmDialog";

export type ConfirmDialogRequest = {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
};

export type AlertDialogRequest = {
  title?: string;
  message: string;
  okText?: string;
};

type DialogContextValue = {
  confirm: (request: ConfirmDialogRequest) => Promise<boolean>;
  alert: (request: AlertDialogRequest) => Promise<void>;
};

const DialogContext = createContext<DialogContextValue | null>(null);

type PendingDialog =
  | {
      kind: "confirm";
      request: ConfirmDialogRequest;
      resolve: (value: boolean) => void;
    }
  | {
      kind: "alert";
      request: AlertDialogRequest;
      resolve: () => void;
    };

export function ConfirmDialogProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<PendingDialog | null>(null);
  const pendingRef = useRef<PendingDialog | null>(null);

  const settle = useCallback((next: PendingDialog | null) => {
    pendingRef.current = next;
    setPending(next);
  }, []);

  const confirm = useCallback((request: ConfirmDialogRequest) => {
    return new Promise<boolean>((resolve) => {
      settle({ kind: "confirm", request, resolve });
    });
  }, [settle]);

  const alert = useCallback((request: AlertDialogRequest) => {
    return new Promise<void>((resolve) => {
      settle({ kind: "alert", request, resolve });
    });
  }, [settle]);

  const close = useCallback(() => {
    const current = pendingRef.current;
    if (!current) return;
    if (current.kind === "confirm") {
      current.resolve(false);
    } else {
      current.resolve();
    }
    settle(null);
  }, [settle]);

  const handleConfirm = useCallback(() => {
    const current = pendingRef.current;
    if (!current) return;
    if (current.kind === "confirm") {
      current.resolve(true);
    } else {
      current.resolve();
    }
    settle(null);
  }, [settle]);

  const value = useMemo(() => ({ confirm, alert }), [confirm, alert]);

  const dialogProps =
    pending?.kind === "confirm"
      ? {
          open: true,
          title: pending.request.title ?? "Confirmar ação",
          message: pending.request.message,
          confirmText: pending.request.confirmText ?? "Confirmar",
          cancelText: pending.request.cancelText ?? "Cancelar",
          danger: pending.request.danger ?? true,
          showCancel: true,
        }
      : pending?.kind === "alert"
        ? {
            open: true,
            title: pending.request.title ?? "Aviso",
            message: pending.request.message,
            confirmText: pending.request.okText ?? "Entendi",
            cancelText: "Fechar",
            danger: false,
            showCancel: false,
          }
        : null;

  return (
    <DialogContext.Provider value={value}>
      {children}
      {dialogProps ? (
        <ConfirmDialog
          open={dialogProps.open}
          title={dialogProps.title}
          message={dialogProps.message}
          confirmText={dialogProps.confirmText}
          cancelText={dialogProps.cancelText}
          danger={dialogProps.danger}
          showCancel={dialogProps.showCancel}
          onCancel={close}
          onConfirm={handleConfirm}
        />
      ) : null}
    </DialogContext.Provider>
  );
}

function useDialogContext() {
  const context = useContext(DialogContext);
  if (!context) {
    throw new Error("useConfirmDialog/useAppAlert must be used within ConfirmDialogProvider");
  }
  return context;
}

export function useConfirmDialog() {
  return useDialogContext().confirm;
}

export function useAppAlert() {
  return useDialogContext().alert;
}
