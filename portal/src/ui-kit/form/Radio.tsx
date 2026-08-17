// portal/src/ui-kit/form/Radio.tsx

import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import "./RadioGroup.css";

export type RadioProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "size"
> & {
  label?: ReactNode;
};

/** Rádio avulso — para linhas de tabela e layouts em que o `RadioGroup`
 *  não pode envolver as opções. Em formulários, prefira `RadioGroup`. */
export const Radio = forwardRef<HTMLInputElement, RadioProps>(function Radio(
  { label, className, disabled, ...rest },
  ref,
) {
  const classes = [
    "portal-ui-radio",
    disabled ? "portal-ui-radio--disabled" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <label className={classes}>
      <input
        ref={ref}
        type="radio"
        className="portal-ui-radio__input"
        disabled={disabled}
        {...rest}
      />
      <span className="portal-ui-radio__dot" aria-hidden="true" />
      {label != null ? <span>{label}</span> : null}
    </label>
  );
});
