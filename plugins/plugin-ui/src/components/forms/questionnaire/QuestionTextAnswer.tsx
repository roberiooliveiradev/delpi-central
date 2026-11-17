import { delpiUiClass } from "../../../utils/delpiUiClass";
import { TextAreaField, type TextAreaFieldClassNames } from "../TextAreaField";

export type QuestionTextAnswerProps = {
  id?: string;
  /** Rótulo visível do campo. */
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  maxLength?: number;
  disabled?: boolean;
  /** Id de elemento que descreve o grupo (ex.: erro do cartão). */
  describedBy?: string;
  prefix?: string;
  className?: string;
};

/**
 * Campo de resposta aberta sobre o `TextAreaField` existente (intacto).
 * Como o componente base não repassa `aria-*` ao `textarea` (resíduo R7),
 * `describedBy` vai para um envoltório `role="group"`; o erro da pergunta
 * já é anunciado pelo `aria-describedby` do `fieldset` do QuestionCard.
 * Aparência: classes `.delpi-ui-form-textanswer*` no escopo do formulário.
 */
export function QuestionTextAnswer({
  id,
  label,
  hint,
  value,
  onChange,
  placeholder,
  rows = 4,
  maxLength,
  disabled = false,
  describedBy,
  prefix = "ds",
  className,
}: QuestionTextAnswerProps) {
  const cn = (suffix: string) =>
    delpiUiClass(
      `${prefix}-form-textanswer${suffix}`,
      `delpi-ui-form-textanswer${suffix}`,
    );

  const control = cn("__control");
  const classNames: TextAreaFieldClassNames = {
    root: cn(""),
    labelWrapper: cn("__label"),
    fieldLabel: "",
    control,
    required: cn("__required"),
    fullWidthModifier: cn("--full"),
    controlTextarea: `${control} ${cn("__control--textarea")}`,
  };

  return (
    <div role="group" aria-describedby={describedBy}>
      <TextAreaField
        id={id}
        label={label}
        hint={hint}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={rows}
        maxLength={maxLength}
        disabled={disabled}
        className={className}
        classNames={classNames}
      />
    </div>
  );
}
