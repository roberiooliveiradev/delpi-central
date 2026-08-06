import {
  createContext,
  useContext,
  useMemo,
  type ReactNode,
} from "react";

import {
  useConfirmDialogController,
  type ConfirmDialogChoice,
  type ConfirmDialogOptions,
} from "@delpi/plugin-ui/index";

import { CommercialConfirmModal } from "./CommercialConfirmModal";

export type { ConfirmDialogOptions, ConfirmDialogChoice };

type ConfirmDialogContextValue = {
  confirm: (options: ConfirmDialogOptions) => Promise<boolean>;
  confirmChoice: (
    options: ConfirmDialogOptions & { secondaryLabel: string },
  ) => Promise<ConfirmDialogChoice>;
};

const ConfirmDialogContext = createContext<ConfirmDialogContextValue | null>(null);

export function CommercialConfirmDialogProvider({ children }: { children: ReactNode }) {
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
      <CommercialConfirmModal
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

export function useCommercialConfirm() {
  const context = useContext(ConfirmDialogContext);
  if (!context) {
    throw new Error("useCommercialConfirm deve ser usado dentro de CommercialConfirmDialogProvider");
  }
  return context.confirm;
}
