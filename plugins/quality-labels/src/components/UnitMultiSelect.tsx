import { useEffect, useRef, useState } from "react";
import { ChevronDown, Check } from "lucide-react";

import {
  OPERATIONAL_UNIT_OPTIONS,
  formatOperationalUnit,
} from "../utils/operationalUnits";

type Props = {
  value: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
};

export function UnitMultiSelect({ value, onChange, placeholder = "Todas" }: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  function toggle(code: string) {
    onChange(
      value.includes(code)
        ? value.filter((item) => item !== code)
        : [...value, code],
    );
  }

  const summary =
    value.length === 0
      ? placeholder
      : value.map((code) => formatOperationalUnit(code, code)).join(", ");

  return (
    <div className="ql-multiselect" ref={rootRef}>
      <button
        type="button"
        className="ql-input ql-multiselect__trigger"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className={value.length === 0 ? "ql-multiselect__placeholder" : ""}>
          {summary}
        </span>
        <ChevronDown className="ql-icon" />
      </button>
      {open && (
        <div className="ql-multiselect__menu">
          {OPERATIONAL_UNIT_OPTIONS.map((opt) => {
            const checked = value.includes(opt.value);
            return (
              <button
                key={opt.value}
                type="button"
                className="ql-multiselect__option"
                onClick={() => toggle(opt.value)}
              >
                <span className={`ql-checkbox ${checked ? "is-checked" : ""}`}>
                  {checked && <Check className="ql-icon" />}
                </span>
                {opt.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
