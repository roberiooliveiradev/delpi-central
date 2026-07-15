import type { GuideSection } from "../types/guide";

type GuideSectionBlockProps = {
  index: number;
  section: GuideSection;
};

export function GuideSectionBlock({ index, section }: GuideSectionBlockProps) {
  return (
    <section className="gp-section" aria-labelledby={`gp-section-${section.id}`}>
      <h2 className="gp-section__title" id={`gp-section-${section.id}`}>
        <span className="gp-section__index" aria-hidden="true">
          {String(index).padStart(2, "0")}
        </span>
        {section.title}
      </h2>
      <ul className="gp-section__list">
        {section.items.map((item) => (
          <li
            key={item.id}
            className={
              item.emphasis
                ? "gp-section__item gp-section__item--emphasis"
                : "gp-section__item"
            }
          >
            {item.text}
          </li>
        ))}
      </ul>
    </section>
  );
}
