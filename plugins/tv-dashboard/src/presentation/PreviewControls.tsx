type Props = {
  index: number;
  total: number;
  paused: boolean;
  onPauseToggle: () => void;
  onPrevious: () => void;
  onNext: () => void;
};

export function PreviewControls({
  index,
  total,
  paused,
  onPauseToggle,
  onPrevious,
  onNext,
}: Props) {
  return (
    <div className="tdp-preview-controls">
      <button type="button" className="td-btn" onClick={onPrevious} disabled={total <= 1}>
        Anterior
      </button>
      <span className="tdp-preview-controls__status">
        {index + 1} / {total}
        {paused ? " · Pausado" : ""}
      </span>
      <button type="button" className="td-btn" onClick={onPauseToggle}>
        {paused ? "Retomar" : "Pausar"}
      </button>
      <button type="button" className="td-btn" onClick={onNext} disabled={total <= 1}>
        Próxima
      </button>
    </div>
  );
}
