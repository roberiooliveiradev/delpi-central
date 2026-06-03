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

export function SegmentToggle<T extends string>({
  options,
  value,
  onChange,
  idPrefix = "tm-segment",
  ariaLabel,
}: SegmentToggleProps<T>) {
  return (
    <div className="ds-segment-toggle" role="group" aria-label={ariaLabel}>
      {options.map((option) => (
        <button
          key={option.value}
          id={`${idPrefix}-${option.value}`}
          type="button"
          className={`ds-segment-toggle__btn${
            value === option.value ? " ds-segment-toggle__btn--active" : ""
          }`}
          onClick={() => onChange(option.value)}
          aria-pressed={value === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
