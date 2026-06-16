import type { ContentFormatKind } from "./assistantContentLayout";
import type { VisualFormatOption } from "./assistantContentVisualFormats";
import { recordPresentationTelemetry } from "../presentationTelemetry";

type AssistantContentFormatToolbarProps = {
  options: VisualFormatOption[];
  activeKind: ContentFormatKind | null;
  showCompleteOption?: boolean;
  onChange: (kind: ContentFormatKind | null) => void;
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
      className={`mdc-rich-chart__toggle-btn mdc-assistant-content__format-toggle-btn ${active ? "mdc-rich-chart__toggle-btn--active mdc-assistant-content__format-toggle-btn--active" : ""}`}
      aria-pressed={active}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export function AssistantContentFormatToolbar({
  options,
  activeKind,
  showCompleteOption = false,
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
        {showCompleteOption ? (
          <FormatToggle
            active={activeKind === null}
            label="Completo"
            onClick={() => {
              if (activeKind === null) {
                return;
              }

              recordPresentationTelemetry("presentation_view_switch", {
                from: activeKind,
                to: "complete",
              });
              onChange(null);
            }}
          />
        ) : null}
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
