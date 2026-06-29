import { ChevronDown, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { FieldLabel } from "./HelpTooltip";
import type { SelectOption } from "./types";

type CreatableMultiSelectFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  options?: SelectOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  emptyLabel?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};

function normalizeValue(value: string): string {
  return value.trim();
}

function uniqueValues(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const normalized = normalizeValue(value);
    if (!normalized) continue;
    const key = normalized.toLocaleLowerCase("pt-BR");
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(normalized);
  }
  return result;
}

export function CreatableMultiSelectField({
  id,
  label,
  hint,
  options = [],
  selectedValues,
  onChange,
  emptyLabel = "Selecione ou digite…",
  placeholder = "Buscar ou adicionar…",
  disabled = false,
  className,
}: CreatableMultiSelectFieldProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const listId = `${fieldId}-list`;

  const optionMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const option of options) {
      map.set(option.value.toLocaleLowerCase("pt-BR"), option.label);
    }
    for (const value of selectedValues) {
      const key = value.toLocaleLowerCase("pt-BR");
      if (!map.has(key)) map.set(key, value);
    }
    return map;
  }, [options, selectedValues]);

  const filteredOptions = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");
    const merged = uniqueValues([
      ...options.map((option) => option.value),
      ...selectedValues,
    ]);
    const base = merged.map((value) => ({
      value,
      label: optionMap.get(value.toLocaleLowerCase("pt-BR")) ?? value,
    }));
    if (!normalizedQuery) return base;
    return base.filter(
      (option) =>
        option.label.toLocaleLowerCase("pt-BR").includes(normalizedQuery) ||
        option.value.toLocaleLowerCase("pt-BR").includes(normalizedQuery),
    );
  }, [optionMap, options, query, selectedValues]);

  const canCreate = useMemo(() => {
    const normalized = normalizeValue(query);
    if (!normalized) return false;
    return !selectedValues.some(
      (value) => value.toLocaleLowerCase("pt-BR") === normalized.toLocaleLowerCase("pt-BR"),
    );
  }, [query, selectedValues]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
      setQuery("");
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const addValue = (value: string) => {
    onChange(uniqueValues([...selectedValues, value]));
    setQuery("");
  };

  const removeValue = (value: string) => {
    onChange(selectedValues.filter((selected) => selected !== value));
  };

  const triggerLabel =
    selectedValues.length === 0
      ? emptyLabel
      : `${selectedValues.length} item(ns) selecionado(s)`;

  return (
    <div
      className={`pac-field pac-field--creatable-multi${className ? ` ${className}` : ""}`}
      ref={wrapperRef}
    >
      <label className="pac-field__label" htmlFor={fieldId}>
        <FieldLabel label={label} hint={hint} />
      </label>

      {selectedValues.length > 0 ? (
        <div className="pac-tag-list" aria-label={`${label} selecionados`}>
          {selectedValues.map((value) => (
            <span key={value} className="pac-tag-chip">
              <span>{optionMap.get(value.toLocaleLowerCase("pt-BR")) ?? value}</span>
              <button
                type="button"
                className="pac-tag-chip__remove"
                aria-label={`Remover ${value}`}
                onClick={() => removeValue(value)}
                disabled={disabled}
              >
                <X size={14} aria-hidden="true" />
              </button>
            </span>
          ))}
        </div>
      ) : null}

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
            <input
              type="search"
              className="pac-multi-select__search"
              placeholder={placeholder}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && canCreate) {
                  event.preventDefault();
                  addValue(query);
                }
              }}
              aria-label={`Buscar ou adicionar em ${label}`}
            />

            {canCreate ? (
              <div className="pac-multi-select__actions">
                <button
                  type="button"
                  className="pac-ghost-btn pac-btn--sm"
                  onClick={() => addValue(query)}
                >
                  Adicionar «{normalizeValue(query)}»
                </button>
              </div>
            ) : null}

            <ul id={listId} className="pac-multi-select__list" role="listbox" aria-multiselectable="true">
              {filteredOptions.length === 0 ? (
                <li className="pac-multi-select__empty">
                  {canCreate ? "Pressione Enter ou use o botão acima." : "Nenhuma opção encontrada."}
                </li>
              ) : (
                filteredOptions.map((option) => (
                  <li key={option.value}>
                    <label className="pac-multi-select__option" title={option.label}>
                      <input
                        type="checkbox"
                        checked={selectedValues.includes(option.value)}
                        onChange={() => {
                          if (selectedValues.includes(option.value)) {
                            removeValue(option.value);
                            return;
                          }
                          addValue(option.value);
                        }}
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
