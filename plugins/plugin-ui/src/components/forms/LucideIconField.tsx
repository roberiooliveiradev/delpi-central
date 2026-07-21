import { useRef, useState, type CSSProperties, type ReactNode } from "react";

import { LucideIconByName } from "./LucideIconPicker";
import type { LucideIconPickerLabels, LucideIconPickerProps } from "./LucideIconPicker";
import { LucideIconPickerPopover } from "./LucideIconPickerPopover";
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
  showClear?: boolean;
  title?: string;
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
  portalScopeClassName?: string;
};

function buildPickerChange(
  options: UseLucideIconFieldOptions,
  onClose: () => void,
): LucideIconPickerProps["onChange"] {
  const { onChange, closeOnSelect = true } = options;
  return (name) => {
    onChange(name);
    if (closeOnSelect) onClose();
  };
}

/** Estado do campo — use com trigger customizado (ex.: ribbon TV) + LucideIconPickerPopover. */
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
    /** Props do conteúdo do picker (sem shell de portal). */
    pickerContentProps: {
      value: resolvedValue,
      curatedOnly: options.curatedOnly ?? false,
      nameFormat: options.nameFormat ?? "pascal",
      maxResults: options.maxResults,
      labels: options.labels,
      showClear: options.showClear,
      title: options.title,
      onChange: buildPickerChange(options, close),
      onClose: close,
    } satisfies Partial<LucideIconPickerProps> & {
      onChange: LucideIconPickerProps["onChange"];
      onClose: () => void;
    },
    /**
     * @deprecated Prefira `pickerContentProps` + `LucideIconPickerPopover`.
     * Mantido para hosts que ainda montam `LucideIconPicker` embutido.
     */
    pickerProps: {
      embedded: true,
      curatedOnly: options.curatedOnly ?? false,
      nameFormat: options.nameFormat ?? "pascal",
      value: resolvedValue,
      maxResults: options.maxResults,
      labels: options.labels,
      showClear: options.showClear,
      onChange: buildPickerChange(options, close),
      onClose: close,
    } satisfies LucideIconPickerProps,
  };
}

/** Campo padrão: trigger + popover com biblioteca Lucide completa. */
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
  portalScopeClassName,
  ...options
}: LucideIconFieldProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const uncontrolled = useLucideIconField({ ...options, defaultOpen });
  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : uncontrolled.open;

  const setOpen = (next: boolean) => {
    if (!isControlled) uncontrolled.setOpen(next);
    onOpenChange?.(next);
  };

  const resolvedValue = uncontrolled.resolvedValue;

  const triggerState: LucideIconFieldTriggerState = {
    open: isOpen,
    resolvedValue,
    toggle: () => setOpen(!isOpen),
    close: () => setOpen(false),
  };

  const rootClass = ["delpi-ui-lucide-icon-field", className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} style={style} ref={rootRef}>
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
      <LucideIconPickerPopover
        open={isOpen}
        onOpenChange={setOpen}
        anchorRef={rootRef}
        value={resolvedValue}
        onChange={buildPickerChange(options, () => setOpen(false))}
        curatedOnly={options.curatedOnly}
        nameFormat={options.nameFormat}
        maxResults={options.maxResults}
        labels={options.labels}
        showClear={options.showClear}
        title={options.title}
        pickerClassName={pickerClassName}
        portalScopeClassName={portalScopeClassName}
        ariaLabel={ariaLabel}
      />
    </div>
  );
}
