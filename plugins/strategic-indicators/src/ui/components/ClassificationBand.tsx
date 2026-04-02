type ClassificationBandProps = {
  value: number;
};

const bands = [
  { label: "Crítico", min: 0, max: 6, variant: "danger" },
  { label: "Regular, Exige Ação", min: 6, max: 7, variant: "warning" },
  { label: "Satisfatório com Alertas", min: 7, max: 8, variant: "info" },
  { label: "Alto Desempenho", min: 8, max: 9, variant: "success" },
  { label: "Excelência Integrada", min: 9, max: 10, variant: "success" },
] as const;

export function ClassificationBand({ value }: ClassificationBandProps) {
  const normalized = Math.max(0, Math.min(10, value));
  const percent = `${(normalized / 10) * 100}%`;

  return (
    <section className="si-classification-band">
      <div className="si-classification-band__header">
        <h3 className="si-classification-band__title">Faixa de classificação</h3>
        <span className="si-classification-band__value">{value.toFixed(1)}</span>
      </div>

      <div className="si-classification-band__track">
        <div
          className="si-classification-band__marker"
          style={{ left: percent }}
          aria-hidden="true"
        />
      </div>

      <div className="si-classification-band__segments">
        {bands.map((band) => (
          <div
            key={band.label}
            className={`si-classification-band__segment si-classification-band__segment--${band.variant}`}
          >
            <span className="si-classification-band__segment-label">
              {band.label}
            </span>
            <span className="si-classification-band__segment-range">
              {band.min.toFixed(1)}–{band.max.toFixed(1)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}