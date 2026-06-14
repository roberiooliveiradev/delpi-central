import type { ReactNode } from "react";

type InfoCardProps = {
  title: string;
  children: ReactNode;
  highlight?: boolean;
};

export function InfoCard({ title, children, highlight = false }: InfoCardProps) {
  return (
    <section className={`pc-card${highlight ? " pc-card--highlight" : ""}`}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

type InfoGridProps = {
  items: Array<{ label: string; value: string; wide?: boolean }>;
};

export function InfoGrid({ items }: InfoGridProps) {
  return (
    <dl className="pc-info-grid">
      {items.map((item) => (
        <div
          key={item.label}
          className={`pc-info-grid__item${item.wide ? " pc-info-grid__item--wide" : ""}`}
        >
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
