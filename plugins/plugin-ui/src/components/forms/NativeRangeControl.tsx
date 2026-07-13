import type { CSSProperties, ChangeEvent } from "react";

import { mergeClassNames } from "./nativeControlClasses";

export const NATIVE_RANGE_CLASS = "delpi-ui-native-range";

export type NativeRangeControlProps = {
  id?: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  className?: string;
  style?: CSSProperties;
  "aria-label"?: string;
  "aria-valuemin"?: number;
  "aria-valuemax"?: number;
  "aria-valuenow"?: number;
};

/**
 * `<input type="range">` canônico — classe `.delpi-ui-native-range` (sem visual de text field).
 * Estilos de fill/thumb ficam no consumidor (ex. ribbon do deck) via `className`.
 */
export function NativeRangeControl({
  id,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  disabled,
  className,
  style,
  "aria-label": ariaLabel,
  "aria-valuemin": ariaValueMin,
  "aria-valuemax": ariaValueMax,
  "aria-valuenow": ariaValueNow,
}: NativeRangeControlProps) {
  return (
    <input
      id={id}
      type="range"
      className={mergeClassNames(NATIVE_RANGE_CLASS, className)}
      min={min}
      max={max}
      step={step}
      value={value}
      disabled={disabled}
      style={style}
      aria-label={ariaLabel}
      aria-valuemin={ariaValueMin ?? min}
      aria-valuemax={ariaValueMax ?? max}
      aria-valuenow={ariaValueNow ?? value}
      onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(Number(event.target.value))}
    />
  );
}
