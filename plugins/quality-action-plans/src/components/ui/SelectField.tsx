import { ChevronDown } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { FieldLabel } from "@delpi/plugin-ui";
import type { SelectOption } from "./types";

type SelectFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  allowEmpty?: boolean;
  emptyLabel?: string;
};

export function SelectField({
  id,
  label,
  hint,
  options,
  value,
  onChange,
  placeholder = "Selecione…",
  searchable = false,
  disabled = false,
  required = false,
  className,
  allowEmpty = false,
  emptyLabel = "—",
}: SelectFieldProps) {
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

  const selectedLabel =
    options.find((option) => option.value === value)?.label ??
    (allowEmpty && !value ? emptyLabel : placeholder);

  return (
    <div className={`pac-field${className ? ` ${className}` : ""}`} ref={wrapperRef}>
      <label className="pac-field__label" htmlFor={fieldId}>
        <FieldLabel label={label} hint={hint} />
        {required ? <span className="pac-field__required"> *</span> : null}
      </label>
      <div className={`pac-select${open ? " pac-select--open" : ""}`}>
        <button
          id={fieldId}
          type="button"
          className="pac-select__trigger"
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
          <span className="pac-select__trigger-label">{selectedLabel}</span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        {open ? (
          <div className="pac-select__panel">
            {searchable ? (
              <input
                type="search"
                className="pac-select__search"
                placeholder="Buscar…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                aria-label={`Buscar ${label}`}
              />
            ) : null}

            <ul id={listId} className="pac-select__list" role="listbox">
              {allowEmpty ? (
                <li>
                  <button
                    type="button"
                    className={`pac-select__option${!value ? " pac-select__option--active" : ""}`}
                    onClick={() => {
                      onChange("");
                      setOpen(false);
                    }}
                  >
                    {emptyLabel}
                  </button>
                </li>
              ) : null}
              {filteredOptions.length === 0 ? (
                <li className="pac-select__empty">Nenhuma opção encontrada.</li>
              ) : (
                filteredOptions.map((option) => (
                  <li key={option.value}>
                    <button
                      type="button"
                      className={`pac-select__option${
                        option.value === value ? " pac-select__option--active" : ""
                      }`}
                      onClick={() => {
                        onChange(option.value);
                        setOpen(false);
                      }}
                    >
                      {option.label}
                    </button>
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
