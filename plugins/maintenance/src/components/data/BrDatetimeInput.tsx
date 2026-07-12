import { useEffect, useState } from "react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { parseBrDatetimeDisplay, toBrDatetimeDisplay } from "../../utils/datetimeLocal";

type BrDatetimeInputProps = {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
  readOnly?: boolean;
  placeholder?: string;
  error?: string;
};

export function BrDatetimeInput({
  value,
  onChange,
  className,
  disabled = false,
  readOnly = false,
  placeholder = "dd/mm/aaaa HH:mm",
  error,
}: BrDatetimeInputProps) {
  const [display, setDisplay] = useState(() => toBrDatetimeDisplay(value));

  useEffect(() => {
    setDisplay(toBrDatetimeDisplay(value));
  }, [value]);

  function commit(nextDisplay: string) {
    const parsed = parseBrDatetimeDisplay(nextDisplay);
    if (parsed === null) {
      setDisplay(toBrDatetimeDisplay(value));
      return;
    }
    onChange(parsed);
    setDisplay(parsed ? toBrDatetimeDisplay(parsed) : "");
  }

  function handleChange(nextDisplay: string) {
    setDisplay(nextDisplay);
    const parsed = parseBrDatetimeDisplay(nextDisplay);
    if (parsed !== null && parsed !== "") {
      onChange(parsed);
    }
  }

  return (
    <>
      <NativeTextControl
        type="text"
        inputMode="numeric"
        autoComplete="off"
        spellCheck={false}
        className={className ?? "dm-br-datetime-input"}
        placeholder={placeholder}
        value={display}
        disabled={disabled}
        readOnly={readOnly}
        aria-invalid={Boolean(error)}
        onChange={handleChange}
        onBlur={() => commit(display)}
      />
      {error ? <span className="dm-field__error">{error}</span> : null}
    </>
  );
}
