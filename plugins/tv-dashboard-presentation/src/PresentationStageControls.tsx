import { useEffect, useId, useRef, useState } from "react";
import type { PresentationSection } from "./types";
import { playbackModeLabel, type PlaybackMode } from "./playbackMode";

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
  /** Modo efetivo — em reunião oculta Pausar. */
  playbackMode?: PlaybackMode;
  onPlaybackModeChange?: (mode: PlaybackMode) => void;
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
  playbackMode = "presentation",
  onPlaybackModeChange,
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
  const showModeToggle = typeof onPlaybackModeChange === "function";
  const autoAdvance = playbackMode === "presentation";

  const menuId = useId();
  const modeMenuId = useId();
  const jumpRef = useRef<HTMLDivElement | null>(null);
  const modeRef = useRef<HTMLDivElement | null>(null);
  const [sectionMenuOpen, setSectionMenuOpen] = useState(false);
  const [modeMenuOpen, setModeMenuOpen] = useState(false);

  useEffect(() => {
    if (!visible) {
      setSectionMenuOpen(false);
      setModeMenuOpen(false);
    }
  }, [visible]);

  useEffect(() => {
    if (!sectionMenuOpen && !modeMenuOpen) return;

    const onPointerDown = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (sectionMenuOpen && jumpRef.current && !jumpRef.current.contains(target)) {
        setSectionMenuOpen(false);
      }
      if (modeMenuOpen && modeRef.current && !modeRef.current.contains(target)) {
        setModeMenuOpen(false);
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSectionMenuOpen(false);
        setModeMenuOpen(false);
      }
    };

    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [sectionMenuOpen, modeMenuOpen]);

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
        {autoAdvance && paused ? " · Pausado" : ""}
      </span>
      {autoAdvance ? (
        <button
          type="button"
          className="tdp-preview-controls__btn"
          onClick={onPauseToggle}
          tabIndex={visible ? 0 : -1}
        >
          {paused ? "Retomar" : "Pausar"}
        </button>
      ) : null}
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
            onClick={() => {
              setModeMenuOpen(false);
              setSectionMenuOpen((open) => !open);
            }}
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
      {showModeToggle ? (
        <div ref={modeRef} className="tdp-preview-controls__section-jump">
          <button
            type="button"
            className={[
              "tdp-preview-controls__btn",
              "tdp-preview-controls__section-trigger",
              modeMenuOpen ? "tdp-preview-controls__section-trigger--open" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label="Modo de reprodução"
            aria-haspopup="listbox"
            aria-expanded={modeMenuOpen}
            aria-controls={modeMenuId}
            tabIndex={visible ? 0 : -1}
            onClick={() => {
              setSectionMenuOpen(false);
              setModeMenuOpen((open) => !open);
            }}
          >
            {playbackModeLabel(playbackMode)}
          </button>
          {modeMenuOpen ? (
            <ul
              id={modeMenuId}
              className="tdp-preview-controls__section-menu"
              role="listbox"
              aria-label="Modo de reprodução"
            >
              {(
                [
                  { id: "presentation" as const, hint: "Avanço automático" },
                  { id: "meeting" as const, hint: "Avanço manual" },
                ] as const
              ).map((option) => (
                <li key={option.id} role="presentation">
                  <button
                    type="button"
                    role="option"
                    aria-selected={playbackMode === option.id}
                    className="tdp-preview-controls__section-option"
                    onClick={() => {
                      onPlaybackModeChange?.(option.id);
                      setModeMenuOpen(false);
                    }}
                  >
                    {playbackModeLabel(option.id)}
                    <span className="tdp-preview-controls__mode-hint"> · {option.hint}</span>
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
