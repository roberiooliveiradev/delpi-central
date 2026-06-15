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
  return (
    <dl className="dp-detail-grid">
      {fields.map((field) => (
        <div
          key={field.label}
          className={`dp-detail-grid__item${
            field.wide ? " dp-detail-grid__item--wide" : ""
          }`}
        >
          <dt>{field.label}</dt>
          <dd>{field.value ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}
