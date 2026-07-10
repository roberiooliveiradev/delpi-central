import type { ReactNode } from "react";

export type FormatPaneSectionProps = {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
};

/** Seção recolhível do painel de formatação (estilo «Preenchimento» / «Linha» no PowerPoint). */
export function FormatPaneSection({
  title,
  defaultOpen = true,
  children,
  className,
}: FormatPaneSectionProps) {
  const rootClass = ["delpi-ui-format-pane__section", className].filter(Boolean).join(" ");

  return (
    <details className={rootClass} open={defaultOpen}>
      <summary className="delpi-ui-format-pane__section-summary">{title}</summary>
      <div className="delpi-ui-format-pane__section-body">{children}</div>
    </details>
  );
}
