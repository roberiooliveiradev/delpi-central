import type { ReactNode } from "react";

export type SimpleKpiCardClassNames = {
  article: string;
  icon: string;
  body?: string;
  title: string;
  value: string;
  subtitle?: string;
};

export type SimpleKpiCardProps = {
  title: string;
  value: string;
  icon: ReactNode;
  loading?: boolean;
  subtitle?: string;
  variant?: string;
  valueTag?: "h3" | "p";
  classNames: SimpleKpiCardClassNames;
  className?: string;
};

export function simpleKpiCardBemClasses(
  prefix: string,
  block = "kpi-card",
  options?: { withBody?: boolean; withSubtitle?: boolean },
): SimpleKpiCardClassNames {
  const card = `${prefix}-${block}`;

  return {
    article: `${prefix}-card ${card}`,
    icon: `${card}__icon`,
    body: options?.withBody ? `${card}__body` : undefined,
    title: `${card}__title`,
    value: `${card}__value`,
    subtitle: options?.withSubtitle ? `${card}__subtitle` : undefined,
  };
}

export function simpleKpiCardVariantClass(prefix: string, variant: string, block = "kpi-card") {
  return `${prefix}-${block}--${variant}`;
}

export function SimpleKpiCard({
  title,
  value,
  icon,
  loading = false,
  subtitle,
  valueTag = "h3",
  classNames,
  className,
}: SimpleKpiCardProps) {
  const articleClass = [classNames.article, className].filter(Boolean).join(" ");
  const ValueTag = valueTag;

  const content = (
    <>
      <p className={classNames.title}>{title}</p>
      <ValueTag className={classNames.value}>{loading ? "…" : value}</ValueTag>
      {subtitle && classNames.subtitle ? (
        <span className={classNames.subtitle}>{subtitle}</span>
      ) : null}
    </>
  );

  return (
    <article className={articleClass}>
      <div className={classNames.icon} aria-hidden="true">
        {icon}
      </div>
      {classNames.body ? <div className={classNames.body}>{content}</div> : <div>{content}</div>}
    </article>
  );
}

export type DashboardSimpleKpiCardProps = Omit<SimpleKpiCardProps, "classNames">;

export function createSimpleKpiCard(
  prefix: string,
  options?: {
    withBody?: boolean;
    withSubtitle?: boolean;
    defaultValueTag?: "h3" | "p";
  },
) {
  const classNames = simpleKpiCardBemClasses(prefix, "kpi-card", {
    withBody: options?.withBody,
    withSubtitle: options?.withSubtitle,
  });
  const defaultValueTag = options?.defaultValueTag ?? "h3";

  return function DashboardSimpleKpiCard({
    variant,
    className,
    valueTag,
    ...props
  }: DashboardSimpleKpiCardProps) {
    const variantClass = variant ? simpleKpiCardVariantClass(prefix, variant) : undefined;
    const mergedClassName = [variantClass, className].filter(Boolean).join(" ") || undefined;

    return (
      <SimpleKpiCard
        classNames={classNames}
        className={mergedClassName}
        valueTag={valueTag ?? defaultValueTag}
        {...props}
      />
    );
  };
}
