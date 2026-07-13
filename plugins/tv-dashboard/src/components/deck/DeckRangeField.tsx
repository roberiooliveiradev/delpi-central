import { useEffect, useState } from "react";
import { FieldLabel, NativeRangeControl, NativeTextControl } from "@delpi/plugin-ui/index";

type Props = {
  id: string;
  label: string;
  hint?: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  /** Valor exibido no input (quando difere do arredondamento padrão). */
  displayValue?: string;
  "aria-label"?: string;
  className?: string;
};

function formatShown(value: number, displayValue?: string): string {
  if (displayValue != null) return displayValue;
  return String(Math.round(value * 1000) / 1000);
}

function parseAndClamp(raw: string, min: number, max: number, fallback: number): number {
  const num = Number(raw.replace(",", "."));
  if (!Number.isFinite(num)) return fallback;
  return Math.min(max, Math.max(min, num));
}

/**
 * Campo contínuo canônico — rótulo, slider e input numérico abaixo (digitar).
 */
export function DeckRangeField({
  id,
  label,
  hint,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  displayValue,
  "aria-label": ariaLabel,
  className,
}: Props) {
  const safeMax = max === min ? max + 1 : max;
  const clamped = Math.min(safeMax, Math.max(min, value));
  const progress = ((clamped - min) / (safeMax - min)) * 100;
  const shown = formatShown(value, displayValue);
  const [draft, setDraft] = useState(shown);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!editing) setDraft(formatShown(value, displayValue));
  }, [value, displayValue, editing]);

  const commitDraft = () => {
    setEditing(false);
    const next = parseAndClamp(draft, min, max, clamped);
    setDraft(formatShown(next, displayValue));
    if (next !== value) onChange(next);
  };

  return (
    <span
      className={["td-deck-ribbon__frame-field", "td-deck-ribbon__frame-field--range", className]
        .filter(Boolean)
        .join(" ")}
    >
      <FieldLabel
        htmlFor={id}
        label={label}
        hint={hint}
        className="td-deck-ribbon__field-label"
      />
      <span className="td-deck-ribbon__range-row">
        <NativeRangeControl
          id={id}
          className="td-deck-ribbon__range"
          min={min}
          max={max}
          step={step}
          value={clamped}
          aria-label={ariaLabel ?? label}
          style={{ ["--td-range-progress" as string]: `${progress}%` }}
          onChange={(next) => {
            setEditing(false);
            onChange(next);
          }}
        />
        <NativeTextControl
          id={`${id}-num`}
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact td-deck-ribbon__range-input"
          min={min}
          max={max}
          step={step}
          aria-label={`${ariaLabel ?? label} (digitar)`}
          value={draft}
          onFocus={() => setEditing(true)}
          onChange={(raw) => {
            setEditing(true);
            setDraft(raw);
          }}
          onBlur={commitDraft}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              (event.target as HTMLInputElement).blur();
            }
          }}
        />
      </span>
    </span>
  );
}
