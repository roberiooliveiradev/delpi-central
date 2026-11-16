import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../../utils/delpiUiClass";

export type FormPageLayoutBand = "compact" | "tall";

export type FormPageLayoutProps = {
  /**
   * Altura da faixa da marca e sobreposição da coluna:
   * `compact` (padrão) — faixa 112 px e coluna sobreposta em 80 px;
   * `tall` — faixa 168 px e coluna sobreposta em 112 px.
   * A partir de 600 px a faixa tem 220 px e a sobreposição 160 px.
   */
  band?: FormPageLayoutBand;
  /** Prefixo BEM do consumidor (dual-class com `delpi-ui-form-page*`). */
  prefix?: string;
  className?: string;
  children: ReactNode;
};

/**
 * Estrutura de página do kit de formulário: faixa da marca no topo +
 * coluna de conteúdo sobreposta (16 px de margem lateral; máx. 760 px
 * centralizada a partir de 600 px). Ocupa a altura da janela. Os tokens
 * `--delpi-ui-form-*` vêm de `QuestionnaireThemeScope` (`.delpi-ui-form-root`).
 */
export function FormPageLayout({
  band = "compact",
  prefix = "ds",
  className,
  children,
}: FormPageLayoutProps) {
  const page = `${prefix}-form-page`;
  const rootClass = [
    withBemModifier(
      delpiUiClass(page, "delpi-ui-form-page"),
      `band-${band}`,
    ),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <div
        className={delpiUiClass(`${page}__band`, "delpi-ui-form-page__band")}
        aria-hidden="true"
      />
      <div
        className={delpiUiClass(
          `${page}__column`,
          "delpi-ui-form-page__column",
        )}
      >
        {children}
      </div>
    </div>
  );
}
