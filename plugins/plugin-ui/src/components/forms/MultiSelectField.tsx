import { ChevronDown, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { FieldLabel } from "../help/FieldLabel";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { buildMultiSelectTriggerLabel } from "../../utils/multiSelectLabel";
import { delpiUiClass } from "../../utils/delpiUiClass";
import { NativeCheckboxControl } from "./NativeCheckboxControl";

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
  tagList?: string;
  tagChip?: string;
  tagRemove?: string;
};

export type MultiSelectFieldLabels = {
  emptyLabel: string;
  searchPlaceholder: string;
  selectVisible: string;
  clear: string;
  emptyOptions: string;
  multipleSelected: (count: number) => string;
  createOption?: (query: string) => string;
  searchAriaLabel?: (label: string) => string;
  selectedCountLabel?: (count: number) => string;
  emptyOptionsCreatable?: string;
  removeTagAriaLabel?: (value: string) => string;
};

export type MultiSelectFieldProps = {
  label: string;
  labelHint?: string;
  id?: string;
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
  /** Limite de itens selecionados (ex.: 1 = escolha única com UX de tags). */
  maxSelected?: number;
  onCreateOption?: (value: string) => void;
  showSelectedTags?: boolean;
  includeSelectedInOptions?: boolean;
  showBulkActions?: boolean;
  /** Escopo CSS do MFE no portal do painel (ex.: `dashboard-commercial`). */
  portalScopeClassName?: string;
};

/** Monta BEM `{prefix}-multi-select__*` + classes estáveis `.delpi-ui-multi-select*`. */
export function multiSelectBemClasses(prefix: string): MultiSelectFieldClassNames {
  const ms = `${prefix}-multi-select`;
  const ui = "delpi-ui-multi-select";
  const pair = (local: string, canonical: string) =>
    local === canonical ? canonical : delpiUiClass(local, canonical);

  return {
    root: delpiUiClass(
      `${prefix}-filter-box ${prefix}-field ${prefix}-field--multi-select`,
      "delpi-ui-filter-box",
    ),
    fieldLabel: `${prefix}-field__label`,
    multiSelect: pair(ms, ui),
    multiSelectOpen: pair(`${ms} ${ms}--open`, `${ui} ${ui}--open`),
    trigger: pair(`${ms}__trigger`, `${ui}__trigger`),
    triggerLabel: pair(`${ms}__trigger-label`, `${ui}__trigger-label`),
    panel: pair(`${ms}__panel`, `${ui}__panel`),
    search: pair(`${ms}__search`, `${ui}__search`),
    actions: pair(`${ms}__actions`, `${ui}__actions`),
    /* Compacto canônico — não usar `{prefix}-ghost-btn` (toolbar sobrescreve btn--sm). */
    actionButton: "delpi-ui-multi-select__action",
    list: pair(`${ms}__list`, `${ui}__list`),
    empty: pair(`${ms}__empty`, `${ui}__empty`),
    option: pair(`${ms}__option`, `${ui}__option`),
    createOption: pair(`${ms}__create`, `${ui}__create`),
  };
}

/** Multi-select em formulário PAC (mantém dual filter-box canônico). */
export function multiSelectPacClasses(prefix: string): MultiSelectFieldClassNames {
  return {
    ...multiSelectBemClasses(prefix),
    root: delpiUiClass(`${prefix}-field ${prefix}-field--multi`, "delpi-ui-filter-box"),
  };
}

/** Multi-select creatable PAC com chips de tags selecionadas. */
export function multiSelectCreatablePacClasses(prefix: string): MultiSelectFieldClassNames {
  return {
    ...multiSelectBemClasses(prefix),
    root: delpiUiClass(
      `${prefix}-field ${prefix}-field--creatable-multi`,
      "delpi-ui-filter-box",
    ),
    tagList: delpiUiClass(`${prefix}-tag-list`, "delpi-ui-tag-list"),
    tagChip: delpiUiClass(`${prefix}-tag-chip`, "delpi-ui-tag-chip"),
    tagRemove: delpiUiClass(`${prefix}-tag-chip__remove`, "delpi-ui-tag-chip__remove"),
  };
}

export function MultiSelectField({
  label,
  labelHint,
  id,
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
  maxSelected,
  onCreateOption,
  showSelectedTags = false,
  includeSelectedInOptions = false,
  showBulkActions = true,
  portalScopeClassName,
}: MultiSelectFieldProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const generatedId = useId();
  const triggerId = id ?? generatedId;
  const listId = `${triggerId}-list`;
  const resolvedEmptyLabel = emptyLabel ?? labels.emptyLabel;
  const normalizedQuery = query.trim();

  const optionLabelByValue = useMemo(() => {
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

  const listOptions = useMemo(() => {
    if (!includeSelectedInOptions) return options;

    const merged = new Map<string, MultiSelectOption>();
    for (const option of options) {
      merged.set(option.value.toLocaleLowerCase("pt-BR"), option);
    }
    for (const value of selectedValues) {
      const key = value.toLocaleLowerCase("pt-BR");
      if (!merged.has(key)) {
        merged.set(key, { value, label: optionLabelByValue.get(key) ?? value });
      }
    }
    return Array.from(merged.values());
  }, [includeSelectedInOptions, optionLabelByValue, options, selectedValues]);

  const filteredOptions = useMemo(() => {
    const normalizedSearch = normalizedQuery.toLocaleLowerCase("pt-BR");
    const source = includeSelectedInOptions ? listOptions : options;
    if (!normalizedSearch) return source;
    return source.filter(
      (option) =>
        option.label.toLocaleLowerCase("pt-BR").includes(normalizedSearch) ||
        option.value.toLocaleLowerCase("pt-BR").includes(normalizedSearch),
    );
  }, [includeSelectedInOptions, listOptions, normalizedQuery, options]);

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
    const next =
      maxSelected === 1
        ? [normalizedQuery]
        : maxSelected != null && selectedValues.length >= maxSelected
          ? [...selectedValues.slice(0, maxSelected - 1), normalizedQuery]
          : [...selectedValues, normalizedQuery];
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
    if (disabled) {
      setOpen(false);
      setQuery("");
    }
  }, [disabled]);

  const closePanel = () => {
    setOpen(false);
    setQuery("");
  };

  const triggerLabel = useMemo(() => {
    if (selectedValues.length > 0 && labels.selectedCountLabel) {
      return labels.selectedCountLabel(selectedValues.length);
    }

    return buildMultiSelectTriggerLabel(
      selectedValues,
      options,
      resolvedEmptyLabel,
      labels.multipleSelected,
    );
  }, [labels, options, resolvedEmptyLabel, selectedValues]);

  const removeValue = (value: string) => {
    onChange(selectedValues.filter((selected) => selected !== value));
  };

  const toggleValue = (value: string) => {
    if (selectedValues.includes(value)) {
      onChange(selectedValues.filter((selected) => selected !== value));
      return;
    }
    if (maxSelected === 1) {
      onChange([value]);
      return;
    }
    if (maxSelected != null && selectedValues.length >= maxSelected) {
      onChange([...selectedValues.slice(0, maxSelected - 1), value]);
      return;
    }
    onChange([...selectedValues, value]);
  };

  const selectVisible = () => {
    const visibleValues = filteredOptions.map((option) => option.value);
    if (maxSelected === 1) {
      const first = visibleValues[0];
      onChange(first ? [first] : []);
      return;
    }
    const merged = [...new Set([...selectedValues, ...visibleValues])];
    onChange(maxSelected != null ? merged.slice(0, maxSelected) : merged);
  };

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const actionButtonClass = [
    "delpi-ui-multi-select__action",
    classNames.actionButton !== "delpi-ui-multi-select__action" ? classNames.actionButton : null,
  ]
    .filter(Boolean)
    .join(" ");
  const emptyListMessage =
    filteredOptions.length === 0 && canCreate && labels.emptyOptionsCreatable
      ? labels.emptyOptionsCreatable
      : labels.emptyOptions;

  // Espelha `--portal` em cada token (prefix + delpi-ui), como no SelectControl.
  const panelClassName = [
    classNames.panel,
    ...classNames.panel
      .split(/\s+/)
      .filter(Boolean)
      .map((token) => `${token}--portal`),
  ].join(" ");

  return (
    <div className={rootClass}>
      <FieldLabel label={label} hint={labelHint} className={classNames.fieldLabel} />

      {showSelectedTags && selectedValues.length > 0 && classNames.tagList ? (
        <div className={classNames.tagList} aria-label={`${label} selecionados`}>
          {selectedValues.map((value) => (
            <span key={value} className={classNames.tagChip}>
              <span>{optionLabelByValue.get(value.toLocaleLowerCase("pt-BR")) ?? value}</span>
              {classNames.tagRemove ? (
                <button
                  type="button"
                  className={classNames.tagRemove}
                  aria-label={labels.removeTagAriaLabel?.(value) ?? `Remover ${value}`}
                  onClick={() => removeValue(value)}
                  disabled={disabled}
                >
                  <X size={14} aria-hidden="true" />
                </button>
              ) : null}
            </span>
          ))}
        </div>
      ) : null}

      <div
        className={open ? classNames.multiSelectOpen : classNames.multiSelect}
        ref={anchorRef}
      >
        <button
          id={triggerId}
          type="button"
          className={classNames.trigger}
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
          <span className={classNames.triggerLabel}>{triggerLabel}</span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>

        <AnchoredPanelPortal
          open={open}
          anchorRef={anchorRef}
          panelRef={panelRef}
          className={panelClassName}
          variant="bare"
          matchAnchorWidth
          role="presentation"
          portalScopeClassName={portalScopeClassName}
          exclusive={false}
          onDismiss={closePanel}
        >
          {searchable ? (
            <input
              type="search"
              className={classNames.search}
              placeholder={labels.searchPlaceholder}
              value={query}
              aria-label={labels.searchAriaLabel?.(label)}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && canCreate) {
                  event.preventDefault();
                  handleCreate();
                }
              }}
            />
          ) : null}

          {!showBulkActions && canCreate ? (
            <div className={classNames.actions}>
              <button type="button" className={actionButtonClass} onClick={handleCreate}>
                {(labels.createOption ?? ((value: string) => `Adicionar "${value}"`))(
                  normalizedQuery,
                )}
              </button>
            </div>
          ) : null}

          {showBulkActions && canCreate && classNames.createOption ? (
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

          {showBulkActions ? (
            <div className={classNames.actions}>
              <button type="button" className={actionButtonClass} onClick={selectVisible}>
                {labels.selectVisible}
              </button>
              <button type="button" className={actionButtonClass} onClick={() => onChange([])}>
                {labels.clear}
              </button>
            </div>
          ) : null}

          <ul id={listId} className={classNames.list} role="listbox" aria-multiselectable="true">
            {filteredOptions.length === 0 ? (
              <li className={classNames.empty}>{emptyListMessage}</li>
            ) : (
              filteredOptions.map((option) => (
                <li key={option.value} className={classNames.option} title={option.label}>
                  <NativeCheckboxControl
                    className="delpi-ui-native-checkbox--compact"
                    checked={selectedValues.includes(option.value)}
                    onChange={() => toggleValue(option.value)}
                    label={option.label}
                  />
                </li>
              ))
            )}
          </ul>
        </AnchoredPanelPortal>
      </div>
    </div>
  );
}

export type DashboardMultiSelectFieldProps = Omit<
  MultiSelectFieldProps,
  "classNames" | "labels"
> & {
  hint?: string;
  placeholder?: string;
};

function resolveMultiSelectClassNames(config: {
  prefix?: string;
  classNames?: MultiSelectFieldClassNames;
}): MultiSelectFieldClassNames {
  if (config.classNames) return config.classNames;
  if (config.prefix) return multiSelectBemClasses(config.prefix);
  throw new Error("createDashboardMultiSelectField: informe prefix ou classNames");
}

export function createDashboardMultiSelectField(config: {
  prefix?: string;
  classNames?: MultiSelectFieldClassNames;
  labels: MultiSelectFieldLabels;
  portalScopeClassName?: string;
}) {
  const classNames = resolveMultiSelectClassNames(config);

  return function DashboardMultiSelectField({
    hint,
    placeholder,
    labelHint,
    portalScopeClassName,
    ...props
  }: DashboardMultiSelectFieldProps) {
    return (
      <MultiSelectField
        classNames={classNames}
        labels={{
          ...config.labels,
          searchPlaceholder: placeholder ?? config.labels.searchPlaceholder,
        }}
        labelHint={hint ?? labelHint}
        {...props}
        portalScopeClassName={portalScopeClassName ?? config.portalScopeClassName}
      />
    );
  };
}

export type DashboardCreatableMultiSelectFieldProps = Omit<
  DashboardMultiSelectFieldProps,
  | "searchable"
  | "creatable"
  | "showSelectedTags"
  | "includeSelectedInOptions"
  | "showBulkActions"
  | "options"
> & {
  options?: MultiSelectOption[];
};

export function createDashboardCreatableMultiSelectField(config: {
  prefix?: string;
  classNames?: MultiSelectFieldClassNames;
  labels: MultiSelectFieldLabels;
  showSelectedTags?: boolean;
  includeSelectedInOptions?: boolean;
  showBulkActions?: boolean;
  portalScopeClassName?: string;
}) {
  const classNames = resolveMultiSelectClassNames(config);

  return function DashboardCreatableMultiSelectField({
    hint,
    placeholder,
    labelHint,
    options = [],
    portalScopeClassName,
    ...props
  }: DashboardCreatableMultiSelectFieldProps) {
    return (
      <MultiSelectField
        classNames={classNames}
        labels={{
          ...config.labels,
          searchPlaceholder: placeholder ?? config.labels.searchPlaceholder,
        }}
        labelHint={hint ?? labelHint}
        options={options}
        searchable
        creatable
        showSelectedTags={config.showSelectedTags ?? true}
        includeSelectedInOptions={config.includeSelectedInOptions ?? true}
        showBulkActions={config.showBulkActions ?? false}
        {...props}
        portalScopeClassName={portalScopeClassName ?? config.portalScopeClassName}
      />
    );
  };
}
