import { delpiUiClass } from "../../../utils/delpiUiClass";

export type NotApplicableOptionProps = {
  /** Mesmo `name` do grupo `RatingScale` — a exclusividade é nativa. */
  name: string;
  /** Texto visível e nome acessível da opção. */
  label: string;
  checked?: boolean;
  onChange?: () => void;
  disabled?: boolean;
  /** Borda `--delpi-ui-danger` + `aria-invalid` no `input`. */
  invalid?: boolean;
  prefix?: string;
  className?: string;
};

/**
 * Opção "não se aplica": pílula do MESMO grupo `radio` da RatingScale
 * (nunca controle independente). O `input` fica recortado (focável) e o
 * visual vem do `:has()` sobre o `label`.
 */
export function NotApplicableOption({
  name,
  label,
  checked = false,
  onChange,
  disabled = false,
  invalid = false,
  prefix = "ds",
  className,
}: NotApplicableOptionProps) {
  const cn = (suffix: string) =>
    delpiUiClass(`${prefix}-form-na${suffix}`, `delpi-ui-form-na${suffix}`);

  return (
    <label
      className={[
        cn(""),
        invalid ? cn("--invalid") : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <input
        type="radio"
        name={name}
        className={cn("__input")}
        checked={checked}
        onChange={() => onChange?.()}
        disabled={disabled}
        aria-invalid={invalid || undefined}
      />
      <span className={cn("__indicator")} aria-hidden="true" />
      <span className={cn("__text")}>{label}</span>
    </label>
  );
}
