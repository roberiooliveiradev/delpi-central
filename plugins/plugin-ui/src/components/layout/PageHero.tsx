import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type PageHeroHighlight = {
  id: string;
  label: ReactNode;
  value: ReactNode;
};

export type PageHeroClassNames = {
  root: string;
  glow: string;
  content: string;
  eyebrow: string;
  headline: string;
  title: string;
  description: string;
  badge: string;
  highlights: string;
  highlight: string;
  highlightLabel: string;
  highlightValue: string;
};

export type PageHeroProps = {
  classNames: PageHeroClassNames;
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  badge?: ReactNode;
  highlights?: PageHeroHighlight[];
  className?: string;
  "aria-label"?: string;
};

export function pageHeroBemClasses(prefix: string): PageHeroClassNames {
  return {
    root: delpiUiClass(`${prefix}-page-hero`, "delpi-ui-page-hero"),
    glow: delpiUiClass(`${prefix}-page-hero__glow`, "delpi-ui-page-hero__glow"),
    content: delpiUiClass(`${prefix}-page-hero__content`, "delpi-ui-page-hero__content"),
    eyebrow: delpiUiClass(`${prefix}-page-hero__eyebrow`, "delpi-ui-page-hero__eyebrow"),
    headline: delpiUiClass(`${prefix}-page-hero__headline`, "delpi-ui-page-hero__headline"),
    title: delpiUiClass(`${prefix}-page-hero__title`, "delpi-ui-page-hero__title"),
    description: delpiUiClass(
      `${prefix}-page-hero__description`,
      "delpi-ui-page-hero__description",
    ),
    badge: delpiUiClass(`${prefix}-page-hero__badge`, "delpi-ui-page-hero__badge"),
    highlights: delpiUiClass(
      `${prefix}-page-hero__highlights`,
      "delpi-ui-page-hero__highlights",
    ),
    highlight: delpiUiClass(
      `${prefix}-page-hero__highlight`,
      "delpi-ui-page-hero__highlight",
    ),
    highlightLabel: delpiUiClass(
      `${prefix}-page-hero__highlight-label`,
      "delpi-ui-page-hero__highlight-label",
    ),
    highlightValue: delpiUiClass(
      `${prefix}-page-hero__highlight-value`,
      "delpi-ui-page-hero__highlight-value",
    ),
  };
}

export function PageHero({
  classNames,
  eyebrow,
  title,
  description,
  badge,
  highlights,
  className,
  "aria-label": ariaLabel,
}: PageHeroProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const hasHighlights = Boolean(highlights?.length);

  return (
    <section className={rootClass} aria-label={ariaLabel}>
      <span className={classNames.glow} aria-hidden="true" />
      <div className={classNames.content}>
        {eyebrow ? <p className={classNames.eyebrow}>{eyebrow}</p> : null}
        <div className={classNames.headline}>
          <h1 className={classNames.title}>{title}</h1>
          {badge ? <div className={classNames.badge}>{badge}</div> : null}
        </div>
        {description ? <p className={classNames.description}>{description}</p> : null}
        {hasHighlights ? (
          <div className={classNames.highlights}>
            {highlights!.map((item) => (
              <div key={item.id} className={classNames.highlight}>
                <span className={classNames.highlightLabel}>{item.label}</span>
                <span className={classNames.highlightValue}>{item.value}</span>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}

export type DashboardPageHeroProps = Omit<PageHeroProps, "classNames">;

export function createDashboardPageHero(config: { prefix: string }) {
  const classNames = pageHeroBemClasses(config.prefix);
  return function DashboardPageHero(props: DashboardPageHeroProps) {
    return <PageHero classNames={classNames} {...props} />;
  };
}
