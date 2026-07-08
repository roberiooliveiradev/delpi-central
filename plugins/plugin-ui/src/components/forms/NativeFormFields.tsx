import {
  createDashboardFormFieldShell,
  FormFieldShell,
  type FormFieldShellClassNames,
} from "./FormFieldShell";

type BaseNativeFieldProps = {
  id: string;
  label: string;
  hint?: string;
  span?: boolean;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  controlClassName?: string;
  classNames: FormFieldShellClassNames;
};

export type NativeTextFieldProps = BaseNativeFieldProps & {
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "date" | "number";
  placeholder?: string;
  maxLength?: number;
  min?: number | string;
  inputMode?: "decimal" | "numeric";
};

export function NativeTextField({
  id,
  label,
  hint,
  span,
  required,
  disabled,
  className,
  controlClassName,
  classNames,
  value,
  onChange,
  type = "text",
  placeholder,
  maxLength,
  min,
  inputMode,
}: NativeTextFieldProps) {
  return (
    <FormFieldShell
      id={id}
      label={label}
      hint={hint}
      span={span}
      className={className}
      classNames={classNames}
    >
      <input
        id={id}
        className={controlClassName}
        type={type}
        required={required}
        disabled={disabled}
        value={value}
        placeholder={placeholder}
        maxLength={maxLength}
        min={min}
        inputMode={inputMode}
        onChange={(event) => onChange(event.target.value)}
      />
    </FormFieldShell>
  );
}

export type NativeSelectOption = {
  value: string;
  label: string;
};

export type NativeSelectFieldProps = BaseNativeFieldProps & {
  value: string;
  onChange: (value: string) => void;
  options: readonly NativeSelectOption[];
  placeholderOption?: string;
};

export function NativeSelectField({
  id,
  label,
  hint,
  span,
  required,
  disabled,
  className,
  controlClassName,
  classNames,
  value,
  onChange,
  options,
  placeholderOption,
}: NativeSelectFieldProps) {
  return (
    <FormFieldShell
      id={id}
      label={label}
      hint={hint}
      span={span}
      className={className}
      classNames={classNames}
    >
      <select
        id={id}
        className={controlClassName}
        required={required}
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {placeholderOption !== undefined ? <option value="">{placeholderOption}</option> : null}
        {options.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
    </FormFieldShell>
  );
}

export type NativeTextAreaFieldProps = BaseNativeFieldProps & {
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  placeholder?: string;
};

export function NativeTextAreaField({
  id,
  label,
  hint,
  span = true,
  required,
  disabled,
  className,
  controlClassName,
  classNames,
  value,
  onChange,
  rows,
  placeholder,
}: NativeTextAreaFieldProps) {
  return (
    <FormFieldShell
      id={id}
      label={label}
      hint={hint}
      span={span}
      className={className}
      classNames={classNames}
    >
      <textarea
        id={id}
        className={controlClassName}
        rows={rows}
        required={required}
        disabled={disabled}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </FormFieldShell>
  );
}

export type DashboardNativeTextFieldProps = Omit<NativeTextFieldProps, "classNames">;
export type DashboardNativeSelectFieldProps = Omit<NativeSelectFieldProps, "classNames">;
export type DashboardNativeTextAreaFieldProps = Omit<NativeTextAreaFieldProps, "classNames">;

export function createDashboardNativeTextField(config: { classNames: FormFieldShellClassNames }) {
  return function DashboardNativeTextField(props: DashboardNativeTextFieldProps) {
    return <NativeTextField classNames={config.classNames} {...props} />;
  };
}

export function createDashboardNativeSelectField(config: { classNames: FormFieldShellClassNames }) {
  return function DashboardNativeSelectField(props: DashboardNativeSelectFieldProps) {
    return <NativeSelectField classNames={config.classNames} {...props} />;
  };
}

export function createDashboardNativeTextAreaField(config: {
  classNames: FormFieldShellClassNames;
}) {
  return function DashboardNativeTextAreaField(props: DashboardNativeTextAreaFieldProps) {
    return <NativeTextAreaField classNames={config.classNames} {...props} />;
  };
}

export function createDashboardNativeFormFields(config: { classNames: FormFieldShellClassNames }) {
  return {
    FormFieldShell: createDashboardFormFieldShell({ classNames: config.classNames }),
    TextField: createDashboardNativeTextField({ classNames: config.classNames }),
    SelectField: createDashboardNativeSelectField({ classNames: config.classNames }),
    TextAreaField: createDashboardNativeTextAreaField({ classNames: config.classNames }),
  };
}
