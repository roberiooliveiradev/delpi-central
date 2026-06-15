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
    return <p className="ef-detail__empty">Sem dados.</p>;
  }

  return (
    <dl className="ef-detail-grid">
      {fields.map((field) => (
        <div
          key={field.label}
          className={field.wide ? "ef-detail-grid__item ef-detail-grid__item--wide" : "ef-detail-grid__item"}
        >
          <dt>{field.label}</dt>
          <dd>{field.value}</dd>
        </div>
      ))}
    </dl>
  );
}
