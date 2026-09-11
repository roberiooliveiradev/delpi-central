import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type PageHeroHighlightTone = "neutral" | "warning" | "danger";

export type PageHeroDensity = "comfortable" | "compact";

export type PageHeroHighlight = {
  id: string;
  label: ReactNode;
  value: ReactNode;
  /** Tom visual do tile (ex.: atrasos > 0 → warning). */
  tone?: PageHeroHighlightTone;
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
  actions: string;
  highlights: string;
  highlight: string;
  highlightTone: (tone: Exclude<PageHeroHighlightTone, "neutral">) => string;
  highlightLabel: string;
  highlightValue: string;
  body: string;
};

export type PageHeroProps = {
  classNames: PageHeroClassNames;
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  badge?: ReactNode;
  /** Ações à direita do headline (ex.: Atualizar). */
  actions?: ReactNode;
  highlights?: PageHeroHighlight[];
  /** Faixa inferior (filtros, chips, escopo). Preferir fora do hero em listas densas. */
  children?: ReactNode;
  /** Densidade vertical — `compact` reduz padding/título/highlights. */
  density?: PageHeroDensity;
  className?: string;
  "aria-label"?: string;
};

export function pageHeroBemClasses(prefix: string): PageHeroClassNames {
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  const base = `${prefix}-page-hero`;
  const ui = "delpi-ui-page-hero";
  return {
    root: pair(base, ui),
    glow: pair(`${base}__glow`, `${ui}__glow`),
    content: pair(`${base}__content`, `${ui}__content`),
    eyebrow: pair(`${base}__eyebrow`, `${ui}__eyebrow`),
    headline: pair(`${base}__headline`, `${ui}__headline`),
    title: pair(`${base}__title`, `${ui}__title`),
    description: pair(`${base}__description`, `${ui}__description`),
    badge: pair(`${base}__badge`, `${ui}__badge`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    highlights: pair(`${base}__highlights`, `${ui}__highlights`),
    highlight: pair(`${base}__highlight`, `${ui}__highlight`),
    highlightTone: (tone) =>
      pair(
        `${base}__highlight ${base}__highlight--${tone}`,
        `${ui}__highlight ${ui}__highlight--${tone}`,
      ),
    highlightLabel: pair(`${base}__highlight-label`, `${ui}__highlight-label`),
    highlightValue: pair(`${base}__highlight-value`, `${ui}__highlight-value`),
    body: pair(`${base}__body`, `${ui}__body`),
  };
}

export function PageHero({
  classNames,
  eyebrow,
  title,
  description,
  badge,
  actions,
  highlights,
  children,
  density = "comfortable",
  className,
  "aria-label": ariaLabel,
}: PageHeroProps) {
  const rootClass = [
    density === "compact" ? withBemModifier(classNames.root, "compact") : classNames.root,
    className,
  ]
    .filter(Boolean)
    .join(" ");
  const hasHighlights = Boolean(highlights?.length);

  return (
    <section className={rootClass} aria-label={ariaLabel} data-density={density}>
      <span className={classNames.glow} aria-hidden="true" />
      <div className={classNames.content}>
        {eyebrow ? <p className={classNames.eyebrow}>{eyebrow}</p> : null}
        <div className={classNames.headline}>
          <h1 className={classNames.title}>{title}</h1>
          {badge ? <div className={classNames.badge}>{badge}</div> : null}
          {actions ? <div className={classNames.actions}>{actions}</div> : null}
        </div>
        {description ? <p className={classNames.description}>{description}</p> : null}
        {hasHighlights ? (
          <div className={classNames.highlights}>
            {highlights!.map((item) => {
              const tone = item.tone && item.tone !== "neutral" ? item.tone : null;
              const tileClass = tone ? classNames.highlightTone(tone) : classNames.highlight;
              return (
                <div key={item.id} className={tileClass} data-tone={item.tone ?? "neutral"}>
                  <span className={classNames.highlightLabel}>{item.label}</span>
                  <span className={classNames.highlightValue}>{item.value}</span>
                </div>
              );
            })}
          </div>
        ) : null}
        {children ? <div className={classNames.body}>{children}</div> : null}
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
