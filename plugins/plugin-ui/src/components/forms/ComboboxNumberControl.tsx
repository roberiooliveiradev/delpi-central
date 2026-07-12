import { ChevronDown } from "lucide-react";
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { mergeClassNames } from "./nativeControlClasses";

export type ComboboxNumberControlProps = {
  value: number;
  onChange: (value: number) => void;
  /** Valores sugeridos na lista (o usuário pode digitar fora da lista). */
  options: readonly number[];
  min?: number;
  max?: number;
  /** Normaliza o valor ao confirmar (blur/Enter/seleção). */
  clamp?: (value: number) => number;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  "aria-label"?: string;
  /** Escopo CSS do MFE no portal do painel (ex.: `dashboard-tv-dashboard`). */
  portalScopeClassName?: string;
  /** Cantos retos (padrão da ribbon TV). */
  square?: boolean;
  compact?: boolean;
};

function parseDraftNumber(raw: string): number | null {
  const normalized = raw.trim().replace(",", ".");
  if (!normalized) return null;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

/**
 * Combobox numérico: digitar valor livre ou escolher da lista (select + input).
 * Visual canônico `.delpi-ui-combobox-number*` — sem strings PT no pacote.
 */
export function ComboboxNumberControl({
  value,
  onChange,
  options,
  min,
  max,
  clamp,
  disabled = false,
  className,
  inputClassName,
  "aria-label": ariaLabel,
  portalScopeClassName,
  square = true,
  compact = false,
}: ComboboxNumberControlProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(String(value));
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const generatedId = useId();
  const listId = `${generatedId}-list`;

  useEffect(() => {
    setDraft(String(value));
  }, [value]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      if (wrapperRef.current?.contains(target)) return;
      if (panelRef.current?.contains(target)) return;
      setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (disabled) setOpen(false);
  }, [disabled]);

  const sortedOptions = useMemo(
    () => [...options].filter((n, index, all) => all.indexOf(n) === index).sort((a, b) => a - b),
    [options],
  );

  const commit = (raw: string) => {
    const parsed = parseDraftNumber(raw);
    if (parsed == null) {
      setDraft(String(value));
      return;
    }
    const next = clamp ? clamp(parsed) : parsed;
    onChange(next);
    setDraft(String(next));
  };

  const selectOption = (next: number) => {
    const resolved = clamp ? clamp(next) : next;
    onChange(resolved);
    setDraft(String(resolved));
    setOpen(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      commit(draft);
      setOpen(false);
      return;
    }
    if (event.key === "Escape") {
      setDraft(String(value));
      setOpen(false);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
    }
  };

  const rootClass = mergeClassNames(
    "delpi-ui-combobox-number",
    open ? "delpi-ui-combobox-number--open" : null,
    square ? "delpi-ui-combobox-number--square" : null,
    compact ? "delpi-ui-combobox-number--compact" : null,
    className,
  );

  return (
    <div className={rootClass} ref={wrapperRef}>
      <div className="delpi-ui-combobox-number__field">
        <input
          ref={inputRef}
          className={mergeClassNames("delpi-ui-combobox-number__input", inputClassName)}
          type="text"
          inputMode="decimal"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-haspopup="listbox"
          aria-label={ariaLabel}
          aria-valuemin={min}
          aria-valuemax={max}
          disabled={disabled}
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value);
          }}
          onBlur={() => {
            commit(draft);
            setOpen(false);
          }}
          onKeyDown={handleKeyDown}
        />
        <button
          type="button"
          className="delpi-ui-combobox-number__toggle"
          tabIndex={-1}
          disabled={disabled}
          aria-label={ariaLabel ? `${ariaLabel}: lista` : "Abrir lista"}
          aria-expanded={open}
          aria-controls={listId}
          onMouseDown={(event) => {
            event.preventDefault();
            setOpen((current) => !current);
            inputRef.current?.focus();
          }}
        >
          <ChevronDown size={14} aria-hidden="true" />
        </button>
      </div>

      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        variant="bare"
        matchAnchorWidth
        role="presentation"
        portalScopeClassName={portalScopeClassName}
        className={mergeClassNames(
          "delpi-ui-combobox-number__panel",
          "delpi-ui-combobox-number__panel--portal",
          square ? "delpi-ui-combobox-number__panel--square" : null,
        )}
      >
        <ul id={listId} className="delpi-ui-combobox-number__list" role="listbox">
          {sortedOptions.map((option) => {
            const active = option === value;
            return (
              <li key={option} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  className={mergeClassNames(
                    "delpi-ui-combobox-number__option",
                    active ? "delpi-ui-combobox-number__option--active" : null,
                  )}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    selectOption(option);
                  }}
                >
                  {option}
                </button>
              </li>
            );
          })}
        </ul>
      </AnchoredPanelPortal>
    </div>
  );
}
