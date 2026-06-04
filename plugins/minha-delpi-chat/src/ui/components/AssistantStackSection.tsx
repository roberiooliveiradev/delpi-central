import type { StackSectionChrome } from "./presentationStackSections";

import "./AssistantStackSection.css";

type AssistantStackSectionProps = {
  section: StackSectionChrome;
};

export function AssistantStackSection({ section }: AssistantStackSectionProps) {
  return (
    <section
      className="mdc-stack-section"
      aria-labelledby={`stack-section-${section.id}`}
      data-stack-section={section.id}
    >
      <h4 className="mdc-stack-section__title" id={`stack-section-${section.id}`}>
        <span className="mdc-stack-section__rule" aria-hidden="true" />
        {section.title}
        <span className="mdc-stack-section__rule" aria-hidden="true" />
      </h4>
      {section.description.trim() ? (
        <p className="mdc-stack-section__description">{section.description}</p>
      ) : null}
    </section>
  );
}
