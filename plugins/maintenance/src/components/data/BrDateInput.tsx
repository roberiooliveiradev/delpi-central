import { useEffect, useState } from "react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { parseBrDateDisplay, toBrDateDisplay } from "../../utils/datetimeLocal";

type BrDateInputProps = {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
  readOnly?: boolean;
  placeholder?: string;
  error?: string;
};

export function BrDateInput({
  value,
  onChange,
  className,
  disabled = false,
  readOnly = false,
  placeholder = "dd/mm/aaaa",
  error,
}: BrDateInputProps) {
  const [display, setDisplay] = useState(() => toBrDateDisplay(value));

  useEffect(() => {
    setDisplay(toBrDateDisplay(value));
  }, [value]);

  function commit(nextDisplay: string) {
    const parsed = parseBrDateDisplay(nextDisplay);
    if (parsed === null) {
      setDisplay(toBrDateDisplay(value));
      return;
    }
    onChange(parsed);
    setDisplay(parsed ? toBrDateDisplay(parsed) : "");
  }

  function handleChange(nextDisplay: string) {
    setDisplay(nextDisplay);
    const parsed = parseBrDateDisplay(nextDisplay);
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
        className={className ?? "dm-br-date-input"}
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
