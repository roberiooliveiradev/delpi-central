import { delpiUiClass } from "../../../utils/delpiUiClass";

export type FormLogoSize = "sm" | "md" | "lg";

export type FormLogoProps = {
  src: string;
  /** Texto alternativo (obrigatório). */
  alt: string;
  /** Altura da imagem: sm 34 px, md 40 px, lg 44 px (largura automática). */
  size?: FormLogoSize;
  prefix?: string;
  className?: string;
};

/**
 * Logo do formulário dentro de um selo — transparente no claro e com fundo
 * `--delpi-ui-form-logo-bg` (branco, padding 6×10, raio 8) no escuro.
 */
export function FormLogo({
  src,
  alt,
  size = "md",
  prefix = "ds",
  className,
}: FormLogoProps) {
  const classes = [
    delpiUiClass(`${prefix}-form-logo`, "delpi-ui-form-logo"),
    delpiUiClass(
      `${prefix}-form-logo--${size}`,
      `delpi-ui-form-logo--${size}`,
    ),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={classes}>
      <img
        className={delpiUiClass(
          `${prefix}-form-logo__img`,
          "delpi-ui-form-logo__img",
        )}
        src={src}
        alt={alt}
      />
    </span>
  );
}
