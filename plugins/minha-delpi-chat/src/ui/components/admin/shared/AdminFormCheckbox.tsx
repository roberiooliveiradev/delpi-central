import type { InputHTMLAttributes, ReactNode } from "react";

type AdminFormCheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  title: ReactNode;
  hint?: ReactNode;
  className?: string;
};

export function AdminFormCheckbox({
  title,
  hint,
  className,
  ...inputProps
}: AdminFormCheckboxProps) {
  return (
    <label className={["mdc-admin-form-row", className].filter(Boolean).join(" ")}>
      <input type="checkbox" {...inputProps} />
      <span className="mdc-admin-form-row__copy">
        <span className="mdc-admin-form-row__title">{title}</span>
        {hint ? <span className="mdc-admin-form-row__hint">{hint}</span> : null}
      </span>
    </label>
  );
}
