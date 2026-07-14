import { ChevronDown } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState, type CSSProperties } from "react";

import { FieldLabel } from "../help/FieldLabel";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";

export type SelectOption = {
  value: string;
  label: string;
  /** Estilo da opção (ex.: preview de `fontFamily` no seletor de fonte). */
  style?: CSSProperties;
};

export type SelectControlClassNames = {
  root: string;
  rootOpen: string;
  trigger: string;
  triggerLabel: string;
  panel: string;
  search: string;
  list: string;
  option: string;
  optionActive: string;
  empty: string;
};

export type SelectControlLabels = {
  searchPlaceholder: string;
  emptyOptions: string;
  searchAriaLabel: (label?: string) => string;
};

export type SelectControlProps = {
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
  /** Escopo CSS do MFE no portal do painel (ex.: `dashboard-tv-dashboard`). */
  portalScopeClassName?: string;
  classNames: SelectControlClassNames;
  labels: SelectControlLabels;
};

export function selectControlBemClasses(prefix: string): SelectControlClassNames {
  const select = `${prefix}-select`;
  return {
    root: select,
    rootOpen: `${select} ${select}--open`,
    trigger: `${select}__trigger`,
    triggerLabel: `${select}__trigger-label`,
    panel: `${select}__panel`,
    search: `${select}__search`,
    list: `${select}__list`,
    option: `${select}__option`,
    optionActive: `${select}__option ${select}__option--active`,
    empty: `${select}__empty`,
  };
}

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
  portalScopeClassName,
  classNames,
  labels,
}: SelectControlProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
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
    if (disabled) {
      setOpen(false);
      setQuery("");
    }
  }, [disabled]);

  const selectedOption = options.find((option) => option.value === value);
  const selectedLabel =
    selectedOption?.label ?? (allowEmpty && !value ? emptyLabel : placeholder);

  const rootClass = [open ? classNames.rootOpen : classNames.root, className]
    .filter(Boolean)
    .join(" ");

  const panelClassName = [classNames.panel, `${classNames.panel}--portal`].filter(Boolean).join(" ");

  const closePanel = () => {
    setOpen(false);
    setQuery("");
  };

  return (
    <div className={rootClass} ref={wrapperRef}>
      <button
        id={fieldId}
        type="button"
        className={classNames.trigger}
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
        <span className={classNames.triggerLabel} style={selectedOption?.style}>
          {selectedLabel}
        </span>
        <ChevronDown size={16} aria-hidden={true} />
      </button>

      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        className={panelClassName}
        variant="bare"
        matchAnchorWidth
        role="presentation"
        portalScopeClassName={portalScopeClassName}
        onDismiss={closePanel}
      >
        {searchable ? (
          <input
            type="search"
            className={classNames.search}
            placeholder={labels.searchPlaceholder}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label={labels.searchAriaLabel(ariaLabel)}
          />
        ) : null}

        <ul id={listId} className={classNames.list} role="listbox">
          {allowEmpty ? (
            <li>
              <button
                type="button"
                className={!value ? classNames.optionActive : classNames.option}
                onClick={() => {
                  onChange("");
                  closePanel();
                }}
              >
                {emptyLabel}
              </button>
            </li>
          ) : null}
          {filteredOptions.length === 0 ? (
            <li className={classNames.empty}>{labels.emptyOptions}</li>
          ) : (
            filteredOptions.map((option) => (
              <li key={option.value}>
                <button
                  type="button"
                  className={
                    option.value === value ? classNames.optionActive : classNames.option
                  }
                  style={option.style}
                  onClick={() => {
                    onChange(option.value);
                    closePanel();
                  }}
                >
                  {option.label}
                </button>
              </li>
            ))
          )}
        </ul>
      </AnchoredPanelPortal>
    </div>
  );
}

export type SelectFieldClassNames = {
  root: string;
  labelWrapper?: string;
  fieldLabel: string;
  required: string;
};

export type SelectFieldLabels = {
  placeholder: string;
  emptyLabel: string;
  control: SelectControlLabels;
};

export type SelectFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  options: readonly SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  allowEmpty?: boolean;
  emptyLabel?: string;
  classNames: SelectFieldClassNames;
  controlClassNames: SelectControlClassNames;
  labels: SelectFieldLabels;
};

export function selectFieldTransformometroClasses(prefix: string): {
  field: SelectFieldClassNames;
  control: SelectControlClassNames;
} {
  return {
    field: {
      root: `${prefix}-filter-box`,
      fieldLabel: "tm-field__label",
      required: `${prefix}-field__required`,
    },
    control: selectControlBemClasses(prefix),
  };
}

export function selectFieldPacClasses(prefix: string): {
  field: SelectFieldClassNames;
  control: SelectControlClassNames;
} {
  return {
    field: {
      root: `${prefix}-field`,
      labelWrapper: `${prefix}-field__label`,
      fieldLabel: "",
      required: `${prefix}-field__required`,
    },
    control: selectControlBemClasses(prefix),
  };
}

export function SelectField({
  id,
  label,
  hint,
  options,
  value,
  onChange,
  placeholder,
  searchable = false,
  disabled = false,
  required = false,
  className,
  allowEmpty = false,
  emptyLabel,
  classNames,
  controlClassNames,
  labels,
}: SelectFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const resolvedPlaceholder = placeholder ?? labels.placeholder;
  const resolvedEmptyLabel = emptyLabel ?? labels.emptyLabel;
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass}>
      <label htmlFor={fieldId} className={classNames.labelWrapper}>
        <FieldLabel className={classNames.fieldLabel || undefined} label={label} hint={hint} />
        {required ? <span className={classNames.required}> *</span> : null}
      </label>
      <SelectControl
        id={fieldId}
        options={options}
        value={value}
        onChange={onChange}
        placeholder={resolvedPlaceholder}
        searchable={searchable}
        disabled={disabled}
        allowEmpty={allowEmpty}
        emptyLabel={resolvedEmptyLabel}
        ariaLabel={label}
        classNames={controlClassNames}
        labels={labels.control}
      />
    </div>
  );
}

export type DashboardSelectFieldProps = Omit<
  SelectFieldProps,
  "classNames" | "controlClassNames" | "labels"
>;

export function createDashboardSelectField(config: {
  field: SelectFieldClassNames;
  control: SelectControlClassNames;
  labels: SelectFieldLabels;
}) {
  return function DashboardSelectField(props: DashboardSelectFieldProps) {
    return (
      <SelectField
        classNames={config.field}
        controlClassNames={config.control}
        labels={config.labels}
        {...props}
      />
    );
  };
}

export type DashboardSelectControlProps = Omit<SelectControlProps, "classNames" | "labels">;

export function createDashboardSelectControl(config: {
  control: SelectControlClassNames;
  labels: SelectControlLabels;
}) {
  return function DashboardSelectControl(props: DashboardSelectControlProps) {
    return (
      <SelectControl classNames={config.control} labels={config.labels} {...props} />
    );
  };
}
