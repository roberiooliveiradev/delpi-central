import { ChevronDown } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { FieldLabel } from "./HelpTooltip";

export type MultiSelectOption = {
  value: string;
  label: string;
};

type MultiSelectFieldProps = {
  label: string;
  labelHint?: string;
  options: MultiSelectOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  emptyLabel?: string;
  searchable?: boolean;
  disabled?: boolean;
  className?: string;
};

function buildTriggerLabel(
  selectedValues: string[],
  options: MultiSelectOption[],
  emptyLabel: string
): string {
  if (selectedValues.length === 0) return emptyLabel;
  if (selectedValues.length === 1) {
    return options.find((option) => option.value === selectedValues[0])?.label ?? selectedValues[0];
  }
  return `${selectedValues.length} selecionado(s)`;
}

export function MultiSelectField({
  label,
  labelHint,
  options,
  selectedValues,
  onChange,
  emptyLabel = "Todos",
  searchable = false,
  disabled = false,
  className,
}: MultiSelectFieldProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  const filteredOptions = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");
    if (!normalizedQuery) return options;
    return options.filter((option) =>
      option.label.toLocaleLowerCase("pt-BR").includes(normalizedQuery)
    );
  }, [options, query]);

  useEffect(() => {
    if (!open) {
      setQuery("");
    }
  }, [open]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const triggerLabel = useMemo(
    () => buildTriggerLabel(selectedValues, options, emptyLabel),
    [emptyLabel, options, selectedValues]
  );

  const toggleValue = (value: string) => {
    if (selectedValues.includes(value)) {
      onChange(selectedValues.filter((selected) => selected !== value));
      return;
    }
    onChange([...selectedValues, value]);
  };

  const selectVisible = () => {
    const visibleValues = filteredOptions.map((option) => option.value);
    onChange([...new Set([...selectedValues, ...visibleValues])]);
  };

  const rootClass = ["ef-field", "ef-field--multi-select", className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} ref={wrapperRef}>
      <FieldLabel label={label} hint={labelHint} />
      <div className={`ef-multi-select${open ? " ef-multi-select--open" : ""}`}>
        <button
          type="button"
          className="ef-multi-select__trigger"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={listId}
          disabled={disabled}
          onClick={() => setOpen((current) => !current)}
        >
          <span className="ef-multi-select__trigger-label">{triggerLabel}</span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        {open ? (
          <div className="ef-multi-select__panel">
            {searchable ? (
              <input
                type="search"
                className="ef-multi-select__search"
                placeholder="Buscar…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            ) : null}

            <div className="ef-multi-select__actions">
              <button
                type="button"
                className="ef-btn ef-btn--ghost ef-btn--sm"
                onClick={selectVisible}
              >
                Marcar visíveis
              </button>
              <button
                type="button"
                className="ef-btn ef-btn--ghost ef-btn--sm"
                onClick={() => onChange([])}
              >
                Limpar
              </button>
            </div>

            <ul id={listId} className="ef-multi-select__list" role="listbox" aria-multiselectable="true">
              {filteredOptions.length === 0 ? (
                <li className="ef-multi-select__empty">Nenhuma opção encontrada.</li>
              ) : (
                filteredOptions.map((option) => (
                  <li key={option.value}>
                    <label className="ef-multi-select__option" title={option.label}>
                      <input
                        type="checkbox"
                        checked={selectedValues.includes(option.value)}
                        onChange={() => toggleValue(option.value)}
                      />
                      <span>{option.label}</span>
                    </label>
                  </li>
                ))
              )}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}
