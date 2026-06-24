import { ChevronDown } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import type { SelectOption } from "./types";

type MultiSelectFieldProps = {
  id?: string;
  label: string;
  options: SelectOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  emptyLabel?: string;
  searchable?: boolean;
  disabled?: boolean;
  className?: string;
};

function buildTriggerLabel(
  selectedValues: string[],
  options: SelectOption[],
  emptyLabel: string,
): string {
  if (selectedValues.length === 0) return emptyLabel;
  if (selectedValues.length === 1) {
    return options.find((option) => option.value === selectedValues[0])?.label ?? selectedValues[0];
  }
  return `${selectedValues.length} selecionado(s)`;
}

export function MultiSelectField({
  id,
  label,
  options,
  selectedValues,
  onChange,
  emptyLabel = "Todos",
  searchable = true,
  disabled = false,
  className,
}: MultiSelectFieldProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const listId = `${fieldId}-list`;

  const filteredOptions = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");
    if (!normalizedQuery) return options;
    return options.filter((option) =>
      option.label.toLocaleLowerCase("pt-BR").includes(normalizedQuery),
    );
  }, [options, query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
      setQuery("");
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const triggerLabel = useMemo(
    () => buildTriggerLabel(selectedValues, options, emptyLabel),
    [emptyLabel, options, selectedValues],
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

  return (
    <div className={`pac-field pac-field--multi${className ? ` ${className}` : ""}`} ref={wrapperRef}>
      <label className="pac-field__label" htmlFor={fieldId}>
        {label}
      </label>
      <div className={`pac-multi-select${open ? " pac-multi-select--open" : ""}`}>
        <button
          id={fieldId}
          type="button"
          className="pac-multi-select__trigger"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={listId}
          disabled={disabled}
          onClick={() => {
            setOpen((current) => {
              if (current) setQuery("");
              return !current;
            });
          }}
        >
          <span className="pac-multi-select__trigger-label">{triggerLabel}</span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        {open ? (
          <div className="pac-multi-select__panel">
            {searchable ? (
              <input
                type="search"
                className="pac-multi-select__search"
                placeholder="Buscar…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                aria-label={`Buscar ${label}`}
              />
            ) : null}

            <div className="pac-multi-select__actions">
              <button type="button" className="pac-ghost-btn pac-btn--sm" onClick={selectVisible}>
                Marcar visíveis
              </button>
              <button type="button" className="pac-ghost-btn pac-btn--sm" onClick={() => onChange([])}>
                Limpar
              </button>
            </div>

            <ul id={listId} className="pac-multi-select__list" role="listbox" aria-multiselectable="true">
              {filteredOptions.length === 0 ? (
                <li className="pac-multi-select__empty">Nenhuma opção encontrada.</li>
              ) : (
                filteredOptions.map((option) => (
                  <li key={option.value}>
                    <label className="pac-multi-select__option" title={option.label}>
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
