import type { AssistantVisualKind } from "./assistantContentLayout";
import type { VisualFormatOption } from "./assistantContentVisualFormats";
import { recordPresentationTelemetry } from "./presentationTelemetry";

type AssistantContentFormatToolbarProps = {
  options: VisualFormatOption[];
  activeKind: AssistantVisualKind;
  onChange: (kind: AssistantVisualKind) => void;
};

function FormatToggle({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`mdc-rich-chart__toggle-btn ${active ? "mdc-rich-chart__toggle-btn--active" : ""}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export function AssistantContentFormatToolbar({
  options,
  activeKind,
  onChange,
}: AssistantContentFormatToolbarProps) {
  if (options.length < 2) {
    return null;
  }

  return (
    <div className="mdc-rich-presentation__toolbar mdc-assistant-content__format-toolbar">
      <div
        className="mdc-rich-presentation__format-toggle"
        role="group"
        aria-label="Formato da visualização"
      >
        {options.map((option) => (
          <FormatToggle
            key={option.kind}
            active={activeKind === option.kind}
            label={option.label}
            onClick={() => {
              if (option.kind === activeKind) {
                return;
              }

              recordPresentationTelemetry("presentation_view_switch", {
                from: activeKind,
                to: option.kind,
              });
              onChange(option.kind);
            }}
          />
        ))}
      </div>
    </div>
  );
}
