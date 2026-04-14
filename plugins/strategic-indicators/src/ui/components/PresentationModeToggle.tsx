type PresentationMode = "meeting" | "tv" | "slide";

type PresentationModeToggleProps = {
  mode: PresentationMode;
  onChange: (mode: PresentationMode) => void;
};

export function PresentationModeToggle({
  mode,
  onChange,
}: PresentationModeToggleProps) {
  return (
    <div
      className="si-presentation-mode-toggle"
      aria-label="Modo de apresentação"
    >
      <button
        type="button"
        className={`si-presentation-mode-toggle__button ${
          mode === "meeting" ? "is-active" : ""
        }`}
        onClick={() => onChange("meeting")}
      >
        Reunião
      </button>

      <button
        type="button"
        className={`si-presentation-mode-toggle__button ${
          mode === "tv" ? "is-active" : ""
        }`}
        onClick={() => onChange("tv")}
      >
        TV
      </button>

      <button
        type="button"
        className={`si-presentation-mode-toggle__button ${
          mode === "slide" ? "is-active" : ""
        }`}
        onClick={() => onChange("slide")}
      >
        Slide
      </button>
    </div>
  );
}