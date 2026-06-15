import { ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import type { EficienciaFabrilShift } from "../constants/shifts";
import { FACTORY_SHIFTS } from "../constants/shifts";

type ShiftMultiSelectProps = {
  value: EficienciaFabrilShift[];
  onChange: (value: EficienciaFabrilShift[]) => void;
  disabled?: boolean;
};

function formatShiftLabel(selected: EficienciaFabrilShift[]): string {
  if (selected.length === 0) return "Todos";
  if (selected.length === FACTORY_SHIFTS.length) return "Todos os turnos";

  const labels = FACTORY_SHIFTS.filter((shift) => selected.includes(shift.id)).map(
    (shift) => shift.label
  );
  return labels.join(", ");
}

export function ShiftMultiSelect({
  value,
  onChange,
  disabled = false,
}: ShiftMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

  function toggleShift(shiftId: EficienciaFabrilShift) {
    if (value.includes(shiftId)) {
      onChange(value.filter((item) => item !== shiftId));
      return;
    }
    onChange([...value, shiftId]);
  }

  return (
    <div className="ef-multi-select" ref={rootRef}>
      <button
        type="button"
        className="ef-multi-select__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{formatShiftLabel(value)}</span>
        <ChevronDown size={16} aria-hidden />
      </button>

      {open ? (
        <div className="ef-multi-select__panel" id={listId} role="listbox" aria-multiselectable>
          {FACTORY_SHIFTS.map((shift) => {
            const checked = value.includes(shift.id);
            return (
              <label key={shift.id} className="ef-multi-select__option">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleShift(shift.id)}
                />
                <span>
                  {shift.label} ({shift.start} – {shift.end})
                </span>
              </label>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
