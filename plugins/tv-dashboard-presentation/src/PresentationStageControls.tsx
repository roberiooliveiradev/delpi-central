type Props = {
  index: number;
  total: number;
  paused: boolean;
  onPauseToggle: () => void;
  onPrevious: () => void;
  onNext: () => void;
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
    </div>
  );
}
