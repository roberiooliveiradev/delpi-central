import type { ReactNode } from "react";

import { ensureDelpiUiClass } from "../../utils/delpiUiClass";
import { HelpTooltip } from "./HelpTooltip";

export type FieldLabelProps = {
  label: string;
  hint?: string;
  htmlFor?: string;
  className?: string;
  icon?: ReactNode;
};

/** Rótulo de formulário com ícone de ajuda (HelpTooltip) ao lado do texto. */
export function FieldLabel({ label, hint, htmlFor, className, icon }: FieldLabelProps) {
  const rootClass = ensureDelpiUiClass(className, "delpi-ui-field-label");
  const marked = (
    <>
      {icon ? (
        <span className="delpi-ui-field-label__icon" aria-hidden>
          {icon}
        </span>
      ) : null}
      <span className="delpi-ui-field-label__text">{label}</span>
      {hint != null && hint !== "" ? (
        <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} placement="bottom" />
      ) : null}
    </>
  );

  if (htmlFor) {
    return (
      <label className={rootClass} htmlFor={htmlFor}>
        {marked}
      </label>
    );
  }

  return <span className={rootClass}>{marked}</span>;
}
