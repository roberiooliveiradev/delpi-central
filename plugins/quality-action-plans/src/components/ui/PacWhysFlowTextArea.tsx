import { NativeTextAreaControl } from "@delpi/plugin-ui";

type Props = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  ariaLabel: string;
  id: string;
  rows?: number;
  disabled?: boolean;
  className?: string;
};

/** Textarea compacto do fluxo horizontal 5 Whys (sem FormFieldShell). */
export function PacWhysFlowTextArea({
  value,
  onChange,
  placeholder,
  ariaLabel,
  id,
  rows = 2,
  disabled = false,
  className,
}: Props) {
  return (
    <NativeTextAreaControl
      id={id}
      className={className}
      value={value}
      rows={rows}
      placeholder={placeholder}
      disabled={disabled}
      aria-label={ariaLabel}
      onChange={onChange}
    />
  );
}
