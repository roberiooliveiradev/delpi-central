import { NativeSelectControl, type NativeSelectOption } from "@delpi/plugin-ui";

type ChatRichUxSelectProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly NativeSelectOption[];
  placeholderOption?: string;
  /** Quando false, não inclui opção vazia inicial. */
  allowEmptyOption?: boolean;
  title?: string;
  className?: string;
};

/** Select compacto da toolbar de apresentação rica (tabela/gráfico). */
export function ChatRichUxSelect({
  label,
  value,
  onChange,
  options,
  placeholderOption = "Todos",
  allowEmptyOption = true,
  title,
  className = "mdc-rich-chart__ux-field",
}: ChatRichUxSelectProps) {
  return (
    <label className={className} title={title}>
      <span>{label}</span>
      <NativeSelectControl
        value={value}
        onChange={onChange}
        options={options}
        {...(allowEmptyOption ? { placeholderOption } : {})}
        aria-label={label}
      />
    </label>
  );
}
