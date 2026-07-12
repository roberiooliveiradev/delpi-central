import {
  forwardRef,
  useState,
  type ChangeEvent,
  type FocusEvent,
  type InputHTMLAttributes,
} from "react";

import { NativeTextControl } from "@delpi/plugin-ui/index";

type ChatNativeTextInputProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "onChange" | "type" | "value"
> & {
  type?: "text" | "number" | "url" | "date" | "datetime-local" | "search" | "password" | "month";
  value?: string | number | readonly string[];
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void;
};

/**
 * Adaptador temporário de atributos HTML legados para o contrato string do
 * NativeTextControl. Mantém os consumidores gradualmente migráveis sem
 * reintroduzir controles nativos fora de @delpi/plugin-ui.
 */
export const ChatNativeTextInput = forwardRef<HTMLInputElement, ChatNativeTextInputProps>(
  function ChatNativeTextInput(
    {
      id,
      value,
      defaultValue,
      onChange,
      type = "text",
      placeholder,
      disabled,
      required,
      readOnly,
      min,
      max,
      step,
      maxLength,
      className,
      "aria-label": ariaLabel,
      "aria-invalid": ariaInvalid,
      autoComplete,
      spellCheck,
      inputMode,
      onBlur,
      onFocus,
      onKeyDown,
      onKeyUp,
      autoFocus,
      list,
    },
    ref,
  ) {
    const [uncontrolledValue, setUncontrolledValue] = useState(
      typeof defaultValue === "string" || typeof defaultValue === "number" ? String(defaultValue) : "",
    );
    const resolvedValue =
      typeof value === "string" || typeof value === "number" ? value : uncontrolledValue;

    return (
      <NativeTextControl
        ref={ref}
        id={id}
        type={type}
        value={resolvedValue}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        readOnly={readOnly}
        min={min}
        max={max}
        step={step}
        maxLength={maxLength}
        className={className}
        aria-label={ariaLabel}
        aria-invalid={ariaInvalid === true || ariaInvalid === "true"}
        autoComplete={autoComplete}
        spellCheck={spellCheck === true || spellCheck === "true"}
        inputMode={inputMode}
        onKeyDown={onKeyDown}
        onKeyUp={onKeyUp}
        autoFocus={autoFocus}
        list={list}
        onBlur={() => onBlur?.({} as FocusEvent<HTMLInputElement>)}
        onFocus={() => onFocus?.({} as FocusEvent<HTMLInputElement>)}
        onChange={(nextValue) => {
          if (value === undefined) {
            setUncontrolledValue(nextValue);
          }

          onChange?.({ target: { value: nextValue } } as ChangeEvent<HTMLInputElement>);
        }}
      />
    );
  },
);
