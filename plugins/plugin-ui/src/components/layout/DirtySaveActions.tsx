import type { ReactNode } from "react";
import { Save } from "lucide-react";

import { FormActions, type FormActionsAlign, type FormActionsClassNames } from "./FormActions";
import { shouldShowDirtySave } from "../../utils/valuesEqual";

export type DirtySaveActionsProps = {
  dirty: boolean;
  saving?: boolean;
  onSave: () => void;
  label?: string;
  savingLabel?: string;
  align?: FormActionsAlign;
  className?: string;
  classNames: FormActionsClassNames;
  primaryButtonClassName: string;
  children?: ReactNode;
};

/**
 * Rodapé de salvar alinhado (`FormActions`) — só aparece com alterações (ou enquanto salva).
 */
export function DirtySaveActions({
  dirty,
  saving = false,
  onSave,
  label = "Salvar",
  savingLabel = "Salvando…",
  align = "start",
  className,
  classNames,
  primaryButtonClassName,
  children,
}: DirtySaveActionsProps) {
  if (!shouldShowDirtySave(dirty, saving)) return null;

  return (
    <FormActions align={align} className={className} classNames={classNames}>
      <button
        type="button"
        className={primaryButtonClassName}
        disabled={saving || !dirty}
        onClick={onSave}
      >
        <Save size={16} aria-hidden="true" />
        {saving ? savingLabel : label}
      </button>
      {children}
    </FormActions>
  );
}

export type DashboardDirtySaveActionsProps = Omit<
  DirtySaveActionsProps,
  "classNames" | "primaryButtonClassName"
>;

export function createDashboardDirtySaveActions(config: {
  classNames: FormActionsClassNames;
  primaryButtonClassName: string;
}) {
  return function DashboardDirtySaveActions(props: DashboardDirtySaveActionsProps) {
    return (
      <DirtySaveActions
        classNames={config.classNames}
        primaryButtonClassName={config.primaryButtonClassName}
        {...props}
      />
    );
  };
}
