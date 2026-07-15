import { useState, type ReactNode } from "react";
import { X } from "lucide-react";
import { delpiUiClass } from "@delpi/plugin-ui/index";

type StateBoxProps = {
  children: ReactNode;
  variant?: "default" | "error" | "success";
  onDismiss?: () => void;
};

function rootClass(variant: StateBoxProps["variant"], dismissible: boolean): string {
  const local = ["dm-state-box", "dm-state-box--inline"];
  const ui = ["delpi-ui-state-box", "delpi-ui-state-box--inline"];
  if (variant === "error") {
    local.push("dm-state-box--error");
    ui.push("delpi-ui-state-box--error");
  } else if (variant === "success") {
    local.push("dm-state-box--success");
    ui.push("delpi-ui-state-box--success");
  }
  if (dismissible) {
    local.push("dm-state-box--dismissible");
    ui.push("delpi-ui-state-box--dismissible");
  }
  return delpiUiClass(local.join(" "), ui.join(" "));
}

export function StateBox({ children, variant = "default", onDismiss }: StateBoxProps) {
  const [localDismissed, setLocalDismissed] = useState(false);
  const isAlert = variant === "error" || variant === "success";

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

  if (!isAlert) {
    return <p className={rootClass(variant, false)}>{children}</p>;
  }

  return (
    <div className={rootClass(variant, true)} role="status">
      <span className={delpiUiClass("dm-state-box__content", "delpi-ui-state-box__content")}>
        {children}
      </span>
      <button
        type="button"
        className={delpiUiClass("dm-state-box__dismiss", "delpi-ui-state-box__dismiss")}
        onClick={handleDismiss}
        aria-label="Fechar aviso"
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}
