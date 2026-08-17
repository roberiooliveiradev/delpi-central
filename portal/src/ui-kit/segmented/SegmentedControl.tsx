// portal/src/ui-kit/segmented/SegmentedControl.tsx

import type { HTMLAttributes } from "react";
import "./SegmentedControl.css";

export type SegmentedOption<T extends string = string> = {
  value: T;
  label: string;
  disabled?: boolean;
};

export type SegmentedControlProps<T extends string = string> = Omit<
  HTMLAttributes<HTMLDivElement>,
  "onChange"
> & {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
};

export function SegmentedControl<T extends string = string>({
  options,
  value,
  onChange,
  className,
  ...rest
}: SegmentedControlProps<T>) {
  const classes = ["portal-ui-segmented", className ?? ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} role="group" {...rest}>
      {options.map((opt) => {
        const active = opt.value === value;
        const optClass = [
          "portal-ui-segmented__option",
          active ? "portal-ui-segmented__option--active" : "",
        ]
          .filter(Boolean)
          .join(" ");

        return (
          <button
            key={opt.value}
            type="button"
            className={optClass}
            aria-pressed={active}
            disabled={opt.disabled}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
