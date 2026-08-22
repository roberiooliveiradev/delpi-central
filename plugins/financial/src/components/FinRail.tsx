import {
  Gauge,
  HandCoins,
  House,
  Receipt,
  Target,
  TrendingUp,
  Wallet,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { copy } from "../content/copy";
import type { FinancialBranch, Subplugin } from "../types";
import { buildFinancialHref, navigateFinancial } from "../utils/routeParser";

const ICONS: Record<string, LucideIcon> = {
  house: House,
  "hand-coins": HandCoins,
  receipt: Receipt,
  gauge: Gauge,
  target: Target,
  "trending-up": TrendingUp,
};

type FinRailProps = {
  items: Subplugin[];
  activeId: string;
  branch: FinancialBranch;
};

export function FinRail({ items, activeId, branch }: FinRailProps) {
  return (
    <nav className="fin-rail" aria-label={copy.railAria}>
      <button
        type="button"
        className="fin-rail__brand"
        title={copy.productName}
        onClick={() => navigateFinancial(buildFinancialHref({ subpluginId: "home", branch }))}
      >
        <Wallet size={18} strokeWidth={1.75} aria-hidden />
        <span className="fin-rail__brand-text">{copy.railBrand}</span>
      </button>
      <ul className="fin-rail__list">
        {items.map((item) => {
          const Icon = ICONS[item.icon] ?? Wallet;
          const disabled = item.status === "coming_soon";
          const active = item.id === activeId;
          const href = buildFinancialHref({ subpluginId: item.id, branch });
          return (
            <li key={item.id}>
              <button
                type="button"
                className={`fin-rail__item${active ? " fin-rail__item--active" : ""}${
                  disabled ? " fin-rail__item--disabled" : ""
                }`}
                disabled={disabled}
                title={disabled ? `${item.label} — ${copy.comingSoon}` : item.label}
                aria-current={active ? "page" : undefined}
                onClick={() => {
                  if (!disabled) navigateFinancial(href);
                }}
              >
                <Icon size={18} strokeWidth={1.75} aria-hidden />
                <span className="fin-rail__item-label">{item.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
