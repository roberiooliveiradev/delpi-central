import type { ReactNode } from "react";

export type SimpleKpiCardClassNames = {
  article: string;
  icon: string;
  title: string;
  value: string;
};

export type SimpleKpiCardProps = {
  title: string;
  value: string;
  icon: ReactNode;
  loading?: boolean;
  classNames: SimpleKpiCardClassNames;
  className?: string;
};

export function simpleKpiCardBemClasses(prefix: string, block = "kpi-card"): SimpleKpiCardClassNames {
  const card = `${prefix}-${block}`;

  return {
    article: `${prefix}-card ${card}`,
    icon: `${card}__icon`,
    title: `${card}__title`,
    value: `${card}__value`,
  };
}

export function SimpleKpiCard({
  title,
  value,
  icon,
  loading = false,
  classNames,
  className,
}: SimpleKpiCardProps) {
  const articleClass = [classNames.article, className].filter(Boolean).join(" ");

  return (
    <article className={articleClass}>
      <div className={classNames.icon} aria-hidden="true">
        {icon}
      </div>
      <div>
        <p className={classNames.title}>{title}</p>
        <h3 className={classNames.value}>{loading ? "…" : value}</h3>
      </div>
    </article>
  );
}

export type DashboardSimpleKpiCardProps = Omit<SimpleKpiCardProps, "classNames">;

export function createSimpleKpiCard(prefix: string) {
  const classNames = simpleKpiCardBemClasses(prefix);

  return function DashboardSimpleKpiCard(props: DashboardSimpleKpiCardProps) {
    return <SimpleKpiCard classNames={classNames} {...props} />;
  };
}
