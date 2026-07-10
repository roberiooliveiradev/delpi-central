import {
  createContext,
  useContext,
  type ReactNode,
} from "react";

import { useConfirmDialogController, type ConfirmDialogOptions } from "@delpi/plugin-ui/index";

import { ConfirmModal } from "./ConfirmModal";

export type { ConfirmDialogOptions };

type ConfirmDialogContextValue = {
  confirm: (options: ConfirmDialogOptions) => Promise<boolean>;
};

const ConfirmDialogContext = createContext<ConfirmDialogContextValue | null>(null);

export function ConfirmDialogProvider({ children }: { children: ReactNode }) {
  const { confirm, pending, confirmPending, cancelPending } = useConfirmDialogController();

  return (
    <ConfirmDialogContext.Provider value={{ confirm }}>
      {children}
      <ConfirmModal
        open={pending !== null}
        title={pending?.title}
        message={pending?.message ?? ""}
        confirmLabel={pending?.confirmLabel}
        cancelLabel={pending?.cancelLabel}
        variant={pending?.variant}
        onConfirm={confirmPending}
        onCancel={cancelPending}
      />
    </ConfirmDialogContext.Provider>
  );
}

export function useConfirm() {
  const context = useContext(ConfirmDialogContext);
  if (!context) {
    throw new Error("useConfirm deve ser usado dentro de ConfirmDialogProvider");
  }
  return context.confirm;
}
