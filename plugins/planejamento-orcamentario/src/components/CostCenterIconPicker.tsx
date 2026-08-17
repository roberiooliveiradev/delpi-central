import { useEffect, useId, useRef, useState } from "react";
import { Ban } from "lucide-react";

import {
  COST_CENTER_ICON_CATALOG,
  resolveCostCenterIcon,
} from "../utils/costCenterIcons";

type CostCenterIconPickerProps = {
  iconKey?: string | null;
  disabled?: boolean;
  busy?: boolean;
  label: string;
  onSelect: (iconKey: string | null) => void;
};

export function CostCenterIconPicker({
  iconKey,
  disabled = false,
  busy = false,
  label,
  onSelect,
}: CostCenterIconPickerProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const Icon = resolveCostCenterIcon(iconKey);

  useEffect(() => {
    if (!open) return;
    const onDoc = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="po-cc-icon-picker" ref={rootRef}>
      <button
        type="button"
        className="po-cc-admin__registered-icon po-cc-icon-picker__trigger"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={open ? listId : undefined}
        aria-label={`Ícone de ${label}. Clique para personalizar.`}
        disabled={disabled || busy}
        onClick={() => setOpen((v) => !v)}
      >
        <Icon size={18} aria-hidden="true" />
      </button>
      {open ? (
        <div
          id={listId}
          role="listbox"
          aria-label={`Escolher ícone para ${label}`}
          className="po-cc-icon-picker__panel"
        >
          <button
            type="button"
            role="option"
            aria-selected={!iconKey}
            className="po-cc-icon-picker__option"
            title="Padrão"
            onClick={() => {
              onSelect(null);
              setOpen(false);
            }}
          >
            <Ban size={16} aria-hidden="true" />
            <span>Padrão</span>
          </button>
          {COST_CENTER_ICON_CATALOG.map((item) => {
            const OptionIcon = item.Icon;
            const selected = iconKey === item.key;
            return (
              <button
                key={item.key}
                type="button"
                role="option"
                aria-selected={selected}
                className={
                  selected
                    ? "po-cc-icon-picker__option is-selected"
                    : "po-cc-icon-picker__option"
                }
                title={item.label}
                onClick={() => {
                  onSelect(item.key);
                  setOpen(false);
                }}
              >
                <OptionIcon size={16} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
