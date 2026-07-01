import { FieldLabel } from "../ui/HelpTooltip";

type Rnc8dQuantityUnitFieldProps = {
  quantityId: string;
  unitId: string;
  quantityLabel: string;
  unitLabel: string;
  quantityHint?: string;
  unitHint?: string;
  quantityValue: string;
  unitValue: string;
  onQuantityChange: (value: string) => void;
  onUnitChange: (value: string) => void;
  unitPlaceholder?: string;
};

export function Rnc8dQuantityUnitField({
  quantityId,
  unitId,
  quantityLabel,
  unitLabel,
  quantityHint,
  unitHint,
  quantityValue,
  unitValue,
  onQuantityChange,
  onUnitChange,
  unitPlaceholder = "UNIDADES",
}: Rnc8dQuantityUnitFieldProps) {
  return (
    <div className="pac-quantity-unit-field">
      <div className="pac-field">
        <label className="pac-field__label" htmlFor={quantityId}>
          <FieldLabel label={quantityLabel} hint={quantityHint} />
        </label>
        <input
          id={quantityId}
          type="number"
          min={0}
          step="any"
          className="pac-field__control"
          value={quantityValue}
          onChange={(event) => onQuantityChange(event.target.value)}
        />
      </div>
      <div className="pac-field">
        <label className="pac-field__label" htmlFor={unitId}>
          <FieldLabel label={unitLabel} hint={unitHint} />
        </label>
        <input
          id={unitId}
          type="text"
          className="pac-field__control"
          value={unitValue}
          placeholder={unitPlaceholder}
          onChange={(event) => onUnitChange(event.target.value)}
        />
      </div>
    </div>
  );
}
