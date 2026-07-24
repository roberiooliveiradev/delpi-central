import type { ReactNode } from "react";
import { AlertTriangle, Inbox, LoaderCircle } from "lucide-react";

import { createStateBoxPanel, type StateBoxVariant } from "@delpi/plugin-ui/index";

/** Painel de estado canônico do kit (`StateBoxPanel` + dual-class `ds` / `delpi-ui`). */
export const ErrorStateBox = createStateBoxPanel({
  prefix: "ds",
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} aria-hidden="true" />;
    if (variant === "empty") return <Inbox size={22} aria-hidden="true" />;
    return <LoaderCircle size={22} aria-hidden="true" />;
  },
});

type InlineErrorStateProps = {
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  /** Fecha o aviso — erros não somem sozinhos com o tempo. */
  onDismiss?: () => void;
};

/** Erro inline com título, detalhe e ação — substitui `StateBox` ad hoc em StatusAlerts. */
export function InlineErrorState({
  title = "Não foi possível concluir",
  message,
  actionLabel = "Tentar novamente",
  onAction,
  onDismiss,
}: InlineErrorStateProps) {
  let action: ReactNode;
  if (onAction) {
    action = (
      <button type="button" className="ds-primary-btn" onClick={onAction}>
        {actionLabel}
      </button>
    );
  }

  return (
    <ErrorStateBox
      variant="error"
      title={title}
      message={message}
      action={action}
      onDismiss={onDismiss}
    />
  );
}
