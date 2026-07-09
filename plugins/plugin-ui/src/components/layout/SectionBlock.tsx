import type { PropsWithChildren, ReactNode } from "react";

export type SectionBlockClassNames = {
  root: string;
  header: string;
  title: string;
  description: string;
  aside: string;
  content: string;
};

export type SectionBlockProps = PropsWithChildren<{
  title: string;
  description?: string;
  aside?: ReactNode;
  className?: string;
  classNames: SectionBlockClassNames;
}>;

export function sectionBlockBemClasses(prefix: string): SectionBlockClassNames {
  const base = `${prefix}-section-block`;

  return {
    root: base,
    header: `${base}__header`,
    title: `${base}__title`,
    description: `${base}__description`,
    aside: `${base}__aside`,
    content: `${base}__content`,
  };
}

export function SectionBlock({
  title,
  description,
  aside,
  children,
  className,
  classNames,
}: SectionBlockProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <section className={rootClass}>
      <div className={classNames.header}>
        <div>
          <h2 className={classNames.title}>{title}</h2>
          {description ? <p className={classNames.description}>{description}</p> : null}
        </div>
        {aside ? <div className={classNames.aside}>{aside}</div> : null}
      </div>
      <div className={classNames.content}>{children}</div>
    </section>
  );
}

export type DashboardSectionBlockProps = Omit<SectionBlockProps, "classNames">;

export function createDashboardSectionBlock(config: { prefix: string }) {
  const classNames = sectionBlockBemClasses(config.prefix);

  return function DashboardSectionBlock(props: DashboardSectionBlockProps) {
    return <SectionBlock classNames={classNames} {...props} />;
  };
}
