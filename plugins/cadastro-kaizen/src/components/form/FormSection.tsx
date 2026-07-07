import type { ReactNode } from "react";

import { HelpTooltip } from "@delpi/plugin-ui";

type FormSectionProps = {
  title: string;
  hint?: string;
  description?: string;
  children: ReactNode;
  headerActions?: ReactNode;
};

/** Seção de formulário em card, no mesmo padrão visual da ficha de edição. */
export function FormSection({ title, hint, description, children, headerActions }: FormSectionProps) {
  return (
    <section className="kz-card kz-section-card">
      <header className="kz-section-card__header">
        <div>
          <h2 className="kz-section-card__title">
            {title}
            {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} /> : null}
          </h2>
          {description ? <p className="kz-section-card__desc">{description}</p> : null}
        </div>
        {headerActions ? <div className="kz-section-card__actions">{headerActions}</div> : null}
      </header>
      <div className="kz-form-grid">{children}</div>
    </section>
  );
}
