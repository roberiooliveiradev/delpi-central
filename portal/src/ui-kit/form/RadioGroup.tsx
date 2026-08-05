// portal/src/ui-kit/form/RadioGroup.tsx

import { useId, type HTMLAttributes } from "react";
import "./RadioGroup.css";

export type RadioOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

export type RadioGroupProps = Omit<
  HTMLAttributes<HTMLDivElement>,
  "onChange"
> & {
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  name?: string;
  orientation?: "horizontal" | "vertical";
  disabled?: boolean;
};

export function RadioGroup({
  options,
  value,
  onChange,
  name,
  orientation = "vertical",
  disabled,
  className,
  ...rest
}: RadioGroupProps) {
  const autoName = useId();
  const groupName = name ?? autoName;
  const classes = [
    "portal-ui-radio-group",
    orientation === "vertical" ? "portal-ui-radio-group--vertical" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} role="radiogroup" {...rest}>
      {options.map((opt) => {
        const optDisabled = disabled || opt.disabled;
        const optClass = [
          "portal-ui-radio",
          optDisabled ? "portal-ui-radio--disabled" : "",
        ]
          .filter(Boolean)
          .join(" ");

        return (
          <label key={opt.value} className={optClass}>
            <input
              type="radio"
              className="portal-ui-radio__input"
              name={groupName}
              value={opt.value}
              checked={value === opt.value}
              disabled={optDisabled}
              onChange={() => onChange(opt.value)}
            />
            <span className="portal-ui-radio__dot" aria-hidden="true" />
            <span>{opt.label}</span>
          </label>
        );
      })}
    </div>
  );
}
