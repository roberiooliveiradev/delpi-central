import type { ChatKpiCard, ChatPresentation } from "../../data/api/chatTypes";
import {
  formatCellValue,
  inferColumnType,
  type ColumnType,
} from "./tableCellFormatting";
import "./ChatRichKpi.css";

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
              {formatKpiValue(card)}
              {card.unit && !shouldHideUnit(card) && (
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

function shouldHideUnit(card: ChatKpiCard): boolean {
  const dataType = card.dataType || inferColumnType(card.key || card.label);

  return dataType === "currency" || dataType === "percent";
}

function formatKpiValue(card: ChatKpiCard): string {
  const { value, key, label, dataType, unit } = card;
  const columnKey = key || label;
  const resolvedType = dataType || inferKpiDataType(columnKey, unit);

  if (typeof value === "number") {
    return formatCellValue(value, columnKey, resolvedType);
  }

  if (typeof value === "string" && value.trim()) {
    const numeric = Number(value.replace(/\./g, "").replace(",", "."));

    if (!Number.isNaN(numeric) && value.trim() !== "") {
      return formatCellValue(numeric, columnKey, resolvedType);
    }
  }

  return String(value);
}

function inferKpiDataType(key: string, unit?: string): ColumnType {
  const normalizedUnit = String(unit || "").trim();

  if (normalizedUnit === "R$") {
    return "currency";
  }

  if (normalizedUnit === "%") {
    return "percent";
  }

  if (normalizedUnit && normalizedUnit !== "R$") {
    return "quantity";
  }

  const normalizedKey = key
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  if (
    /component|order|exclusive|without_stock|shipped|tables|price_table|quantity|count|mp|op/.test(
      normalizedKey,
    )
  ) {
    return "quantity";
  }

  if (/price|cost|valor|sale|discount|revenue|faturamento/.test(normalizedKey)) {
    return inferColumnType(key);
  }

  return "number";
}
