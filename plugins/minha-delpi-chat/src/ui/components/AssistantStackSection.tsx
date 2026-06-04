import type { StackSectionChrome } from "./presentationStackSections";

import "./AssistantStackSection.css";

type AssistantStackSectionProps = {
  section: StackSectionChrome;
};

export function AssistantStackSection({ section }: AssistantStackSectionProps) {
  return (
    <header
      className="mdc-stack-section"
      aria-label={section.title}
      data-stack-section={section.id}
    >
      <h4 className="mdc-stack-section__title">
        <span className="mdc-stack-section__rule" aria-hidden="true" />
        {section.title}
        <span className="mdc-stack-section__rule" aria-hidden="true" />
      </h4>
    </header>
  );
}
