import type { ReactNode } from "react";
import { Loader2, Save, X } from "lucide-react";

import { PpActionButton, PpHintAction } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";

type CancelButtonProps = {
  onClick: () => void;
  disabled?: boolean;
  label?: string;
  hint?: string;
  className?: string;
};

/** Ghost dismiss/cancel with icon + PpHintAction (form footers and dialogs). */
export function PpCancelButton({
  onClick,
  disabled,
  label = "Cancelar",
  hint = PP_HELP.form.cancel,
  className,
}: CancelButtonProps) {
  return (
    <PpHintAction hint={hint} ariaLabel={`Ajuda: ${label}`}>
      <PpActionButton
        variant="ghost"
        className={className}
        disabled={disabled}
        aria-label={label}
        onClick={onClick}
      >
        <X size={16} aria-hidden />
        {label}
      </PpActionButton>
    </PpHintAction>
  );
}

type SaveButtonProps = {
  onClick: () => void;
  disabled?: boolean;
  busy?: boolean;
  label?: string;
  busyLabel?: string;
  hint?: string;
  variant?: "default" | "primary" | "ghost";
  className?: string;
  icon?: ReactNode;
};

/** Primary/default save with icon + PpHintAction. */
export function PpSaveButton({
  onClick,
  disabled,
  busy = false,
  label = "Salvar",
  busyLabel = "Salvando…",
  hint = PP_HELP.form.save,
  variant = "primary",
  className,
  icon,
}: SaveButtonProps) {
  const text = busy ? busyLabel : label;
  return (
    <PpHintAction hint={hint} ariaLabel={`Ajuda: ${label}`}>
      <PpActionButton
        variant={variant}
        className={className}
        disabled={disabled || busy}
        aria-label={text}
        onClick={onClick}
      >
        {busy ? (
          <Loader2 size={16} aria-hidden className="pp-spin" />
        ) : (
          (icon ?? <Save size={16} aria-hidden />)
        )}
        {text}
      </PpActionButton>
    </PpHintAction>
  );
}
