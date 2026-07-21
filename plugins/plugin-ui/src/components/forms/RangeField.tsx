import { useEffect, useState } from "react";

import { FieldLabel } from "../help/FieldLabel";
import { mergeClassNames, NATIVE_CONTROL_CLASS, NATIVE_CONTROL_COMPACT_CLASS } from "./nativeControlClasses";
import { NativeRangeControl } from "./NativeRangeControl";
import { NativeTextControl } from "./NativeTextControl";

export const RANGE_FIELD_CLASS = "delpi-ui-range-field";

export type RangeFieldProps = {
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
  /**
   * `compact` — só rótulo + input (sem slider). Popovers / inspetor denso.
   * `full` — slider + input. Na ribbon do deck a largura é estreita via host-density (~96px).
   */
  density?: "full" | "compact";
  "aria-label"?: string;
  className?: string;
};

function formatShown(value: number, displayValue?: string): string {
  if (displayValue != null) return displayValue;
  return String(Math.round(value * 1000) / 1000);
}

/** Extrai número de rascunhos com vírgula, sufixo % etc. (ex.: "80%", "595,2"). */
export function parseRangeFieldNumber(raw: string): number | null {
  const normalized = raw.trim().replace(/\s/g, "").replace(",", ".");
  const match = normalized.match(/-?\d+(?:\.\d+)?/);
  if (!match) return null;
  const num = Number(match[0]);
  return Number.isFinite(num) ? num : null;
}

function parseAndClamp(raw: string, min: number, max: number, fallback: number): number {
  const num = parseRangeFieldNumber(raw);
  if (num == null) return fallback;
  return Math.min(max, Math.max(min, num));
}

function isNegativeShown(raw: string, value: number): boolean {
  const parsed = parseRangeFieldNumber(raw);
  if (parsed != null) return parsed < 0;
  return value < 0;
}

/**
 * Campo contínuo canônico — rótulo, slider e input numérico abaixo (digitar).
 * Classes: `.delpi-ui-range-field` (+ `__slider`, `__input`, `__input--negative`).
 */
export function RangeField({
  id,
  label,
  hint,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  displayValue,
  density = "full",
  "aria-label": ariaLabel,
  className,
}: RangeFieldProps) {
  const safeMax = max === min ? max + 1 : max;
  const clamped = Math.min(safeMax, Math.max(min, value));
  const progress = ((clamped - min) / (safeMax - min)) * 100;
  const shown = formatShown(value, displayValue);
  const [draft, setDraft] = useState(shown);
  const [editing, setEditing] = useState(false);
  const negative = isNegativeShown(draft, value);
  const compact = density === "compact";

  useEffect(() => {
    if (!editing) setDraft(formatShown(value, displayValue));
  }, [value, displayValue, editing]);

  const commitDraft = () => {
    setEditing(false);
    const next = parseAndClamp(draft, min, max, clamped);
    if (next !== value) {
      onChange(next);
      return;
    }
    setDraft(formatShown(value, displayValue));
  };

  return (
    <span
      className={mergeClassNames(
        RANGE_FIELD_CLASS,
        compact ? `${RANGE_FIELD_CLASS}--compact` : null,
        negative ? `${RANGE_FIELD_CLASS}--negative` : null,
        className,
      )}
    >
      <FieldLabel
        htmlFor={compact ? `${id}-num` : id}
        label={label}
        hint={hint}
        className={`${RANGE_FIELD_CLASS}__label`}
      />
      <span className={`${RANGE_FIELD_CLASS}__row`}>
        {!compact ? (
          <NativeRangeControl
            id={id}
            className={`${RANGE_FIELD_CLASS}__slider`}
            min={min}
            max={max}
            step={step}
            value={clamped}
            aria-label={ariaLabel ?? label}
            style={{ ["--delpi-ui-range-progress" as string]: `${progress}%` }}
            onChange={(next) => {
              setEditing(false);
              onChange(next);
            }}
          />
        ) : null}
        <NativeTextControl
          id={`${id}-num`}
          type="text"
          inputMode="decimal"
          className={mergeClassNames(
            NATIVE_CONTROL_CLASS,
            NATIVE_CONTROL_COMPACT_CLASS,
            `${RANGE_FIELD_CLASS}__input`,
            negative ? `${RANGE_FIELD_CLASS}__input--negative` : null,
          )}
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
