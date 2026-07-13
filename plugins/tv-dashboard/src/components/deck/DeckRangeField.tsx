import { FieldLabel, NativeRangeControl } from "@delpi/plugin-ui/index";

type Props = {
  id: string;
  label: string;
  hint?: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  /** Texto ao lado do slider (default: valor arredondado). */
  displayValue?: string;
  "aria-label"?: string;
  className?: string;
};

/**
 * Campo contínuo canônico da ribbon/inspetor — slider plugin-ui + valor.
 * Preferir a number inputs soltos para raio, opacidade, ajustes, etc.
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
  const shown = displayValue ?? String(Math.round(value * 1000) / 1000);

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
      <NativeRangeControl
        id={id}
        className="td-deck-ribbon__range"
        min={min}
        max={max}
        step={step}
        value={clamped}
        aria-label={ariaLabel ?? label}
        style={{ ["--td-range-progress" as string]: `${progress}%` }}
        onChange={onChange}
      />
      <span className="td-deck-ribbon__range-value" aria-hidden>
        {shown}
      </span>
    </span>
  );
}
