import type { IgdTrendPoint } from "../../data/types/trends";

type IgdTrendTimelineProps = {
  series: IgdTrendPoint[];
};

function getBarHeight(value: number) {
  const min = 6;
  const max = 10;
  const normalized = ((value - min) / (max - min)) * 100;
  return `${Math.max(12, normalized)}%`;
}

export function IgdTrendTimeline({
  series,
}: IgdTrendTimelineProps) {
  return (
    <section className="si-igd-timeline">
      <div className="si-igd-timeline__header">
        <h3 className="si-igd-timeline__title">Linha temporal do IGD</h3>
        <span className="si-igd-timeline__subtitle">
          evolução histórica do índice global
        </span>
      </div>

      <div className="si-igd-timeline__chart">
        {series.map((point, index) => {
          const isLast = index === series.length - 1;

          return (
            <div key={point.period} className="si-igd-timeline__column">
              <div className="si-igd-timeline__bar-wrap">
                <div
                  className={`si-igd-timeline__bar ${
                    isLast ? "si-igd-timeline__bar--active" : ""
                  }`}
                  style={{ height: getBarHeight(point.value) }}
                />
              </div>

              <strong className="si-igd-timeline__value">
                {point.value.toFixed(1)}
              </strong>
              <span className="si-igd-timeline__period">{point.period}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}