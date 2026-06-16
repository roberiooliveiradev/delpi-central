import { ChevronDown } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { AnchoredMenuPortal } from "../overlay/AnchoredMenuPortal";

import "./composer-option-selector.css";

export type ComposerOptionItem<T extends string = string> = {
  id: T;
  label: string;
  description?: string;
};

type ComposerOptionSelectorProps<T extends string> = {
  options: ComposerOptionItem<T>[];
  value: T;
  disabled?: boolean;
  onChange: (value: T) => void;
  renderIcon: (id: T) => ReactNode;
  menuLabel: string;
  tourId?: string;
  className?: string;
};

export function ComposerOptionSelector<T extends string>({
  options,
  value,
  disabled,
  onChange,
  renderIcon,
  menuLabel,
  tourId,
  className = "mdc-composer-option-selector",
}: ComposerOptionSelectorProps<T>) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const active = options.find((item) => item.id === value) ?? options[0];

  if (!active || options.length === 0) {
    return null;
  }

  return (
    <div className={className} data-tour={tourId}>
      <button
        ref={triggerRef}
        type="button"
        className="mdc-composer-option-selector__trigger"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        title={active.description ?? active.label}
      >
        {renderIcon(active.id)}
        <span>{active.label}</span>
        <ChevronDown size={14} aria-hidden="true" />
      </button>

      <AnchoredMenuPortal
        open={open}
        triggerRef={triggerRef}
        itemCount={options.length}
        placement="composer-option"
        menuLabel={menuLabel}
        onClose={() => setOpen(false)}
      >
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            role="option"
            aria-selected={option.id === value}
            className={
              option.id === value
                ? "mdc-composer-option-selector__option mdc-composer-option-selector__option--active"
                : "mdc-composer-option-selector__option"
            }
            onClick={() => {
              onChange(option.id);
              setOpen(false);
            }}
          >
            <span className="mdc-composer-option-selector__option-label">
              {renderIcon(option.id)}
              <strong>{option.label}</strong>
            </span>
            {option.description ? <small>{option.description}</small> : null}
          </button>
        ))}
      </AnchoredMenuPortal>
    </div>
  );
}
