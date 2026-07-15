import { useState, type ReactNode } from "react";
import { X } from "lucide-react";

type StateBoxProps = {
  children: ReactNode;
  variant?: "default" | "error" | "success";
  onDismiss?: () => void;
};

export function StateBox({ children, variant = "default", onDismiss }: StateBoxProps) {
  const [localDismissed, setLocalDismissed] = useState(false);
  const isAlert = variant === "error" || variant === "success";

  if (localDismissed) {
    return null;
  }

  const className =
    variant === "error"
      ? "dm-state-box dm-state-box--error"
      : variant === "success"
        ? "dm-state-box dm-state-box--success"
        : "dm-state-box";

  function handleDismiss() {
    if (onDismiss) {
      onDismiss();
      return;
    }
    setLocalDismissed(true);
  }

  if (!isAlert) {
    return <p className={className}>{children}</p>;
  }

  return (
    <div className={`${className} dm-state-box--dismissible`} role="status">
      <span className="dm-state-box__content">{children}</span>
      <button
        type="button"
        className="dm-state-box__dismiss"
        onClick={handleDismiss}
        aria-label="Fechar aviso"
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}
