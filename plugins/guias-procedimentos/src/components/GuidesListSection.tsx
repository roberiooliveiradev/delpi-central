import type { ReactNode } from "react";

type GuidesListSectionProps = {
  title: string;
  titleId?: string;
  children: ReactNode;
};

export function GuidesListSection({
  title,
  titleId = "gp-guides-list-title",
  children,
}: GuidesListSectionProps) {
  return (
    <section className="gp-guides-section" aria-labelledby={titleId}>
      <h2 className="gp-guides-section__title" id={titleId}>
        {title}
      </h2>
      <div className="gp-guides-section__list">{children}</div>
    </section>
  );
}
