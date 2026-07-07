import { ChevronDown } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { FieldLabel } from "../help/FieldLabel";
import { buildMultiSelectTriggerLabel } from "../../utils/multiSelectLabel";

export type MultiSelectOption = {
  value: string;
  label: string;
};

export type MultiSelectFieldClassNames = {
  root: string;
  fieldLabel: string;
  multiSelect: string;
  multiSelectOpen: string;
  trigger: string;
  triggerLabel: string;
  panel: string;
  search: string;
  actions: string;
  actionButton: string;
  list: string;
  empty: string;
  option: string;
  createOption?: string;
};

export type MultiSelectFieldLabels = {
  emptyLabel: string;
  searchPlaceholder: string;
  selectVisible: string;
  clear: string;
  emptyOptions: string;
  multipleSelected: (count: number) => string;
  createOption?: (query: string) => string;
};

export type MultiSelectFieldProps = {
  label: string;
  labelHint?: string;
  options: MultiSelectOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  emptyLabel?: string;
  searchable?: boolean;
  disabled?: boolean;
  className?: string;
  classNames: MultiSelectFieldClassNames;
  labels: MultiSelectFieldLabels;
  creatable?: boolean;
  maxCreateLength?: number;
  onCreateOption?: (value: string) => void;
};

/** Monta classNames BEM `{prefix}-multi-select__*` dos dashboards departamentais. */
export function multiSelectBemClasses(prefix: string): MultiSelectFieldClassNames {
  return {
    root: `${prefix}-filter-box ${prefix}-field ${prefix}-field--multi-select`,
    fieldLabel: `${prefix}-field__label`,
    multiSelect: `${prefix}-multi-select`,
    multiSelectOpen: `${prefix}-multi-select ${prefix}-multi-select--open`,
    trigger: `${prefix}-multi-select__trigger`,
    triggerLabel: `${prefix}-multi-select__trigger-label`,
    panel: `${prefix}-multi-select__panel`,
    search: `${prefix}-multi-select__search`,
    actions: `${prefix}-multi-select__actions`,
    actionButton: `${prefix}-ghost-btn ${prefix}-btn--sm`,
    list: `${prefix}-multi-select__list`,
    empty: `${prefix}-multi-select__empty`,
    option: `${prefix}-multi-select__option`,
    createOption: `${prefix}-multi-select__create`,
  };
}

export function MultiSelectField({
  label,
  labelHint,
  options,
  selectedValues,
  onChange,
  emptyLabel,
  searchable = false,
  disabled = false,
  className,
  classNames,
  labels,
  creatable = false,
  maxCreateLength = 50,
  onCreateOption,
}: MultiSelectFieldProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const resolvedEmptyLabel = emptyLabel ?? labels.emptyLabel;
  const normalizedQuery = query.trim();

  const filteredOptions = useMemo(() => {
    const normalizedSearch = normalizedQuery.toLocaleLowerCase("pt-BR");
    if (!normalizedSearch) return options;
    return options.filter((option) =>
      option.label.toLocaleLowerCase("pt-BR").includes(normalizedSearch),
    );
  }, [normalizedQuery, options]);

  const canCreate = useMemo(() => {
    if (!creatable || !searchable || !normalizedQuery) return false;
    if (normalizedQuery.length > maxCreateLength) return false;
    const key = normalizedQuery.toLocaleLowerCase("pt-BR");
    const exists =
      options.some((option) => option.value.toLocaleLowerCase("pt-BR") === key) ||
      selectedValues.some((value) => value.toLocaleLowerCase("pt-BR") === key);
    return !exists;
  }, [
    creatable,
    maxCreateLength,
    normalizedQuery,
    options,
    searchable,
    selectedValues,
  ]);

  const handleCreate = () => {
    if (!canCreate) return;
    const next = [...selectedValues, normalizedQuery];
    onChange(next);
    onCreateOption?.(normalizedQuery);
    setQuery("");
  };

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
    () =>
      buildMultiSelectTriggerLabel(
        selectedValues,
        options,
        resolvedEmptyLabel,
        labels.multipleSelected,
      ),
    [labels.multipleSelected, options, resolvedEmptyLabel, selectedValues],
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

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} ref={wrapperRef}>
      <FieldLabel label={label} hint={labelHint} className={classNames.fieldLabel} />
      <div className={open ? classNames.multiSelectOpen : classNames.multiSelect}>
        <button
          type="button"
          className={classNames.trigger}
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-controls={listId}
          disabled={disabled}
          onClick={() => setOpen((current) => !current)}
        >
          <span className={classNames.triggerLabel}>{triggerLabel}</span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        {open ? (
          <div className={classNames.panel}>
            {searchable ? (
              <input
                type="search"
                className={classNames.search}
                placeholder={labels.searchPlaceholder}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && canCreate) {
                    event.preventDefault();
                    handleCreate();
                  }
                }}
              />
            ) : null}

            {canCreate && classNames.createOption ? (
              <button
                type="button"
                className={classNames.createOption}
                onClick={handleCreate}
              >
                {(labels.createOption ?? ((value: string) => `Adicionar "${value}"`))(
                  normalizedQuery,
                )}
              </button>
            ) : null}

            <div className={classNames.actions}>
              <button type="button" className={classNames.actionButton} onClick={selectVisible}>
                {labels.selectVisible}
              </button>
              <button type="button" className={classNames.actionButton} onClick={() => onChange([])}>
                {labels.clear}
              </button>
            </div>

            <ul id={listId} className={classNames.list} role="listbox" aria-multiselectable="true">
              {filteredOptions.length === 0 ? (
                <li className={classNames.empty}>{labels.emptyOptions}</li>
              ) : (
                filteredOptions.map((option) => (
                  <li key={option.value}>
                    <label className={classNames.option} title={option.label}>
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

export type DashboardMultiSelectFieldProps = Omit<
  MultiSelectFieldProps,
  "classNames" | "labels"
>;

export function createDashboardMultiSelectField(config: {
  prefix: string;
  labels: MultiSelectFieldLabels;
}) {
  const classNames = multiSelectBemClasses(config.prefix);

  return function DashboardMultiSelectField(props: DashboardMultiSelectFieldProps) {
    return <MultiSelectField classNames={classNames} labels={config.labels} {...props} />;
  };
}
