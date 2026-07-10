import { ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { FieldLabel } from "@delpi/plugin-ui/index";

export type DelpiLookupOption<TMeta = Record<string, string>> = {
  value: string;
  label: string;
  meta?: TMeta;
};

type DelpiAsyncLookupFieldProps<TMeta = Record<string, string>> = {
  id?: string;
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  onSelect?: (option: DelpiLookupOption<TMeta>) => void;
  searchOptions: (query: string, signal: AbortSignal) => Promise<DelpiLookupOption<TMeta>[]>;
  placeholder?: string;
  disabled?: boolean;
  minQueryLength?: number;
  /** Ao abrir, carrega a lista inicial de usuários (sem digitar). */
  browseOnOpen?: boolean;
  className?: string;
};

export function DelpiAsyncLookupField<TMeta = Record<string, string>>({
  id,
  label,
  hint,
  value,
  onChange,
  onSelect,
  searchOptions,
  placeholder = "Digite para buscar…",
  disabled = false,
  minQueryLength = 2,
  browseOnOpen = false,
  className,
}: DelpiAsyncLookupFieldProps<TMeta>) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(value);
  const [options, setOptions] = useState<DelpiLookupOption<TMeta>[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const listId = `${fieldId}-list`;

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    if (!open) return;
    const normalized = query.trim();
    const shouldSearch = browseOnOpen
      ? normalized.length === 0 || normalized.length >= minQueryLength
      : normalized.length >= minQueryLength;
    if (!shouldSearch) {
      setOptions([]);
      setSearchError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setLoading(true);
      setSearchError(null);
      void searchOptions(normalized, controller.signal)
        .then((items) => {
          if (controller.signal.aborted) return;
          setOptions(items);
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setOptions([]);
          setSearchError(error instanceof Error ? error.message : "Erro na busca.");
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 280);

    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [browseOnOpen, minQueryLength, open, query, searchOptions]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current?.contains(event.target as Node)) return;
      setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectOption = (option: DelpiLookupOption<TMeta>) => {
    onChange(option.value);
    onSelect?.(option);
    setQuery(option.value);
    setOpen(false);
  };

  return (
    <div className={`pac-field pac-field--lookup${className ? ` ${className}` : ""}`} ref={wrapperRef}>
      <label className="pac-field__label" htmlFor={fieldId}>
        <FieldLabel label={label} hint={hint} />
      </label>
      <div className={`pac-lookup${open ? " pac-lookup--open" : ""}`}>
        <input
          id={fieldId}
          type="search"
          className="pac-field__control"
          value={query}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(event) => {
            const next = event.target.value;
            setQuery(next);
            onChange(next);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          aria-expanded={open}
          aria-controls={listId}
          autoComplete="off"
        />
        <button
          type="button"
          className="pac-lookup__toggle"
          aria-label={`Abrir sugestões de ${label}`}
          disabled={disabled}
          onClick={() => setOpen((current) => !current)}
        >
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        {open ? (
          <div className="pac-lookup__panel">
            {loading ? <p className="pac-lookup__status">Buscando…</p> : null}
            {searchError ? <p className="pac-lookup__status pac-lookup__status--error">{searchError}</p> : null}
            {!loading && !searchError && !browseOnOpen && query.trim().length < minQueryLength ? (
              <p className="pac-lookup__status">Digite pelo menos {minQueryLength} caracteres.</p>
            ) : null}
            {!loading && !searchError && (browseOnOpen || query.trim().length >= minQueryLength) ? (
              <ul id={listId} className="pac-lookup__list" role="listbox">
                {options.length === 0 ? (
                  <li className="pac-lookup__empty">Nenhum resultado.</li>
                ) : (
                  options.map((option) => (
                    <li key={`${option.value}-${option.label}`}>
                      <button
                        type="button"
                        className="pac-lookup__option"
                        onClick={() => selectOption(option)}
                      >
                        {option.label}
                      </button>
                    </li>
                  ))
                )}
              </ul>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
