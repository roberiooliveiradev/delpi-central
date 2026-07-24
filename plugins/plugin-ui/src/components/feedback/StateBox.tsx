import { useState, type ReactNode } from "react";
import { X } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type StateBoxTone = "default" | "error" | "success" | "warning";

export type StateBoxProps = {
  children: ReactNode;
  /** Tom do aviso (default = info neutro). */
  variant?: StateBoxTone;
  className?: string;
  /** Prefixo BEM do plugin (default `ds`). */
  prefix?: string;
  /**
   * Exibe botão fechar. Se omitido em error/success/warning, o aviso
   * permanece até o pai limpar o estado (ou dismiss local).
   */
  onDismiss?: () => void;
  /** Força dismissível mesmo no tom default. */
  dismissible?: boolean;
};

function rootClass(
  prefix: string,
  variant: StateBoxTone,
  dismissible: boolean,
  className?: string,
): string {
  const local = [`${prefix}-state-box`, `${prefix}-state-box--inline`];
  const ui = ["delpi-ui-state-box", "delpi-ui-state-box--inline"];
  if (variant === "error") {
    local.push(`${prefix}-state-box--error`);
    ui.push("delpi-ui-state-box--error");
  } else if (variant === "success") {
    local.push(`${prefix}-state-box--success`);
    ui.push("delpi-ui-state-box--success");
  } else if (variant === "warning") {
    local.push(`${prefix}-state-box--warning`);
    ui.push("delpi-ui-state-box--warning");
  }
  if (dismissible) {
    local.push(`${prefix}-state-box--dismissible`);
    ui.push("delpi-ui-state-box--dismissible");
  }
  return [delpiUiClass(local.join(" "), ui.join(" ")), className].filter(Boolean).join(" ");
}

/**
 * Aviso inline canônico (sucesso / erro / atenção / info).
 * CSS: `.delpi-ui-state-box--inline` (+ tom). MFEs não devem reimplementar o chrome.
 */
export function StateBox({
  children,
  variant = "default",
  className,
  prefix = "ds",
  onDismiss,
  dismissible,
}: StateBoxProps) {
  const [localDismissed, setLocalDismissed] = useState(false);
  const isAlert = variant === "error" || variant === "success" || variant === "warning";
  /** Avisos tonais são dismissíveis por padrão (X); default info só se `dismissible`. */
  const canDismiss = dismissible ?? isAlert;

  if (localDismissed) {
    return null;
  }

  function handleDismiss() {
    if (onDismiss) {
      onDismiss();
      return;
    }
    setLocalDismissed(true);
  }

  const role = variant === "error" ? "alert" : "status";

  if (!canDismiss) {
    return (
      <div className={rootClass(prefix, variant, false, className)} role={role}>
        {children}
      </div>
    );
  }

  return (
    <div className={rootClass(prefix, variant, true, className)} role={role}>
      <span
        className={delpiUiClass(`${prefix}-state-box__content`, "delpi-ui-state-box__content")}
      >
        {children}
      </span>
      <button
        type="button"
        className={delpiUiClass(`${prefix}-state-box__dismiss`, "delpi-ui-state-box__dismiss")}
        onClick={handleDismiss}
        aria-label="Fechar aviso"
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}

export type DashboardStateBoxProps = Omit<StateBoxProps, "prefix">;

export function createDashboardStateBox(config: { prefix: string }) {
  return function DashboardStateBox(props: DashboardStateBoxProps) {
    return <StateBox prefix={config.prefix} {...props} />;
  };
}
