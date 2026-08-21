import {
  CalendarClock,
  ClipboardList,
  Gauge,
  House,
  LayoutGrid,
  TriangleAlert,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { copy } from "../content/copy";
import type { PpcBranch, Subplugin } from "../types";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const ICONS: Record<string, LucideIcon> = {
  house: House,
  "triangle-alert": TriangleAlert,
  "layout-grid": LayoutGrid,
  "clipboard-list": ClipboardList,
  "calendar-clock": CalendarClock,
  gauge: Gauge,
};

type PpcRailProps = {
  items: Subplugin[];
  activeId: string;
  branch: PpcBranch;
};

export function PpcRail({ items, activeId, branch }: PpcRailProps) {
  return (
    <nav className="ppc-rail" aria-label={copy.railAria}>
      <button
        type="button"
        className="ppc-rail__brand"
        title={copy.productName}
        onClick={() => navigatePpc(buildPpcHref({ subpluginId: "home", branch }))}
      >
        <House size={18} strokeWidth={1.75} aria-hidden />
        <span className="ppc-rail__brand-text">PCP</span>
      </button>
      <ul className="ppc-rail__list">
        {items.map((item) => {
          const Icon = ICONS[item.icon] ?? TriangleAlert;
          const disabled = item.status === "coming_soon";
          const active = item.id === activeId;
          const href = buildPpcHref({ subpluginId: item.id, branch });
          return (
            <li key={item.id}>
              <button
                type="button"
                className={`ppc-rail__item${active ? " ppc-rail__item--active" : ""}${
                  disabled ? " ppc-rail__item--disabled" : ""
                }`}
                disabled={disabled}
                title={disabled ? `${item.label} — ${copy.comingSoon}` : item.label}
                aria-current={active ? "page" : undefined}
                onClick={() => {
                  if (!disabled) navigatePpc(href);
                }}
              >
                <Icon size={18} strokeWidth={1.75} aria-hidden />
                <span className="ppc-rail__item-label">{item.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
