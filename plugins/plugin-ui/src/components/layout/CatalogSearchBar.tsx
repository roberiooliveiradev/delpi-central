import { Search, X } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type CatalogSearchHit = {
  id: string;
  label: string;
  groupLabel?: string;
};

export type CatalogSearchBarClassNames = {
  root: string;
  field: string;
  icon: string;
  input: string;
  clear: string;
  listbox: string;
  option: string;
  optionActive: string;
  optionGroup: string;
  empty: string;
};

export type CatalogSearchBarProps = {
  value: string;
  onChange: (value: string) => void;
  onSelectHit?: (id: string) => void;
  hits?: readonly CatalogSearchHit[];
  placeholder?: string;
  clearLabel?: string;
  emptyHitsLabel?: string;
  classNames: CatalogSearchBarClassNames;
  className?: string;
  "aria-label"?: string;
};

export function catalogSearchBarBemClasses(prefix: string): CatalogSearchBarClassNames {
  const base = `${prefix}-catalog-search`;
  const ui = "delpi-ui-catalog-search-bar";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    field: pair(`${base}__field`, `${ui}__field`),
    icon: pair(`${base}__icon`, `${ui}__icon`),
    input: pair(`${base}__input`, `${ui}__input`),
    clear: pair(`${base}__clear`, `${ui}__clear`),
    listbox: pair(`${base}__listbox`, `${ui}__listbox`),
    option: pair(`${base}__option`, `${ui}__option`),
    optionActive: pair(
      `${base}__option ${base}__option--active`,
      `${ui}__option ${ui}__option--active`,
    ),
    optionGroup: pair(`${base}__option-group`, `${ui}__option-group`),
    empty: pair(`${base}__empty`, `${ui}__empty`),
  };
}

/**
 * Barra de busca de catálogo (controlled). Filtro fica no MFE.
 * CSS: `styles/catalog-search-bar.css`.
 */
export function CatalogSearchBar({
  value,
  onChange,
  onSelectHit,
  hits = [],
  placeholder,
  clearLabel = "Limpar busca",
  emptyHitsLabel,
  classNames,
  className,
  "aria-label": ariaLabel,
}: CatalogSearchBarProps) {
  const listId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(() => value.trim().length > 0);
  const [activeIndex, setActiveIndex] = useState(0);
  const showList = open && value.trim().length > 0;

  useEffect(() => {
    setActiveIndex(0);
  }, [hits, value]);

  useEffect(() => {
    if (!showList) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [showList]);

  const selectHit = useCallback(
    (id: string) => {
      onSelectHit?.(id);
      setOpen(false);
    },
    [onSelectHit],
  );

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      if (value) {
        onChange("");
      }
      setOpen(false);
      return;
    }
    if (!showList || hits.length === 0) {
      if (event.key === "Enter" && hits[0]) {
        event.preventDefault();
        selectHit(hits[0].id);
      }
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, hits.length - 1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const hit = hits[activeIndex] ?? hits[0];
      if (hit) selectHit(hit.id);
    }
  };

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div ref={rootRef} className={rootClass}>
      <div className={classNames.field}>
        <span className={classNames.icon} aria-hidden={true}>
          <Search size={18} strokeWidth={1.75} />
        </span>
        <input
          type="search"
          className={classNames.input}
          value={value}
          placeholder={placeholder}
          aria-label={ariaLabel ?? placeholder}
          aria-autocomplete="list"
          aria-controls={showList ? listId : undefined}
          aria-expanded={showList}
          role="combobox"
          onChange={(event) => {
            onChange(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {value ? (
          <button
            type="button"
            className={classNames.clear}
            aria-label={clearLabel}
            onClick={() => {
              onChange("");
              setOpen(false);
            }}
          >
            <X size={16} strokeWidth={2} aria-hidden={true} />
          </button>
        ) : null}
      </div>
      {showList ? (
        <ul id={listId} className={classNames.listbox} role="listbox">
          {hits.length === 0 ? (
            emptyHitsLabel ? (
              <li className={classNames.empty} role="presentation">
                {emptyHitsLabel}
              </li>
            ) : null
          ) : (
            hits.map((hit, index) => (
              <li key={hit.id} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={index === activeIndex}
                  className={
                    index === activeIndex ? classNames.optionActive : classNames.option
                  }
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => selectHit(hit.id)}
                >
                  {hit.groupLabel ? (
                    <span className={classNames.optionGroup}>{hit.groupLabel}</span>
                  ) : null}
                  <span>{hit.label}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}

export type DashboardCatalogSearchBarProps = Omit<CatalogSearchBarProps, "classNames">;

export function createDashboardCatalogSearchBar(config: {
  classNames: CatalogSearchBarClassNames;
}) {
  return function DashboardCatalogSearchBar(props: DashboardCatalogSearchBarProps) {
    return <CatalogSearchBar classNames={config.classNames} {...props} />;
  };
}
