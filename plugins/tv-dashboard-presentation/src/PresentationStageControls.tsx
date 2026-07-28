import type { PresentationSection } from "./types";

type Props = {
  index: number;
  total: number;
  paused: boolean;
  onPauseToggle: () => void;
  onPrevious: () => void;
  onNext: () => void;
  /** Seções nomeadas para salto rápido (Figma-like). */
  sections?: PresentationSection[];
  onJumpToSection?: (sectionId: string) => void;
  /** Quando false, oculta com transição (idle). */
  visible?: boolean;
  className?: string;
};

/** Controles de slide (anterior / pausa / próxima) — prévia admin e apresentação. */
export function PresentationStageControls({
  index,
  total,
  paused,
  onPauseToggle,
  onPrevious,
  onNext,
  sections = [],
  onJumpToSection,
  visible = true,
  className,
}: Props) {
  const rootClass = [
    "tdp-preview-controls",
    visible ? "tdp-preview-controls--visible" : "tdp-preview-controls--hidden",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const namedSections = sections.filter((section) => Boolean(section.name?.trim()));
  const showSectionJump = namedSections.length >= 1 && typeof onJumpToSection === "function";

  return (
    <div className={rootClass} aria-hidden={!visible}>
      <button
        type="button"
        className="tdp-preview-controls__btn"
        onClick={onPrevious}
        disabled={total <= 1}
        tabIndex={visible ? 0 : -1}
      >
        Anterior
      </button>
      <span className="tdp-preview-controls__status">
        {index + 1} / {total}
        {paused ? " · Pausado" : ""}
      </span>
      <button
        type="button"
        className="tdp-preview-controls__btn"
        onClick={onPauseToggle}
        tabIndex={visible ? 0 : -1}
      >
        {paused ? "Retomar" : "Pausar"}
      </button>
      <button
        type="button"
        className="tdp-preview-controls__btn"
        onClick={onNext}
        disabled={total <= 1}
        tabIndex={visible ? 0 : -1}
      >
        Próxima
      </button>
      {showSectionJump ? (
        <label className="tdp-preview-controls__section-jump">
          <span className="tdp-preview-controls__section-jump-label">Ir para seção</span>
          <select
            className="tdp-preview-controls__section-select"
            aria-label="Ir para seção"
            value=""
            tabIndex={visible ? 0 : -1}
            onChange={(event) => {
              const sectionId = event.target.value;
              if (sectionId) onJumpToSection?.(sectionId);
              event.target.value = "";
            }}
          >
            <option value="">Seção…</option>
            {namedSections.map((section) => (
              <option key={section.id} value={section.id}>
                {section.name}
              </option>
            ))}
          </select>
        </label>
      ) : null}
    </div>
  );
}
