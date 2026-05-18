type PpmCompareToggleProps = {
  compare: boolean;
  onChange: (compare: boolean) => void;
};

export function PpmCompareToggle({ compare, onChange }: PpmCompareToggleProps) {
  return (
    <div className="dq-ppm-toggle" role="group" aria-label="Modo do gráfico PPM">
      <button
        type="button"
        className={`dq-ppm-toggle__btn${!compare ? " dq-ppm-toggle__btn--active" : ""}`}
        onClick={() => onChange(false)}
        aria-pressed={!compare}
      >
        Um tipo
      </button>
      <button
        type="button"
        className={`dq-ppm-toggle__btn${compare ? " dq-ppm-toggle__btn--active" : ""}`}
        onClick={() => onChange(true)}
        aria-pressed={compare}
      >
        Comparar
      </button>
    </div>
  );
}
