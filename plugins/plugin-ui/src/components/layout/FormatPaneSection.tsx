import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type FormatPaneSectionProps = {
  title: string;
  /** Balão explicativo no título da seção (ícone de ajuda). */
  hint?: string;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
};

/** Seção recolhível do painel de formatação (estilo «Preenchimento» / «Linha» no PowerPoint). */
export function FormatPaneSection({
  title,
  hint,
  defaultOpen = true,
  children,
  className,
}: FormatPaneSectionProps) {
  const rootClass = ["delpi-ui-format-pane__section", className].filter(Boolean).join(" ");

  return (
    <details className={rootClass} open={defaultOpen}>
      <summary className="delpi-ui-format-pane__section-summary">
        <span className="delpi-ui-format-pane__section-title-row">
          <span className="delpi-ui-format-pane__section-title-text">{title}</span>
          {hint ? (
            <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} placement="bottom" />
          ) : null}
        </span>
      </summary>
      <div className="delpi-ui-format-pane__section-body">{children}</div>
    </details>
  );
}
