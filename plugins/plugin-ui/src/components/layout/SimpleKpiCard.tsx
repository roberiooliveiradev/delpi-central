import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type SimpleKpiCardClassNames = {
  article: string;
  icon: string;
  header?: string;
  body?: string;
  title: string;
  titleHelp?: string;
  value: string;
  valueDanger?: string;
  subtitle?: string;
};

export type SimpleKpiCardLayout = "iconStart" | "iconEnd";

export type SimpleKpiCardProps = {
  title: string;
  /** Ajuda no hover do texto do título (HelpTooltip wrap — sem ícone ?). */
  titleHint?: string;
  value: string;
  icon: ReactNode;
  loading?: boolean;
  subtitle?: string;
  variant?: string;
  wide?: boolean;
  valueTone?: "default" | "danger";
  /** Classe extra no wrapper do ícone (ex.: tom danger/warning/success). */
  iconClassName?: string;
  valueTag?: "h3" | "p" | "strong";
  layout?: SimpleKpiCardLayout;
  classNames: SimpleKpiCardClassNames;
  className?: string;
  /** Torna o card acionável (deep link / drill-down). */
  onClick?: () => void;
  /** Rótulo acessível quando `onClick` está definido. */
  "aria-label"?: string;
  /** Estado selecionado (filtro KPI acionável). */
  pressed?: boolean;
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
  const ui = "delpi-ui-kpi-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    article: pair(`${prefix}-card ${card}`, `delpi-ui-card ${ui}`),
    icon: pair(`${card}__icon`, "delpi-ui-kpi-icon"),
    header: options?.layout === "iconEnd" ? pair(`${card}__header`, `${ui}__header`) : undefined,
    body: options?.withBody ? pair(`${card}__body`, `${ui}__body`) : undefined,
    title: pair(`${card}__title`, "delpi-ui-kpi-title"),
    titleHelp: pair(`${card}__title-help`, "delpi-ui-kpi-title__help"),
    value: pair(`${card}__value`, "delpi-ui-kpi-value"),
    valueDanger: pair(`${card}__value--danger`, "delpi-ui-kpi-value--danger"),
    subtitle: options?.withSubtitle
      ? pair(`${card}__subtitle`, "delpi-ui-kpi-subtitle")
      : undefined,
  };
}

export function simpleKpiCardVariantClass(prefix: string, variant: string, block = "kpi-card") {
  return `${prefix}-${block}--${variant}`;
}

/** Tom do ícone KPI — dual-class `{prefix}-kpi-card__icon--tone` + `.delpi-ui-kpi-icon--tone`. */
export function simpleKpiCardIconToneClass(
  prefix: string,
  tone: "danger" | "warning" | "success",
  block = "kpi-card",
) {
  return delpiUiClass(`${prefix}-${block}__icon--${tone}`, `delpi-ui-kpi-icon--${tone}`);
}

export function simpleKpiCardWideClass(prefix: string, block = "kpi-card") {
  return delpiUiClass(`${prefix}-${block}--wide`, "delpi-ui-kpi-card--wide");
}

export function simpleKpiKaizenBemClasses(prefix: string): SimpleKpiCardClassNames {
  return {
    article: `${prefix}-kpi`,
    icon: `${prefix}-kpi__icon`,
    body: `${prefix}-kpi__body`,
    title: `${prefix}-kpi__label`,
    value: `${prefix}-kpi__value`,
    subtitle: `${prefix}-kpi__sub`,
  };
}

export function simpleKpiKaizenToneClass(prefix: string, tone: string) {
  return `${prefix}-kpi--${tone}`;
}

/** BEM `{prefix}-analytics-kpi` + dual `.delpi-ui-analytics-kpi*` (auditoria-5s etc.). */
export function simpleKpiAnalyticsBemClasses(prefix: string): SimpleKpiCardClassNames {
  const kpi = `${prefix}-analytics-kpi`;
  const ui = "delpi-ui-analytics-kpi";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    article: pair(kpi, ui),
    icon: pair(`${kpi}__icon`, `${ui}__icon`),
    title: pair(`${kpi}__label`, `${ui}__label`),
    value: pair(`${kpi}__value`, `${ui}__value`),
    subtitle: pair(`${kpi}__hint`, `${ui}__hint`),
  };
}

export function simpleKpiAnalyticsVariantClass(prefix: string, variant: string) {
  return delpiUiClass(
    `${prefix}-analytics-kpi--${variant}`,
    `delpi-ui-analytics-kpi--${variant}`,
  );
}

export function createAnalyticsKpiCard(prefix = "a5s") {
  const classNames = simpleKpiAnalyticsBemClasses(prefix);

  return function AnalyticsKpiCard({
    title,
    value,
    subtitle,
    icon,
    variant,
    className,
  }: {
    title: string;
    value: string;
    subtitle?: string;
    icon: ReactNode;
    variant?: string;
    className?: string;
  }) {
    const variantClass = variant ? simpleKpiAnalyticsVariantClass(prefix, variant) : undefined;
    const mergedClassName = [variantClass, className].filter(Boolean).join(" ") || undefined;

    return (
      <SimpleKpiCard
        title={title}
        value={value}
        subtitle={subtitle}
        icon={icon}
        valueTag="strong"
        classNames={classNames}
        className={mergedClassName}
      />
    );
  };
}

export function createKaizenKpiCard(prefix = "kz") {
  const classNames = simpleKpiKaizenBemClasses(prefix);

  return function KaizenStyleKpiCard({
    tone,
    label,
    value,
    sub,
    icon,
    className,
  }: {
    tone?: string;
    label: string;
    value: string;
    sub?: string;
    icon: ReactNode;
    className?: string;
  }) {
    const toneClass = tone ? simpleKpiKaizenToneClass(prefix, tone) : undefined;
    const mergedClassName = [toneClass, className].filter(Boolean).join(" ") || undefined;

    return (
      <SimpleKpiCard
        title={label}
        value={value}
        subtitle={sub}
        icon={icon}
        valueTag="h3"
        classNames={classNames}
        className={mergedClassName}
      />
    );
  };
}

export function SimpleKpiCard({
  title,
  titleHint,
  value,
  icon,
  loading = false,
  subtitle,
  valueTone = "default",
  iconClassName,
  valueTag = "h3",
  layout = "iconStart",
  classNames,
  className,
  onClick,
  "aria-label": ariaLabel,
  pressed = false,
}: SimpleKpiCardProps) {
  const interactive = typeof onClick === "function";
  const articleClass = [
    classNames.article,
    interactive ? "delpi-ui-kpi-card--interactive" : null,
    interactive && pressed ? "delpi-ui-kpi-card--pressed" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");
  const iconWrapperClass = [classNames.icon, iconClassName].filter(Boolean).join(" ");
  const ValueTag = valueTag;
  const valueClassName =
    valueTone === "danger" && classNames.valueDanger
      ? `${classNames.value} ${classNames.valueDanger}`
      : classNames.value;

  const content = (
    <>
      <p className={classNames.title}>
        {titleHint ? (
          <HelpTooltip
            content={titleHint}
            ariaLabel={`Ajuda: ${title}`}
            wrap
            placement="bottom"
          >
            <span className={classNames.titleHelp}>{title}</span>
          </HelpTooltip>
        ) : (
          title
        )}
      </p>
      <ValueTag className={valueClassName}>{loading ? "…" : value}</ValueTag>
      {subtitle && classNames.subtitle ? (
        <span className={classNames.subtitle}>{subtitle}</span>
      ) : null}
    </>
  );

  const body =
    layout === "iconEnd" && classNames.header ? (
      <div className={classNames.header}>
        {classNames.body ? <div className={classNames.body}>{content}</div> : <div>{content}</div>}
        <div className={iconWrapperClass} aria-hidden="true">
          {icon}
        </div>
      </div>
    ) : (
      <>
        <div className={iconWrapperClass} aria-hidden="true">
          {icon}
        </div>
        {classNames.body ? <div className={classNames.body}>{content}</div> : <div>{content}</div>}
      </>
    );

  if (interactive) {
    return (
      <article
        role="button"
        tabIndex={0}
        className={articleClass}
        onClick={onClick}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onClick();
          }
        }}
        aria-label={ariaLabel ?? `Abrir detalhes: ${title}`}
        aria-pressed={pressed}
      >
        {body}
      </article>
    );
  }

  return <article className={articleClass}>{body}</article>;
}

export type DashboardSimpleKpiCardProps = Omit<
  SimpleKpiCardProps,
  "classNames" | "layout" | "iconClassName"
> & {
  iconTone?: "danger" | "warning" | "success";
};

export function createSimpleKpiCard(
  prefix: string,
  options?: {
    withBody?: boolean;
    withSubtitle?: boolean;
    defaultValueTag?: "h3" | "p" | "strong";
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
    iconTone,
    ...props
  }: DashboardSimpleKpiCardProps) {
    const variantClass = variant ? simpleKpiCardVariantClass(prefix, variant) : undefined;
    const wideClass = wide ? simpleKpiCardWideClass(prefix) : undefined;
    const mergedClassName = [variantClass, wideClass, className].filter(Boolean).join(" ") || undefined;
    const iconClassName = iconTone
      ? simpleKpiCardIconToneClass(prefix, iconTone)
      : undefined;

    return (
      <SimpleKpiCard
        classNames={classNames}
        className={mergedClassName}
        layout={layout}
        valueTag={valueTag ?? defaultValueTag}
        iconClassName={iconClassName}
        {...props}
      />
    );
  };
}
