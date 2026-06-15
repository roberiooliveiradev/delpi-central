import type { ReactNode } from "react";

export type DetailField = {
  label: string;
  value: ReactNode;
  wide?: boolean;
};

type DetailFieldGridProps = {
  fields: DetailField[];
};

export function DetailFieldGrid({ fields }: DetailFieldGridProps) {
  if (fields.length === 0) {
    return <p className="dq-detail__empty">Sem dados.</p>;
  }

  return (
    <dl className="dq-detail-grid">
      {fields.map((field) => (
        <div
          key={field.label}
          className={
            field.wide
              ? "dq-detail-grid__item dq-detail-grid__item--wide"
              : "dq-detail-grid__item"
          }
        >
          <dt>{field.label}</dt>
          <dd>{field.value}</dd>
        </div>
      ))}
    </dl>
  );
}
