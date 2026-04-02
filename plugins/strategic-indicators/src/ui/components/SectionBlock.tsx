import type { PropsWithChildren, ReactNode } from "react";

type SectionBlockProps = PropsWithChildren<{
  title: string;
  description?: string;
  aside?: ReactNode;
}>;

export function SectionBlock({
  title,
  description,
  aside,
  children,
}: SectionBlockProps) {
  return (
    <section className="si-section-block">
      <div className="si-section-block__header">
        <div>
          <h2 className="si-section-block__title">{title}</h2>
          {description ? (
            <p className="si-section-block__description">{description}</p>
          ) : null}
        </div>

        {aside ? <div className="si-section-block__aside">{aside}</div> : null}
      </div>

      <div className="si-section-block__content">{children}</div>
    </section>
  );
}