import {
  forwardRef,
  type ChangeEvent,
  type TextareaHTMLAttributes,
} from "react";

export type NativeTextAreaControlProps = {
  value: string;
  onChange: (value: string) => void;
  /** Evento nativo — selectionStart, preventDefault composto, etc. */
  onChangeEvent?: (event: ChangeEvent<HTMLTextAreaElement>) => void;
} & Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "onChange" | "value" | "defaultValue" | "children">;

/**
 * `<textarea>` nativo compacto (sem FormFieldShell) — editores de domínio (composer, canvas, Mermaid).
 */
export const NativeTextAreaControl = forwardRef<HTMLTextAreaElement, NativeTextAreaControlProps>(
  function NativeTextAreaControl({ value, onChange, onChangeEvent, ...rest }, ref) {
    return (
      <textarea
        ref={ref}
        {...rest}
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
          onChangeEvent?.(event);
        }}
      />
    );
  },
);
