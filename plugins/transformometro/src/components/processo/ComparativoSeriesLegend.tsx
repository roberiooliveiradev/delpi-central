import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";

export type ComparativoLegendItem = {
  key: string;
  label: string;
  color: string;
};

type Props = {
  items: ComparativoLegendItem[];
  ariaLabel: string;
};

const SERIES_HELP = TM_HELP_TOOLTIPS.revisao.comparativoSeries;

export function ComparativoSeriesLegend({ items, ariaLabel }: Props) {
  if (!items.length) return null;
  return (
    <ul className="tm-comparativo-legend" aria-label={ariaLabel}>
      {items.map((item) => {
        const description = SERIES_HELP[item.key as keyof typeof SERIES_HELP];
        return (
          <li key={item.key} className="tm-comparativo-legend__item">
            <span
              className="tm-comparativo-legend__swatch"
              style={{ background: item.color }}
              aria-hidden
            />
            <span className="tm-comparativo-legend__text">
              <span className="tm-comparativo-legend__label">{item.label}</span>
              {description ? (
                <span className="tm-comparativo-legend__desc">{description}</span>
              ) : null}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
