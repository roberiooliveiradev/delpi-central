import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

export type DetailField = {
  label: string;
  hint?: string;
  value: ReactNode;
  wide?: boolean;
};

type DetailFieldGridProps = {
  fields: DetailField[];
};

export function DetailFieldGrid({ fields }: DetailFieldGridProps) {
  if (fields.length === 0) {
    return <p className="dc-detail__empty">Sem dados.</p>;
  }

  return (
    <dl className="dc-detail-grid">
      {fields.map((field) => (
        <div
          key={field.label}
          className={
            field.wide
              ? "dc-detail-grid__item dc-detail-grid__item--wide"
              : "dc-detail-grid__item"
          }
        >
          <dt>
            <span className="dc-detail-grid__label">
              {field.label}
              {field.hint ? (
                <HelpTooltip
                  content={field.hint}
                  ariaLabel={`Ajuda: ${field.label}`}
                />
              ) : null}
            </span>
          </dt>
          <dd>{field.value}</dd>
        </div>
      ))}
    </dl>
  );
}
