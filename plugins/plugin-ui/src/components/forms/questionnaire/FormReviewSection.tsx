import { Pencil } from "lucide-react";
import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

import { FormCard } from "./FormCard";

export type FormReviewRowData = {
  label: ReactNode;
  value: ReactNode;
  /** Valor em itálico e `--delpi-ui-muted` (ex.: resposta vazia). */
  muted?: boolean;
  /** Rótulo acima e valor abaixo, preservando quebras de linha. */
  block?: boolean;
};

export type FormReviewRowProps = FormReviewRowData & {
  prefix?: string;
};

/** Uma linha `dt`/`dd` da revisão (par rótulo/valor). */
export function FormReviewRow({
  label,
  value,
  muted = false,
  block = false,
  prefix = "ds",
}: FormReviewRowProps) {
  const cn = (suffix: string) =>
    delpiUiClass(
      `${prefix}-form-review${suffix}`,
      `delpi-ui-form-review${suffix}`,
    );
  return (
    <div
      className={[
        cn("__row"),
        muted ? cn("__row--muted") : "",
        block ? cn("__row--block") : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <dt className={cn("__label")}>{label}</dt>
      <dd className={cn("__value")}>{value}</dd>
    </div>
  );
}

export type FormReviewSectionProps = {
  title: ReactNode;
  /** Ação de edição da seção (ícone de lápis, nome acessível próprio). */
  edit: {
    label: ReactNode;
    ariaLabel: string;
    onClick: () => void;
  };
  rows: FormReviewRowData[];
  /** Prefixo BEM do consumidor (dual-class). */
  prefix?: string;
  className?: string;
};

/**
 * Seção da etapa de revisão sobre `FormCard`: título + ação "Editar" e uma
 * lista de descrição (`dl`/`dt`/`dd`) com os valores informados. Sem lógica
 * de navegação — `edit.onClick` é callback do consumidor.
 */
export function FormReviewSection({
  title,
  edit,
  rows,
  prefix = "ds",
  className,
}: FormReviewSectionProps) {
  const cn = (suffix: string) =>
    delpiUiClass(
      `${prefix}-form-review${suffix}`,
      `delpi-ui-form-review${suffix}`,
    );

  return (
    <FormCard className={[cn(""), className].filter(Boolean).join(" ")}>
      <div className={cn("__head")}>
        <h3 className={cn("__title")}>{title}</h3>
        <button
          type="button"
          className={cn("__edit")}
          aria-label={edit.ariaLabel}
          onClick={edit.onClick}
        >
          <Pencil size={16} aria-hidden="true" />
          <span className={cn("__edit-label")}>{edit.label}</span>
        </button>
      </div>
      <dl className={cn("__rows")}>
        {rows.map((row, index) => (
          <FormReviewRow key={index} {...row} prefix={prefix} />
        ))}
      </dl>
    </FormCard>
  );
}
