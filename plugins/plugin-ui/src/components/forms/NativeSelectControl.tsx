import type { ChangeEvent, CSSProperties, PointerEventHandler } from "react";

import {
  mergeClassNames,
  NATIVE_CONTROL_CLASS,
  NATIVE_CONTROL_SELECT_CLASS,
} from "./nativeControlClasses";

export type NativeSelectOption = {
  value: string;
  label: string;
};

export type NativeSelectControlProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly NativeSelectOption[];
  placeholderOption?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  style?: CSSProperties;
  tabIndex?: number;
  "aria-label"?: string;
  onPointerDown?: PointerEventHandler<HTMLSelectElement>;
};

/**
 * `<select>` nativo compacto (sem FormFieldShell) — visual canônico `.delpi-ui-native-control`.
 */
export function NativeSelectControl({
  id,
  value,
  onChange,
  options,
  placeholderOption,
  disabled,
  required,
  className,
  style,
  tabIndex,
  "aria-label": ariaLabel,
  onPointerDown,
}: NativeSelectControlProps) {
  return (
    <select
      id={id}
      className={mergeClassNames(NATIVE_CONTROL_CLASS, NATIVE_CONTROL_SELECT_CLASS, className)}
      style={style}
      tabIndex={tabIndex}
      value={value}
      disabled={disabled}
      required={required}
      aria-label={ariaLabel}
      onPointerDown={onPointerDown}
      onChange={(event: ChangeEvent<HTMLSelectElement>) => onChange(event.target.value)}
    >
      {placeholderOption !== undefined ? <option value="">{placeholderOption}</option> : null}
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
