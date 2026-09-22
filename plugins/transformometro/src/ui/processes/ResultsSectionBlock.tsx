import type { ReactNode } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

type Props = {
  id: string;
  title: string;
  titleId?: string;
  help?: string;
  helper?: string;
  action?: ReactNode;
  children: ReactNode;
};

/** Section shell for Results — title, optional help, helper, action, content. */
export function ResultsSectionBlock({
  id,
  title,
  titleId,
  help,
  helper,
  action,
  children,
}: Props) {
  const headingId = titleId ?? `tm-results-section-${id}`;
  return (
    <section
      className="tm-processo-results-block"
      data-results-block={id}
      aria-labelledby={headingId}
    >
      <div className="tm-processo-results-block__head">
        <div className="tm-processo-results-block__title-row">
          <h3 id={headingId} className="ds-subsection-title tm-processo-results-block__title">
            {title}
          </h3>
          {help ? (
            <HelpTooltip content={help} ariaLabel={`Ajuda: ${title}`} placement="bottom" />
          ) : null}
        </div>
        {action ? <div className="tm-processo-results-block__action">{action}</div> : null}
      </div>
      {helper ? <p className="tm-processo-results-block__helper">{helper}</p> : null}
      {children}
    </section>
  );
}
