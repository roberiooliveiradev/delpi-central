import type { ReactNode } from "react";

export type SimpleKpiCardClassNames = {
  article: string;
  icon: string;
  header?: string;
  body?: string;
  title: string;
  value: string;
  valueDanger?: string;
  subtitle?: string;
};

export type SimpleKpiCardLayout = "iconStart" | "iconEnd";

export type SimpleKpiCardProps = {
  title: string;
  value: string;
  icon: ReactNode;
  loading?: boolean;
  subtitle?: string;
  variant?: string;
  wide?: boolean;
  valueTone?: "default" | "danger";
  valueTag?: "h3" | "p";
  layout?: SimpleKpiCardLayout;
  classNames: SimpleKpiCardClassNames;
  className?: string;
};

export function simpleKpiCardBemClasses(
  prefix: string,
  block = "kpi-card",
  options?: {
    withBody?: boolean;
    withSubtitle?: boolean;
    layout?: SimpleKpiCardLayout;
  },
): SimpleKpiCardClassNames {
  const card = `${prefix}-${block}`;

  return {
    article: `${prefix}-card ${card}`,
    icon: `${card}__icon`,
    header: options?.layout === "iconEnd" ? `${card}__header` : undefined,
    body: options?.withBody ? `${card}__body` : undefined,
    title: `${card}__title`,
    value: `${card}__value`,
    valueDanger: `${card}__value--danger`,
    subtitle: options?.withSubtitle ? `${card}__subtitle` : undefined,
  };
}

export function simpleKpiCardVariantClass(prefix: string, variant: string, block = "kpi-card") {
  return `${prefix}-${block}--${variant}`;
}

export function simpleKpiCardWideClass(prefix: string, block = "kpi-card") {
  return `${prefix}-${block}--wide`;
}

export function SimpleKpiCard({
  title,
  value,
  icon,
  loading = false,
  subtitle,
  valueTone = "default",
  valueTag = "h3",
  layout = "iconStart",
  classNames,
  className,
}: SimpleKpiCardProps) {
  const articleClass = [classNames.article, className].filter(Boolean).join(" ");
  const ValueTag = valueTag;
  const valueClassName =
    valueTone === "danger" && classNames.valueDanger
      ? `${classNames.value} ${classNames.valueDanger}`
      : classNames.value;

  const content = (
    <>
      <p className={classNames.title}>{title}</p>
      <ValueTag className={valueClassName}>{loading ? "…" : value}</ValueTag>
      {subtitle && classNames.subtitle ? (
        <span className={classNames.subtitle}>{subtitle}</span>
      ) : null}
    </>
  );

  if (layout === "iconEnd" && classNames.header) {
    return (
      <article className={articleClass}>
        <div className={classNames.header}>
          {classNames.body ? <div className={classNames.body}>{content}</div> : <div>{content}</div>}
          <div className={classNames.icon} aria-hidden="true">
            {icon}
          </div>
        </div>
      </article>
    );
  }

  return (
    <article className={articleClass}>
      <div className={classNames.icon} aria-hidden="true">
        {icon}
      </div>
      {classNames.body ? <div className={classNames.body}>{content}</div> : <div>{content}</div>}
    </article>
  );
}

export type DashboardSimpleKpiCardProps = Omit<SimpleKpiCardProps, "classNames" | "layout">;

export function createSimpleKpiCard(
  prefix: string,
  options?: {
    withBody?: boolean;
    withSubtitle?: boolean;
    defaultValueTag?: "h3" | "p";
    layout?: SimpleKpiCardLayout;
  },
) {
  const classNames = simpleKpiCardBemClasses(prefix, "kpi-card", {
    withBody: options?.withBody,
    withSubtitle: options?.withSubtitle,
    layout: options?.layout,
  });
  const defaultValueTag = options?.defaultValueTag ?? "h3";
  const layout = options?.layout ?? "iconStart";

  return function DashboardSimpleKpiCard({
    variant,
    wide,
    className,
    valueTag,
    ...props
  }: DashboardSimpleKpiCardProps) {
    const variantClass = variant ? simpleKpiCardVariantClass(prefix, variant) : undefined;
    const wideClass = wide ? simpleKpiCardWideClass(prefix) : undefined;
    const mergedClassName = [variantClass, wideClass, className].filter(Boolean).join(" ") || undefined;

    return (
      <SimpleKpiCard
        classNames={classNames}
        className={mergedClassName}
        layout={layout}
        valueTag={valueTag ?? defaultValueTag}
        {...props}
      />
    );
  };
}
