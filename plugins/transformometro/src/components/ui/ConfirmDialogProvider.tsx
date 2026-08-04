import {
  createContext,
  useContext,
  useMemo,
  type ReactNode,
} from "react";

import {
  unsavedChangesDialogOptions,
  useConfirmDialogController,
  type ConfirmDialogChoice,
  type ConfirmDialogOptions,
} from "@delpi/plugin-ui/index";

import { ConfirmModal } from "./ConfirmModal";

export type { ConfirmDialogOptions, ConfirmDialogChoice };
export { unsavedChangesDialogOptions };

type ConfirmDialogContextValue = {
  confirm: (options: ConfirmDialogOptions) => Promise<boolean>;
  confirmChoice: (
    options: ConfirmDialogOptions & { secondaryLabel: string },
  ) => Promise<ConfirmDialogChoice>;
};

const ConfirmDialogContext = createContext<ConfirmDialogContextValue | null>(null);

export function ConfirmDialogProvider({ children }: { children: ReactNode }) {
  const {
    confirm,
    confirmChoice,
    pending,
    confirmPending,
    secondaryPending,
    cancelPending,
  } = useConfirmDialogController();

  const value = useMemo(() => ({ confirm, confirmChoice }), [confirm, confirmChoice]);

  return (
    <ConfirmDialogContext.Provider value={value}>
      {children}
      <ConfirmModal
        open={pending !== null}
        title={pending?.title}
        message={pending?.message ?? ""}
        confirmLabel={pending?.confirmLabel}
        cancelLabel={pending?.cancelLabel}
        secondaryLabel={pending?.secondaryLabel}
        variant={pending?.variant}
        onConfirm={confirmPending}
        onCancel={cancelPending}
        onSecondary={pending?.secondaryLabel ? secondaryPending : undefined}
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

export function useConfirmChoice() {
  const context = useContext(ConfirmDialogContext);
  if (!context) {
    throw new Error("useConfirmChoice deve ser usado dentro de ConfirmDialogProvider");
  }
  return context.confirmChoice;
}
