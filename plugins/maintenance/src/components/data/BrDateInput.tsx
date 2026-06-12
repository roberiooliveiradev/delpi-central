import { useEffect, useState } from "react";

import { parseBrDateDisplay, toBrDateDisplay } from "../../utils/datetimeLocal";

type BrDateInputProps = {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
  readOnly?: boolean;
  placeholder?: string;
};

export function BrDateInput({
  value,
  onChange,
  className,
  disabled = false,
  readOnly = false,
  placeholder = "dd/mm/aaaa",
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

  return (
    <input
      type="text"
      inputMode="numeric"
      autoComplete="off"
      spellCheck={false}
      className={className ?? "dm-br-date-input"}
      placeholder={placeholder}
      value={display}
      disabled={disabled}
      readOnly={readOnly}
      onChange={(event) => setDisplay(event.target.value)}
      onBlur={(event) => commit(event.target.value)}
    />
  );
}
