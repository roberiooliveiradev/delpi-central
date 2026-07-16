import { useState, type CSSProperties, type ReactNode } from "react";

import {
  LucideIconByName,
  LucideIconPicker,
  type LucideIconPickerLabels,
  type LucideIconPickerProps,
} from "./LucideIconPicker";
import { lucideIconPtLabel } from "./lucideIconResolver";

export type UseLucideIconFieldOptions = {
  value?: string | null;
  onChange: (iconName: string | null) => void;
  defaultIcon?: string;
  nameFormat?: "kebab" | "pascal";
  curatedOnly?: boolean;
  labels?: LucideIconPickerLabels;
  maxResults?: number;
  closeOnSelect?: boolean;
  defaultOpen?: boolean;
};

export type LucideIconFieldTriggerState = {
  open: boolean;
  toggle: () => void;
  close: () => void;
  resolvedValue: string;
};

export type LucideIconFieldProps = UseLucideIconFieldOptions & {
  className?: string;
  pickerClassName?: string;
  style?: CSSProperties;
  id?: string;
  ariaLabel?: string;
  showPreview?: boolean;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  renderTrigger?: (state: LucideIconFieldTriggerState) => ReactNode;
};

function buildPickerProps(
  options: UseLucideIconFieldOptions,
  resolvedValue: string,
  onClose: () => void,
): LucideIconPickerProps {
  const {
    onChange,
    nameFormat = "pascal",
    curatedOnly = false,
    labels,
    maxResults,
    closeOnSelect = true,
  } = options;

  return {
    embedded: true,
    curatedOnly,
    nameFormat,
    value: resolvedValue,
    maxResults,
    labels,
    onChange: (name) => {
      onChange(name);
      if (closeOnSelect) onClose();
    },
    onClose,
  };
}

/** Estado + props do picker — use com trigger customizado (ex.: ribbon TV). */
export function useLucideIconField(options: UseLucideIconFieldOptions) {
  const { value, defaultIcon = "Star", defaultOpen = false } = options;
  const [open, setOpen] = useState(defaultOpen);
  const resolvedValue = value?.trim() || defaultIcon;

  const close = () => setOpen(false);

  return {
    open,
    setOpen,
    toggle: () => setOpen((current) => !current),
    close,
    resolvedValue,
    pickerProps: buildPickerProps(options, resolvedValue, close),
  };
}

/** Campo padrão: trigger + picker embutido (biblioteca Lucide canônica). */
export function LucideIconField({
  className,
  pickerClassName,
  style,
  id,
  ariaLabel = "Selecionar ícone",
  showPreview = true,
  defaultOpen = false,
  open,
  onOpenChange,
  renderTrigger,
  ...options
}: LucideIconFieldProps) {
  const uncontrolled = useLucideIconField({ ...options, defaultOpen });
  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : uncontrolled.open;

  const setOpen = (next: boolean) => {
    if (!isControlled) uncontrolled.setOpen(next);
    onOpenChange?.(next);
  };

  const resolvedValue = uncontrolled.resolvedValue;
  const pickerProps = buildPickerProps(options, resolvedValue, () => setOpen(false));

  const triggerState: LucideIconFieldTriggerState = {
    open: isOpen,
    resolvedValue,
    toggle: () => setOpen(!isOpen),
    close: () => setOpen(false),
  };

  const rootClass = ["delpi-ui-lucide-icon-field", className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} style={style}>
      {renderTrigger ? (
        renderTrigger(triggerState)
      ) : (
        <button
          type="button"
          id={id}
          className="delpi-ui-lucide-icon-field__trigger"
          aria-label={ariaLabel}
          aria-expanded={isOpen}
          onClick={triggerState.toggle}
        >
          {showPreview ? (
            <span className="delpi-ui-lucide-icon-field__preview" aria-hidden="true">
              <LucideIconByName
                name={resolvedValue}
                fallback={options.defaultIcon}
                size={18}
                strokeWidth={1.75}
              />
            </span>
          ) : null}
          <span className="delpi-ui-lucide-icon-field__label">
            {lucideIconPtLabel(resolvedValue)}
          </span>
        </button>
      )}
      {isOpen ? (
        <div className={["delpi-ui-lucide-icon-field__picker", pickerClassName].filter(Boolean).join(" ")}>
          <LucideIconPicker {...pickerProps} />
        </div>
      ) : null}
    </div>
  );
}
