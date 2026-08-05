// portal/src/ui-kit/form/MultiSelect.tsx

import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { Check, X } from "lucide-react";
import { AnchoredPanel } from "../overlay/AnchoredPanel";
import type { ControlSize } from "./Input";
import type { SelectOption } from "./Select";
import "./MultiSelect.css";

export type MultiSelectProps = {
  options: SelectOption[];
  value: string[];
  onChange: (next: string[]) => void;
  size?: ControlSize;
  searchable?: boolean;
  maxChips?: number;
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  id?: string;
  className?: string;
  "aria-invalid"?: boolean | "true" | "false";
};

export function MultiSelect({
  options,
  value,
  onChange,
  size = "md",
  searchable = true,
  maxChips,
  placeholder = "Selecionar…",
  disabled,
  invalid,
  id,
  className,
  "aria-invalid": ariaInvalid,
}: MultiSelectProps) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  const isInvalid = invalid || ariaInvalid === true || ariaInvalid === "true";
  const selectedSet = useMemo(() => new Set(value), [value]);

  const labelByValue = useMemo(() => {
    const map = new Map<string, string>();
    options.forEach((o) => map.set(o.value, o.label));
    return map;
  }, [options]);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return options.filter((o) => !o.disabled);
    return options.filter(
      (o) =>
        !o.disabled &&
        (o.label.toLowerCase().includes(term) ||
          o.value.toLowerCase().includes(term)),
    );
  }, [options, query]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, open]);

  const toggle = (optValue: string) => {
    if (disabled) return;
    if (selectedSet.has(optValue)) {
      onChange(value.filter((v) => v !== optValue));
    } else {
      onChange([...value, optValue]);
    }
  };

  const remove = (optValue: string) => {
    if (disabled) return;
    onChange(value.filter((v) => v !== optValue));
  };

  const visibleChips = maxChips != null ? value.slice(0, maxChips) : value;
  const hiddenCount =
    maxChips != null && value.length > maxChips ? value.length - maxChips : 0;

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActiveIndex((i) => Math.min(i + 1, Math.max(filtered.length - 1, 0)));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setOpen(true);
      setActiveIndex((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      const opt = filtered[activeIndex];
      if (opt) toggle(opt.value);
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      setQuery("");
      return;
    }
    if (e.key === "Backspace" && !query && value.length > 0) {
      e.preventDefault();
      onChange(value.slice(0, -1));
    }
  };

  const classes = [
    "portal-ui-multiselect",
    size === "sm" ? "portal-ui-multiselect--sm" : "",
    open ? "portal-ui-multiselect--open" : "",
    isInvalid ? "portal-ui-multiselect--invalid" : "",
    disabled ? "portal-ui-multiselect--disabled" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  let chips: ReactNode = visibleChips.map((v) => (
    <span key={v} className="portal-ui-multiselect__chip">
      <span className="portal-ui-multiselect__chip-label">
        {labelByValue.get(v) ?? v}
      </span>
      {!disabled ? (
        <button
          type="button"
          className="portal-ui-multiselect__chip-remove"
          aria-label={`Remover ${labelByValue.get(v) ?? v}`}
          onClick={(ev) => {
            ev.stopPropagation();
            remove(v);
          }}
        >
          <X size={12} />
        </button>
      ) : null}
    </span>
  ));

  if (hiddenCount > 0) {
    chips = (
      <>
        {chips}
        <span className="portal-ui-multiselect__chip">+{hiddenCount}</span>
      </>
    );
  }

  return (
    <div ref={rootRef} className={classes}>
      <div
        className="portal-ui-multiselect__control"
        onClick={() => {
          if (disabled) return;
          setOpen(true);
          inputRef.current?.focus();
        }}
      >
        {chips}
        {searchable ? (
          <input
            ref={inputRef}
            id={id}
            type="text"
            className="portal-ui-multiselect__input"
            value={query}
            disabled={disabled}
            placeholder={value.length === 0 ? placeholder : ""}
            aria-invalid={isInvalid || undefined}
            aria-expanded={open}
            aria-controls={listId}
            aria-autocomplete="list"
            role="combobox"
            onChange={(e) => {
              setQuery(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={onKeyDown}
          />
        ) : (
          value.length === 0 ? (
            <span className="portal-ui-multiselect__empty">{placeholder}</span>
          ) : null
        )}
      </div>

      <AnchoredPanel
        open={open && !disabled}
        anchorRef={rootRef}
        onDismiss={() => {
          setOpen(false);
          setQuery("");
        }}
      >
        <ul
          id={listId}
          className="portal-ui-listbox"
          role="listbox"
          aria-multiselectable="true"
        >
          {filtered.length === 0 ? (
            <li className="portal-ui-listbox__empty">Nenhuma opção</li>
          ) : (
            filtered.map((opt, index) => {
              const selected = selectedSet.has(opt.value);
              const optClass = [
                "portal-ui-listbox__option",
                selected ? "portal-ui-listbox__option--selected" : "",
                index === activeIndex ? "portal-ui-listbox__option--active" : "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <li
                  key={opt.value}
                  role="option"
                  aria-selected={selected}
                  className={optClass}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    toggle(opt.value);
                  }}
                >
                  <span className="portal-ui-listbox__check">
                    {selected ? <Check size={14} /> : null}
                  </span>
                  <span className="portal-ui-listbox__label">{opt.label}</span>
                </li>
              );
            })
          )}
        </ul>
      </AnchoredPanel>
    </div>
  );
}
