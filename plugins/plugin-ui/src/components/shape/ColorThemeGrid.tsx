import { cssToColorValue, normalizeHex } from "./colorUtils";

type ColorSwatchProps = {
  color: string;
  selected?: boolean;
  label?: string;
  onSelect: (color: string) => void;
  className?: string;
};

export function ColorSwatch({ color, selected, label, onSelect, className }: ColorSwatchProps) {
  const isTransparent = color === "transparent" || cssToColorValue(color).alpha === 0;
  const swatchClass = [
    "delpi-ui-color-swatch",
    selected ? "delpi-ui-color-swatch--selected" : null,
    isTransparent ? "delpi-ui-color-swatch--transparent" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      type="button"
      className={swatchClass}
      aria-label={label ?? color}
      aria-pressed={selected}
      title={label ?? color}
      onClick={() => onSelect(color)}
    >
      <span
        className="delpi-ui-color-swatch__fill"
        style={{ background: isTransparent ? undefined : color }}
        aria-hidden="true"
      />
    </button>
  );
}

type ColorThemeGridProps = {
  rows: readonly (readonly string[])[];
  value?: string;
  onSelect: (color: string) => void;
  ariaLabel?: string;
};

export function ColorThemeGrid({ rows, value, onSelect, ariaLabel }: ColorThemeGridProps) {
  const normalizedValue = value ? normalizeHex(cssToColorValue(value).hex) : undefined;

  return (
    <div className="delpi-ui-color-theme-grid" role="grid" aria-label={ariaLabel}>
      {rows.map((row, rowIndex) => (
        <div key={rowIndex} className="delpi-ui-color-theme-grid__row" role="row">
          {row.map((color, columnIndex) => (
            <ColorSwatch
              key={`${rowIndex}-${columnIndex}-${color}`}
              color={color}
              selected={normalizedValue === normalizeHex(color)}
              onSelect={onSelect}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

type ColorStandardRowProps = {
  colors: readonly string[];
  value?: string;
  onSelect: (color: string) => void;
  ariaLabel?: string;
};

export function ColorStandardRow({ colors, value, onSelect, ariaLabel }: ColorStandardRowProps) {
  const normalizedValue = value ? normalizeHex(cssToColorValue(value).hex) : undefined;

  return (
    <div className="delpi-ui-color-standard-row" role="list" aria-label={ariaLabel}>
      {colors.map((color) => (
        <ColorSwatch
          key={color}
          color={color}
          selected={normalizedValue === normalizeHex(color)}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
