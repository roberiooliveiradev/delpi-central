import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type SegmentToggleOption<T extends string = string> = {
  value: T;
  label: string;
  disabled?: boolean;
};

export type SegmentToggleClassNames = {
  root: string;
  button: string;
  buttonActive: string;
};

export type SegmentToggleSize = "sm" | "md";

export type SegmentToggleProps<T extends string = string> = {
  options: readonly SegmentToggleOption<T>[];
  value: T;
  onChange: (value: T) => void;
  /** Rótulo acessível do grupo (obrigatório). */
  ariaLabel: string;
  idPrefix?: string;
  /** Prefixo BEM do plugin (default `ds`). */
  prefix?: string;
  size?: SegmentToggleSize;
  disabled?: boolean;
  className?: string;
  /** Sobrescreve classes dual BEM + delpi-ui (avançado). */
  classNames?: Partial<SegmentToggleClassNames>;
};

/** Monta classNames BEM `{prefix}-segment-toggle*` + `.delpi-ui-segment-toggle*`. */
export function segmentToggleBemClasses(prefix: string): SegmentToggleClassNames {
  const seg = `${prefix}-segment-toggle`;
  const ui = "delpi-ui-segment-toggle";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(seg, ui),
    button: pair(`${seg}__btn`, `${ui}__btn`),
    buttonActive: pair(
      `${seg}__btn ${seg}__btn--active`,
      `${ui}__btn ${ui}__btn--active`,
    ),
  };
}

/**
 * Toggle segmentado canônico (trilha + pill accent / texto branco — DNA PPM Qualidade).
 * Canônico em `@delpi/plugin-ui` — MFEs não devem reimplementar o chrome.
 */
export function SegmentToggle<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
  idPrefix = "segment",
  prefix = "ds",
  size = "md",
  disabled = false,
  className,
  classNames: classNamesOverride,
}: SegmentToggleProps<T>) {
  const base = segmentToggleBemClasses(prefix);
  const classNames: SegmentToggleClassNames = {
    root: classNamesOverride?.root ?? base.root,
    button: classNamesOverride?.button ?? base.button,
    buttonActive: classNamesOverride?.buttonActive ?? base.buttonActive,
  };

  const rootClass = [
    size === "sm" ? withBemModifier(classNames.root, "sm") : classNames.root,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} role="group" aria-label={ariaLabel}>
      {options.map((option) => {
        const isActive = value === option.value;
        const isDisabled = disabled || Boolean(option.disabled);
        return (
          <button
            key={option.value}
            id={`${idPrefix}-${option.value}`}
            type="button"
            className={isActive ? classNames.buttonActive : classNames.button}
            onClick={() => {
              if (!isDisabled && !isActive) onChange(option.value);
            }}
            aria-pressed={isActive}
            disabled={isDisabled}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
