import { useCallback, useRef, useState, type ReactNode } from "react";

export type ConfirmDialogOptions = {
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Terceira ação — ver `confirmChoice`. */
  secondaryLabel?: string;
  variant?: "default" | "danger";
};

export type ConfirmDialogChoice = "confirm" | "secondary" | "cancel";

export type PendingConfirmDialog = ConfirmDialogOptions & {
  resolve: (choice: ConfirmDialogChoice) => void;
};

export function useConfirmDialogController() {
  const [pending, setPending] = useState<PendingConfirmDialog | null>(null);
  const pendingRef = useRef<PendingConfirmDialog | null>(null);

  const open = useCallback((options: ConfirmDialogOptions) => {
    return new Promise<ConfirmDialogChoice>((resolve) => {
      const next: PendingConfirmDialog = { ...options, resolve };
      pendingRef.current = next;
      setPending(next);
    });
  }, []);

  /** Compatível com callers existentes (`true` = confirm, `false` = cancel). */
  const confirm = useCallback(
    (options: ConfirmDialogOptions) => {
      return open(options).then((choice) => choice === "confirm");
    },
    [open],
  );

  /** Fluxo com 3 saídas (ex.: sair sem salvar / salvar / continuar). */
  const confirmChoice = useCallback(
    (options: ConfirmDialogOptions & { secondaryLabel: string }) => open(options),
    [open],
  );

  const settle = useCallback((choice: ConfirmDialogChoice) => {
    const current = pendingRef.current;
    if (!current) return;
    pendingRef.current = null;
    setPending(null);
    current.resolve(choice);
  }, []);

  return {
    confirm,
    confirmChoice,
    pending,
    isOpen: pending !== null,
    settle,
    confirmPending: () => settle("confirm"),
    secondaryPending: () => settle("secondary"),
    cancelPending: () => settle("cancel"),
  };
}

/** Diálogo canônico de alterações não salvas. */
export function unsavedChangesDialogOptions(message?: ReactNode): ConfirmDialogOptions & {
  secondaryLabel: string;
} {
  return {
    title: "Alterações não salvas",
    message:
      message ??
      "Há alterações que ainda não foram salvas. Deseja salvar antes de sair, descartar ou continuar editando?",
    confirmLabel: "Sair sem salvar",
    secondaryLabel: "Salvar alterações",
    cancelLabel: "Continuar editando",
    variant: "danger",
  };
}
