import type { ChatPresentation } from "../../data/api/chatTypes";

type KpiPresentation = Extract<ChatPresentation, { type: "kpi" }>;

const TREND_ICONS: Record<string, string> = {
  up: "↑",
  down: "↓",
  stable: "→",
};

export function ChatRichKpi({
  presentation,
}: {
  presentation: KpiPresentation;
}) {
  const { title, cards: rawCards } = presentation;
  const cards = Array.isArray(rawCards) ? rawCards : [];

  return (
    <div className="mdc-rich-kpi">
      {title && <div className="mdc-rich-kpi__title">{title}</div>}
      <div
        className="mdc-rich-kpi__grid"
        style={{ gridTemplateColumns: `repeat(${Math.min(cards.length, 4)}, 1fr)` }}
      >
        {cards.map((card, idx) => (
          <div
            key={idx}
            className="mdc-rich-kpi__card"
            style={card.color ? { borderTopColor: card.color } : undefined}
          >
            <div className="mdc-rich-kpi__label">{card.label}</div>
            <div className="mdc-rich-kpi__value">
              {formatKpiValue(card.value)}
              {card.unit && (
                <span className="mdc-rich-kpi__unit">{card.unit}</span>
              )}
            </div>
            {(card.trend || card.delta) && (
              <div
                className={[
                  "mdc-rich-kpi__trend",
                  `mdc-rich-kpi__trend--${card.trend || "stable"}`,
                ].join(" ")}
              >
                {card.trend && TREND_ICONS[card.trend]}
                {card.delta && (
                  <span className="mdc-rich-kpi__delta">{card.delta}</span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function formatKpiValue(value: string | number): string {
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString("pt-BR");
    return value.toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    });
  }
  return String(value);
}
