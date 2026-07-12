import {
  forwardRef,
  type ChangeEvent,
  type TextareaHTMLAttributes,
} from "react";

import {
  mergeClassNames,
  NATIVE_CONTROL_CLASS,
  NATIVE_CONTROL_TEXTAREA_CLASS,
} from "./nativeControlClasses";

export type NativeTextAreaControlProps = {
  value: string;
  onChange: (value: string) => void;
  /** Evento nativo — selectionStart, preventDefault composto, etc. */
  onChangeEvent?: (event: ChangeEvent<HTMLTextAreaElement>) => void;
} & Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange" | "value" | "defaultValue" | "children">;

/**
 * `<textarea>` nativo compacto (sem FormFieldShell) — visual canônico `.delpi-ui-native-control`.
 */
export const NativeTextAreaControl = forwardRef<HTMLTextAreaElement, NativeTextAreaControlProps>(
  function NativeTextAreaControl({ value, onChange, onChangeEvent, className, ...rest }, ref) {
    return (
      <textarea
        ref={ref}
        {...rest}
        className={mergeClassNames(NATIVE_CONTROL_CLASS, NATIVE_CONTROL_TEXTAREA_CLASS, className)}
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          onChangeEvent?.(event);
        }}
      />
    );
  },
);
