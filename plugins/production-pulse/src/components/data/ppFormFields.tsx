import type { ReactNode } from "react";

import {
  createDashboardNativeFormFields,
  FormSelectControl,
  formFieldShellBemClasses,
  NativeSwitchControl,
  NativeTextControl,
  type FormFieldShellClassNames,
  type NativeTextControlProps,
} from "@delpi/plugin-ui/index";

const PP_PORTAL_SCOPE = "dashboard-production-pulse";

const PP_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  ...formFieldShellBemClasses("pp"),
  spanWideModifier: "pp-form-grid__span-full",
};

export const {
  FormFieldShell: PpFormFieldShell,
  TextField: PpNativeTextField,
  TextAreaField: PpNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: PP_FIELD_CLASS_NAMES,
});

export type PpNativeSelectOption = {
  value: string;
  label: string;
};

export type PpNativeSelectFieldProps = {
  id: string;
  label: string;
  hint?: string;
  span?: boolean;
  disabled?: boolean;
  className?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly PpNativeSelectOption[];
  placeholderOption?: string;
  searchable?: boolean;
  afterControl?: ReactNode;
};

/** Select de formulário — FormSelectControl do kit (painel portado), não select HTML nativo. */
export function PpNativeSelectField({
  id,
  label,
  hint,
  span,
  disabled,
  className,
  value,
  onChange,
  options,
  placeholderOption,
  searchable = false,
  afterControl,
}: PpNativeSelectFieldProps) {
  const allowEmpty = placeholderOption !== undefined;

  return (
    <PpFormFieldShell
      id={id}
      label={label}
      hint={hint}
      span={span}
      className={className}
      afterControl={afterControl}
    >
      <FormSelectControl
        id={id}
        options={options}
        value={value}
        onChange={onChange}
        disabled={disabled}
        searchable={searchable}
        allowEmpty={allowEmpty}
        emptyLabel={placeholderOption}
        placeholder={placeholderOption ?? "Selecione…"}
        portalScopeClassName={PP_PORTAL_SCOPE}
        ariaLabel={label}
      />
    </PpFormFieldShell>
  );
}

export function ppFieldError(message?: string | null): ReactNode {
  return message ? <span className="pp-field-error">{message}</span> : null;
}

export function ppFieldHint(message?: string | null): ReactNode {
  return message ? <span className="pp-field-hint">{message}</span> : null;
}

export type PpNativeInlineTextFieldProps = {
  id: string;
  label: string;
  hint?: string;
  span?: boolean;
  className?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: NativeTextControlProps["type"];
  min?: number | string;
  max?: number | string;
  step?: number | string;
  inputMode?: NativeTextControlProps["inputMode"];
  disabled?: boolean;
  trailing?: ReactNode;
  afterControl?: ReactNode;
};

/** Texto nativo do kit com slot trailing (ex.: botão «Testar conexão» ao lado do input). */
export function PpNativeInlineTextField({
  id,
  label,
  hint,
  span,
  className,
  value,
  onChange,
  placeholder,
  type,
  min,
  max,
  step,
  inputMode,
  disabled,
  trailing,
  afterControl,
}: PpNativeInlineTextFieldProps) {
  return (
    <PpFormFieldShell
      id={id}
      label={label}
      hint={hint}
      span={span}
      className={className}
      controlWrapperClassName="pp-field__inline-controls"
      afterControl={afterControl}
    >
      <>
        <NativeTextControl
          id={id}
          value={value}
          placeholder={placeholder}
          type={type}
          min={min}
          max={max}
          step={step}
          inputMode={inputMode}
          disabled={disabled}
          onChange={onChange}
        />
        {trailing}
      </>
    </PpFormFieldShell>
  );
}

export type PpNativeSwitchFieldProps = {
  id: string;
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  className?: string;
};

export function PpNativeSwitchField({
  id,
  label,
  hint,
  checked,
  onChange,
  className,
}: PpNativeSwitchFieldProps) {
  return (
    <PpFormFieldShell
      id={id}
      label={label}
      hint={hint}
      className={["pp-field--switch", className].filter(Boolean).join(" ")}
    >
      <NativeSwitchControl checked={checked} aria-label={label} onChange={onChange} />
    </PpFormFieldShell>
  );
}
