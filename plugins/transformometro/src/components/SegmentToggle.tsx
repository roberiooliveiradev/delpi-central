import { segmentToggleBemClasses } from "@delpi/plugin-ui/index";

type SegmentOption<T extends string> = {
  value: T;
  label: string;
};

type SegmentToggleProps<T extends string> = {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  idPrefix?: string;
  ariaLabel: string;
};

const SEGMENT = segmentToggleBemClasses("ds");

export function SegmentToggle<T extends string>({
  options,
  value,
  onChange,
  idPrefix = "tm-segment",
  ariaLabel,
}: SegmentToggleProps<T>) {
  return (
    <div className={SEGMENT.root} role="group" aria-label={ariaLabel}>
      {options.map((option) => (
        <button
          key={option.value}
          id={`${idPrefix}-${option.value}`}
          type="button"
          className={value === option.value ? SEGMENT.buttonActive : SEGMENT.button}
          onClick={() => onChange(option.value)}
          aria-pressed={value === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
