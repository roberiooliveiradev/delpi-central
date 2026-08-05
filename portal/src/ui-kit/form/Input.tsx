// portal/src/ui-kit/form/Input.tsx

import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import "./controls.css";

export type ControlSize = "sm" | "md";

export type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "size"> & {
  size?: ControlSize;
  invalid?: boolean;
  mono?: boolean;
  prefix?: ReactNode;
  suffix?: ReactNode;
};

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  {
    size = "md",
    invalid,
    mono,
    prefix,
    suffix,
    className,
    disabled,
    "aria-invalid": ariaInvalid,
    ...rest
  },
  ref,
) {
  const isInvalid = invalid || ariaInvalid === true || ariaInvalid === "true";
  const controlClass = [
    "portal-ui-control",
    `portal-ui-control--${size}`,
    mono ? "portal-ui-control--mono" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  if (prefix != null || suffix != null) {
    const wrapClass = [
      "portal-ui-control-wrap",
      isInvalid ? "portal-ui-control-wrap--invalid" : "",
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <div className={wrapClass}>
        {prefix != null ? (
          <span className="portal-ui-control-wrap__affix">{prefix}</span>
        ) : null}
        <input
          ref={ref}
          className={controlClass}
          disabled={disabled}
          aria-invalid={isInvalid || undefined}
          {...rest}
        />
        {suffix != null ? (
          <span className="portal-ui-control-wrap__affix portal-ui-control-wrap__affix--suffix">
            {suffix}
          </span>
        ) : null}
      </div>
    );
  }

  return (
    <input
      ref={ref}
      className={controlClass}
      disabled={disabled}
      aria-invalid={isInvalid || undefined}
      {...rest}
    />
  );
});
