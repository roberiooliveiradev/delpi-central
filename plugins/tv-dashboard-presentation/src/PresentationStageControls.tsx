import { useEffect, useId, useRef, useState } from "react";
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
  const onlyMain =
    namedSections.length === 1 && Boolean(namedSections[0]?.isMain);
  const jumpSections = onlyMain ? [] : namedSections;
  const showSectionJump = jumpSections.length >= 1 && typeof onJumpToSection === "function";

  const menuId = useId();
  const jumpRef = useRef<HTMLDivElement | null>(null);
  const [sectionMenuOpen, setSectionMenuOpen] = useState(false);

  useEffect(() => {
    if (!visible) setSectionMenuOpen(false);
  }, [visible]);

  useEffect(() => {
    if (!sectionMenuOpen) return;

    const onPointerDown = (event: PointerEvent) => {
      const root = jumpRef.current;
      if (!root) return;
      if (event.target instanceof Node && !root.contains(event.target)) {
        setSectionMenuOpen(false);
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSectionMenuOpen(false);
    };

    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [sectionMenuOpen]);

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
        <div ref={jumpRef} className="tdp-preview-controls__section-jump">
          <button
            type="button"
            className={[
              "tdp-preview-controls__btn",
              "tdp-preview-controls__section-trigger",
              sectionMenuOpen ? "tdp-preview-controls__section-trigger--open" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label="Ir para seção"
            aria-haspopup="listbox"
            aria-expanded={sectionMenuOpen}
            aria-controls={menuId}
            tabIndex={visible ? 0 : -1}
            onClick={() => setSectionMenuOpen((open) => !open)}
          >
            Seção…
          </button>
          {sectionMenuOpen ? (
            <ul
              id={menuId}
              className="tdp-preview-controls__section-menu"
              role="listbox"
              aria-label="Seções"
            >
              {jumpSections.map((section) => (
                <li key={section.id} role="presentation">
                  <button
                    type="button"
                    role="option"
                    className="tdp-preview-controls__section-option"
                    onClick={() => {
                      onJumpToSection?.(section.id);
                      setSectionMenuOpen(false);
                    }}
                  >
                    {section.name}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
