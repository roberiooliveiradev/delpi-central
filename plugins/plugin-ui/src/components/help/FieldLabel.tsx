import { ensureDelpiUiClass } from "../../utils/delpiUiClass";
import { HelpTooltip } from "./HelpTooltip";

export type FieldLabelProps = {
  label: string;
  hint?: string;
  htmlFor?: string;
  className?: string;
};

/** Rótulo de formulário com balão de ajuda no hover do próprio texto. */
export function FieldLabel({ label, hint, htmlFor, className }: FieldLabelProps) {
  const rootClass = ensureDelpiUiClass(className, "delpi-ui-field-label");
  const labelText =
    hint != null && hint !== "" ? (
      <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} wrap placement="bottom">
        <span className="delpi-ui-field-label__text">{label}</span>
      </HelpTooltip>
    ) : (
      label
    );

  if (htmlFor) {
    return (
      <label className={rootClass} htmlFor={htmlFor}>
        {labelText}
      </label>
    );
  }

  return <span className={rootClass}>{labelText}</span>;
}
