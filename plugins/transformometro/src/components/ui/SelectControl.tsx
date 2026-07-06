import { ChevronDown } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import type { SelectOption } from "./selectTypes";

type SelectControlProps = {
  id?: string;
  options: readonly SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  disabled?: boolean;
  allowEmpty?: boolean;
  emptyLabel?: string;
  ariaLabel?: string;
  className?: string;
};

export function SelectControl({
  id,
  options,
  value,
  onChange,
  placeholder = "Selecione…",
  searchable = false,
  disabled = false,
  allowEmpty = false,
  emptyLabel = "—",
  ariaLabel,
  className,
}: SelectControlProps) {
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
      option.label.toLocaleLowerCase("pt-BR").includes(normalizedQuery)
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

  useEffect(() => {
    if (disabled) {
      setOpen(false);
      setQuery("");
    }
  }, [disabled]);

  const selectedLabel =
    options.find((option) => option.value === value)?.label ??
    (allowEmpty && !value ? emptyLabel : placeholder);

  const rootClass = ["ds-select", open ? "ds-select--open" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} ref={wrapperRef}>
      <button
        id={fieldId}
        type="button"
        className="ds-select__trigger"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={listId}
        aria-label={ariaLabel}
        disabled={disabled}
        onClick={() => {
          setOpen((current) => {
            if (current) setQuery("");
            return !current;
          });
        }}
      >
        <span className="ds-select__trigger-label">{selectedLabel}</span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>

      {open ? (
        <div className="ds-select__panel">
          {searchable ? (
            <input
              type="search"
              className="ds-select__search"
              placeholder="Buscar…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-label={ariaLabel ? `Buscar ${ariaLabel}` : "Buscar opções"}
            />
          ) : null}

          <ul id={listId} className="ds-select__list" role="listbox">
            {allowEmpty ? (
              <li>
                <button
                  type="button"
                  className={`ds-select__option${!value ? " ds-select__option--active" : ""}`}
                  onClick={() => {
                    onChange("");
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  {emptyLabel}
                </button>
              </li>
            ) : null}
            {filteredOptions.length === 0 ? (
              <li className="ds-select__empty">Nenhuma opção encontrada.</li>
            ) : (
              filteredOptions.map((option) => (
                <li key={option.value}>
                  <button
                    type="button"
                    className={`ds-select__option${
                      option.value === value ? " ds-select__option--active" : ""
                    }`}
                    onClick={() => {
                      onChange(option.value);
                      setOpen(false);
                      setQuery("");
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
  );
}
