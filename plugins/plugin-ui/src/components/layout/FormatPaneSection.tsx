import { useState, type ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type FormatPaneSectionProps = {
  title: string;
  /** Balão explicativo no título da seção (ícone de ajuda). */
  hint?: string;
  /** Só o estado inicial — o pai não controla `open` (senão o chevron não fecha). */
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
  const [open, setOpen] = useState(defaultOpen);
  const rootClass = ["delpi-ui-format-pane__section", className].filter(Boolean).join(" ");

  return (
    <details className={rootClass} open={open}>
      <summary
        className="delpi-ui-format-pane__section-summary"
        onClick={(event) => {
          event.preventDefault();
          setOpen((current) => !current);
        }}
      >
        <span className="delpi-ui-format-pane__section-title-row">
          <span className="delpi-ui-format-pane__section-title-text">{title}</span>
          {hint ? (
            <span
              onClick={(event) => event.stopPropagation()}
              onKeyDown={(event) => event.stopPropagation()}
            >
              <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} placement="bottom" />
            </span>
          ) : null}
        </span>
      </summary>
      <div className="delpi-ui-format-pane__section-body">{children}</div>
    </details>
  );
}
