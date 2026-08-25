import { useEffect, useRef, useState } from "react";

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
  /**
   * Chamado ao soltar o slider (pointerup/cancel) e ao confirmar o input (blur/Enter).
   * Use para persistência cara (PATCH); mantenha `onChange` para UI ao vivo.
   */
  onCommit?: (value: number) => void;
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
 *
 * Durante o arraste, o valor exibido fica em buffer local até o `value` do pai
 * acompanhar — evita salto quando o pai só atualiza após PATCH assíncrono.
 */
export function RangeField({
  id,
  label,
  hint,
  value,
  onChange,
  onCommit,
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
  const draggingRef = useRef(false);
  const [dragValue, setDragValue] = useState<number | null>(null);
  const activeValue = dragValue ?? clamped;
  const activeValueRef = useRef(activeValue);
  activeValueRef.current = activeValue;
  const progress = ((activeValue - min) / (safeMax - min)) * 100;
  const shown = formatShown(activeValue, displayValue);
  const [draft, setDraft] = useState(shown);
  const [editing, setEditing] = useState(false);
  const negative = isNegativeShown(draft, activeValue);
  const compact = density === "compact";

  useEffect(() => {
    if (draggingRef.current) return;
    if (dragValue != null && dragValue !== clamped) {
      // Pós-arraste: mantém o thumb até o pai refletir o valor (evita snap-back).
      return;
    }
    setDragValue(null);
  }, [clamped, dragValue]);

  useEffect(() => {
    if (!editing) setDraft(formatShown(activeValue, displayValue));
  }, [activeValue, displayValue, editing]);

  const commitDraft = () => {
    setEditing(false);
    const next = parseAndClamp(draft, min, max, activeValue);
    setDragValue(null);
    if (next !== value) {
      onChange(next);
      onCommit?.(next);
      return;
    }
    setDraft(formatShown(value, displayValue));
  };

  const endSliderGesture = () => {
    draggingRef.current = false;
    onCommit?.(activeValueRef.current);
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
            value={activeValue}
            aria-label={ariaLabel ?? label}
            style={{ ["--delpi-ui-range-progress" as string]: `${progress}%` }}
            onPointerDown={() => {
              draggingRef.current = true;
            }}
            onPointerUp={endSliderGesture}
            onPointerCancel={endSliderGesture}
            onChange={(next) => {
              setEditing(false);
              setDragValue(next);
              onChange(next);
              // Teclado / clique sem gesto pointer: persiste na hora.
              if (!draggingRef.current) onCommit?.(next);
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
