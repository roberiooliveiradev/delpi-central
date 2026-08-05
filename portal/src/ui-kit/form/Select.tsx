// portal/src/ui-kit/form/Select.tsx

import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { Check, ChevronDown } from "lucide-react";
import { AnchoredPanel } from "../overlay/AnchoredPanel";
import type { ControlSize } from "./Input";
import "./controls.css";
import "./Select.css";

export type SelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

export type SelectProps = {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  id?: string;
  size?: ControlSize;
  invalid?: boolean;
  disabled?: boolean;
  placeholder?: string;
  /** Campo de busca no painel. Padrão: automático a partir de 8 opções. */
  searchable?: boolean;
  className?: string;
  "aria-label"?: string;
  "aria-invalid"?: boolean | "true" | "false";
  "aria-required"?: boolean;
};

const SEARCHABLE_THRESHOLD = 8;

export function Select({
  value,
  onChange,
  options,
  id,
  size = "md",
  invalid,
  disabled,
  placeholder = "Selecione…",
  searchable,
  className,
  "aria-label": ariaLabel,
  "aria-invalid": ariaInvalid,
  "aria-required": ariaRequired,
}: SelectProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const listId = `${fieldId}-listbox`;

  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  const isInvalid = invalid || ariaInvalid === true || ariaInvalid === "true";
  const withSearch = searchable ?? options.length >= SEARCHABLE_THRESHOLD;

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return options;
    return options.filter(
      (option) =>
        option.label.toLowerCase().includes(term) ||
        option.value.toLowerCase().includes(term),
    );
  }, [options, query]);

  const selected = options.find((option) => option.value === value);

  const close = (focusTrigger = true) => {
    setOpen(false);
    setQuery("");
    if (focusTrigger) triggerRef.current?.focus();
  };

  useEffect(() => {
    if (!open) return;
    const index = filtered.findIndex((option) => option.value === value);
    setActiveIndex(index >= 0 ? index : 0);
    if (withSearch) searchRef.current?.focus();
    // Alinhar a opção ativa só na abertura.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const option = panelRef.current?.querySelector<HTMLElement>(
      '[data-active="true"]',
    );
    option?.scrollIntoView({ block: "nearest" });
  }, [open, activeIndex]);

  const commit = (option: SelectOption) => {
    if (option.disabled) return;
    onChange(option.value);
    close();
  };

  const moveActive = (delta: number) => {
    if (filtered.length === 0) return;
    setActiveIndex((current) => {
      let next = current;
      for (let step = 0; step < filtered.length; step += 1) {
        next = (next + delta + filtered.length) % filtered.length;
        if (!filtered[next]?.disabled) return next;
      }
      return current;
    });
  };

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (disabled) return;

    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
        event.preventDefault();
        setOpen(true);
      }
      return;
    }

    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        moveActive(1);
        break;
      case "ArrowUp":
        event.preventDefault();
        moveActive(-1);
        break;
      case "Home":
        event.preventDefault();
        setActiveIndex(0);
        break;
      case "End":
        event.preventDefault();
        setActiveIndex(Math.max(filtered.length - 1, 0));
        break;
      case "Enter": {
        event.preventDefault();
        const option = filtered[activeIndex];
        if (option) commit(option);
        break;
      }
      case "Escape":
        event.preventDefault();
        close();
        break;
      case "Tab":
        close(false);
        break;
      default:
        break;
    }
  };

  const rootClass = [
    "portal-ui-select",
    `portal-ui-select--${size}`,
    open ? "portal-ui-select--open" : "",
    isInvalid ? "portal-ui-select--invalid" : "",
    disabled ? "portal-ui-select--disabled" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <button
        id={fieldId}
        ref={triggerRef}
        type="button"
        className="portal-ui-select__trigger"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={open ? listId : undefined}
        aria-label={ariaLabel}
        aria-invalid={isInvalid || undefined}
        aria-required={ariaRequired}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={onKeyDown}
      >
        <span
          className={[
            "portal-ui-select__value",
            selected ? "" : "portal-ui-select__value--placeholder",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {selected?.label ?? placeholder}
        </span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>

      <AnchoredPanel
        open={open && !disabled}
        anchorRef={triggerRef}
        panelRef={panelRef}
        onDismiss={() => close(false)}
        className="portal-ui-select__panel"
      >
        {withSearch ? (
          <input
            ref={searchRef}
            type="search"
            className="portal-ui-select__search"
            value={query}
            placeholder="Buscar…"
            aria-label="Buscar opção"
            onChange={(event) => {
              setQuery(event.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={onKeyDown}
          />
        ) : null}

        <ul id={listId} className="portal-ui-listbox" role="listbox">
          {filtered.length === 0 ? (
            <li className="portal-ui-listbox__empty">Nenhuma opção</li>
          ) : (
            filtered.map((option, index) => {
              const isSelected = option.value === value;
              const isActive = index === activeIndex;

              return (
                <li
                  key={option.value}
                  role="option"
                  aria-selected={isSelected}
                  aria-disabled={option.disabled || undefined}
                  data-active={isActive || undefined}
                  className={[
                    "portal-ui-listbox__option",
                    isActive ? "portal-ui-listbox__option--active" : "",
                    isSelected ? "portal-ui-listbox__option--selected" : "",
                    option.disabled ? "portal-ui-listbox__option--disabled" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    commit(option);
                  }}
                >
                  <span className="portal-ui-listbox__check">
                    {isSelected ? <Check size={14} /> : null}
                  </span>
                  <span className="portal-ui-listbox__label">{option.label}</span>
                </li>
              );
            })
          )}
        </ul>
      </AnchoredPanel>
    </div>
  );
}
