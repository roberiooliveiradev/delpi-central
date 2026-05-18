import type { PpmType } from "../types/ppm";

type PpmTypeToggleProps = {
  value: PpmType;
  onChange: (value: PpmType) => void;
};

export function PpmTypeToggle({ value, onChange }: PpmTypeToggleProps) {
  return (
    <div className="dq-ppm-toggle" role="group" aria-label="Tipo de PPM">
      <button
        type="button"
        className={`dq-ppm-toggle__btn${value === "internal" ? " dq-ppm-toggle__btn--active" : ""}`}
        onClick={() => onChange("internal")}
        aria-pressed={value === "internal"}
      >
        Interno
      </button>
      <button
        type="button"
        className={`dq-ppm-toggle__btn${value === "external" ? " dq-ppm-toggle__btn--active" : ""}`}
        onClick={() => onChange("external")}
        aria-pressed={value === "external"}
      >
        Externo
      </button>
    </div>
  );
}
