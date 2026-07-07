import type { ReactNode } from "react";

export type ContentCardClassNames = {
  section: string;
  header: string;
  headerContent: string;
  headerRight: string;
  title: string;
  description: string;
  body: string;
};

export type ContentCardProps = {
  title?: string;
  description?: string;
  headerRight?: ReactNode;
  children: ReactNode;
  classNames: ContentCardClassNames;
  className?: string;
  titleLevel?: 2 | 3;
};

export function contentCardBemClasses(prefix: string): ContentCardClassNames {
  const card = `${prefix}-card`;

  return {
    section: card,
    header: `${card}__header`,
    headerContent: `${card}__header-content`,
    headerRight: `${card}__header-right`,
    title: `${card}__title`,
    description: `${card}__description`,
    body: `${card}__body`,
  };
}

export function ContentCard({
  title,
  description,
  headerRight,
  children,
  classNames,
  className,
  titleLevel = 3,
}: ContentCardProps) {
  const TitleTag = titleLevel === 2 ? "h2" : "h3";
  const sectionClass = [classNames.section, className].filter(Boolean).join(" ");
  const showHeader = Boolean(title || description || headerRight);

  return (
    <section className={sectionClass}>
      {showHeader ? (
        <header className={classNames.header}>
          <div className={classNames.headerContent}>
            {title ? <TitleTag className={classNames.title}>{title}</TitleTag> : null}
            {description ? <p className={classNames.description}>{description}</p> : null}
          </div>
          {headerRight ? <div className={classNames.headerRight}>{headerRight}</div> : null}
        </header>
      ) : null}
      <div className={classNames.body}>{children}</div>
    </section>
  );
}

export type DashboardContentCardProps = Omit<ContentCardProps, "classNames">;

export function createContentCard(prefix: string, options?: { titleLevel?: 2 | 3 }) {
  const classNames = contentCardBemClasses(prefix);
  const titleLevel = options?.titleLevel ?? 3;

  return function DashboardContentCard(props: DashboardContentCardProps) {
    return <ContentCard classNames={classNames} titleLevel={titleLevel} {...props} />;
  };
}
