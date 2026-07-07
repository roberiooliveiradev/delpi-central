import type { ReactNode } from "react";

export type PanelCardClassNames = {
  section: string;
  sectionHighlight: string;
};

export type PanelCardProps = {
  title: string;
  children: ReactNode;
  highlight?: boolean;
  classNames: PanelCardClassNames;
  className?: string;
  titleLevel?: 2 | 3;
};

export function panelCardBemClasses(prefix: string): PanelCardClassNames {
  const card = `${prefix}-card`;

  return {
    section: card,
    sectionHighlight: `${card} ${card}--highlight`,
  };
}

export function PanelCard({
  title,
  children,
  highlight = false,
  classNames,
  className,
  titleLevel = 2,
}: PanelCardProps) {
  const TitleTag = titleLevel === 3 ? "h3" : "h2";
  const sectionClass = [highlight ? classNames.sectionHighlight : classNames.section, className]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={sectionClass}>
      <TitleTag>{title}</TitleTag>
      {children}
    </section>
  );
}

export type DashboardPanelCardProps = Omit<PanelCardProps, "classNames">;

export function createPanelCard(prefix: string) {
  const classNames = panelCardBemClasses(prefix);

  return function DashboardPanelCard(props: DashboardPanelCardProps) {
    return <PanelCard classNames={classNames} {...props} />;
  };
}
