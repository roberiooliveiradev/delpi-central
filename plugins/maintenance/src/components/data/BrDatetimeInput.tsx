import { useEffect, useState } from "react";

import { parseBrDatetimeDisplay, toBrDatetimeDisplay } from "../../utils/datetimeLocal";

type BrDatetimeInputProps = {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
  readOnly?: boolean;
  placeholder?: string;
};

export function BrDatetimeInput({
  value,
  onChange,
  className,
  disabled = false,
  readOnly = false,
  placeholder = "dd/mm/aaaa HH:mm",
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

  return (
    <input
      type="text"
      inputMode="numeric"
      autoComplete="off"
      spellCheck={false}
      className={className ?? "dm-br-datetime-input"}
      placeholder={placeholder}
      value={display}
      disabled={disabled}
      readOnly={readOnly}
      onChange={(event) => setDisplay(event.target.value)}
      onBlur={(event) => commit(event.target.value)}
    />
  );
}
