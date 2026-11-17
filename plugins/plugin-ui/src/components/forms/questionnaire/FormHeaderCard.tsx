import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";
import { FormCard } from "./FormCard";
import { FormProgress } from "./FormProgress";

export type FormHeaderCardStep = {
  /** Rótulo da etapa à esquerda (ex.: "Etapa 1 de 3 · Avaliação"). */
  label: ReactNode;
  /** Texto do progresso à direita (ex.: "3 de 12"). */
  progressLabel: ReactNode;
};

export type FormHeaderCardProgress = {
  done: number;
  total: number;
  ariaLabel: string;
};

export type FormHeaderCardProps = {
  /** Já pronto (ex.: `FormLogo`). */
  logo: ReactNode;
  /** Metadado à direita do logo (ex.: prazo) — visível só ≥ 600 px. */
  meta?: ReactNode;
  /** Ação à direita (ex.: `FormThemeToggle`). */
  headerAction?: ReactNode;
  title: ReactNode;
  subtitle?: ReactNode;
  /** Linha da etapa + texto do progresso (uma única vez, antes da barra). */
  step?: FormHeaderCardStep;
  /** Barra de progresso (sem rótulo duplicado). */
  progress?: FormHeaderCardProgress;
  prefix?: string;
  className?: string;
};

/**
 * Cartão de cabeçalho das etapas/revisão: linha de logo (+ meta/ação),
 * título, subtítulo, divisor, linha da etapa e barra de progresso.
 */
export function FormHeaderCard({
  logo,
  meta,
  headerAction,
  title,
  subtitle,
  step,
  progress,
  prefix = "ds",
  className,
}: FormHeaderCardProps) {
  const cn = (suffix: string) =>
    delpiUiClass(
      `${prefix}-form-header${suffix}`,
      `delpi-ui-form-header${suffix}`,
    );

  return (
    <FormCard prefix={prefix} className={className}>
      <div className={cn("__top")}>
        {logo}
        {(meta != null || headerAction != null) && (
          <div className={cn("__end")}>
            {meta != null && <span className={cn("__meta")}>{meta}</span>}
            {headerAction}
          </div>
        )}
      </div>
      <h1 className={cn("__title")}>{title}</h1>
      {subtitle != null && <p className={cn("__subtitle")}>{subtitle}</p>}
      {(step != null || progress != null) && (
        <div className={cn("__divider")} aria-hidden="true" />
      )}
      {step != null && (
        <div className={cn("__step")}>
          <span className={cn("__step-label")}>{step.label}</span>
          <span className={cn("__step-progress")}>{step.progressLabel}</span>
        </div>
      )}
      {progress != null && (
        <FormProgress
          done={progress.done}
          total={progress.total}
          ariaLabel={progress.ariaLabel}
          prefix={prefix}
        />
      )}
    </FormCard>
  );
}
