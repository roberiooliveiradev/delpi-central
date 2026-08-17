import { useState } from "react";
import { formatQuantity, parseQuantityInput, roundQuantity } from "../format";

type Props = {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  ariaLabel: string;
};

function clampQuantity(value: number, min?: number, max?: number): number {
  let next = value;
  if (max != null && Number.isFinite(max)) next = Math.min(next, max);
  if (min != null && Number.isFinite(min)) next = Math.max(next, min);
  return roundQuantity(next);
}

export function QuantityInput({ value, onChange, min, max, ariaLabel }: Props) {
  const [focused, setFocused] = useState(false);
  const [draft, setDraft] = useState("");

  function commit(raw: string) {
    const parsed = parseQuantityInput(raw);
    if (!Number.isFinite(parsed)) return;
    onChange(clampQuantity(parsed, min, max));
  }

  return (
    <input
      type="text"
      inputMode="decimal"
      aria-label={ariaLabel}
      value={focused ? draft : formatQuantity(value)}
      onFocus={() => {
        setFocused(true);
        setDraft(formatQuantity(value));
      }}
      onChange={(event) => {
        const raw = event.target.value;
        setDraft(raw);
        commit(raw);
      }}
      onBlur={() => {
        setFocused(false);
        commit(draft);
      }}
    />
  );
}
