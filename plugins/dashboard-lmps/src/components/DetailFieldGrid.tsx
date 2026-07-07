import type { ReactNode } from "react";

import { HelpTooltip } from "@delpi/plugin-ui";

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
    return <p className="lmps-detail__empty">Sem dados.</p>;
  }

  return (
    <dl className="lmps-detail-grid">
      {fields.map((field) => (
        <div
          key={field.label}
          className={
            field.wide
              ? "lmps-detail-grid__item lmps-detail-grid__item--wide"
              : "lmps-detail-grid__item"
          }
        >
          <dt>
            <span className="lmps-detail-grid__label">
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
