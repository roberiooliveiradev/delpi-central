import { createContext, useContext, type ReactNode } from "react";
import { useConfirmDialogController, type ConfirmDialogOptions } from "@delpi/plugin-ui/index";

import { PpcConfirmModal } from "./PpcConfirmModal";

export type { ConfirmDialogOptions };

type ConfirmDialogContextValue = {
  confirm: (options: ConfirmDialogOptions) => Promise<boolean>;
};

const ConfirmDialogContext = createContext<ConfirmDialogContextValue | null>(null);

export function PpcConfirmDialogProvider({ children }: { children: ReactNode }) {
  const { confirm, pending, confirmPending, cancelPending } = useConfirmDialogController();

  return (
    <ConfirmDialogContext.Provider value={{ confirm }}>
      {children}
      <PpcConfirmModal
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

export function usePpcConfirm() {
  const context = useContext(ConfirmDialogContext);
  if (!context) {
    throw new Error("usePpcConfirm deve ser usado dentro de PpcConfirmDialogProvider");
  }
  return context.confirm;
}
