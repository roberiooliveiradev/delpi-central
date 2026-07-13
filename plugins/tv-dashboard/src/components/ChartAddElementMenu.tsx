import { useEffect, useId, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import type { SeriesChartKind } from "@delpi/plugin-ui/index";
import type {
  ChartAddElementChoiceId,
  ChartElementId,
  ComunicadoChartOptions,
} from "@delpi/tv-dashboard-presentation";
import { isChartAddElementChoiceActive } from "@delpi/tv-dashboard-presentation";

import { resolveChartAddElementMenuRoots } from "../content/chartAddElementMenuCatalog";

type Props = {
  options: ComunicadoChartOptions;
  chartKind: SeriesChartKind;
  onApplyChoice: (choiceId: ChartAddElementChoiceId) => void;
  onMoreOptions: (elementId: ChartElementId) => void;
  className?: string;
};

/**
 * Menu cascata PPT: raiz → flyout de presets → «Mais opções…».
 * Compartilhado ribbon + float `+`.
 */
export function ChartAddElementMenu({
  options,
  chartKind,
  onApplyChoice,
  onMoreOptions,
  className,
}: Props) {
  const roots = resolveChartAddElementMenuRoots(chartKind);
  const [openId, setOpenId] = useState<ChartElementId | null>(null);
  const rootRef = useRef<HTMLUListElement>(null);
  const baseId = useId();

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpenId(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <ul
      ref={rootRef}
      className={["td-chart-add-element", className].filter(Boolean).join(" ")}
      role="menu"
      aria-label="Adicionar elemento de gráfico"
    >
      {roots.map((root) => {
        const Icon = root.icon;
        const open = openId === root.elementId;
        const flyoutId = `${baseId}-${root.elementId}-flyout`;
        return (
          <li
            key={root.elementId}
            className={[
              "td-chart-add-element__root",
              open ? "td-chart-add-element__root--open" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onMouseEnter={() => setOpenId(root.elementId)}
            onFocusCapture={() => setOpenId(root.elementId)}
          >
            <button
              type="button"
              role="menuitem"
              className="td-chart-add-element__root-btn"
              aria-haspopup="menu"
              aria-expanded={open}
              aria-controls={flyoutId}
              onClick={() => setOpenId((prev) => (prev === root.elementId ? null : root.elementId))}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{root.label}</span>
              <ChevronRight size={14} aria-hidden="true" className="td-chart-add-element__chevron" />
            </button>

            {open ? (
              <ul
                id={flyoutId}
                className="td-chart-add-element__flyout"
                role="menu"
                aria-label={root.label}
              >
                {root.choices.map((choice) => {
                  const ChoiceIcon = choice.icon;
                  const active = isChartAddElementChoiceActive(choice.id, options);
                  return (
                    <li key={choice.id}>
                      <button
                        type="button"
                        role="menuitemcheckbox"
                        aria-checked={active}
                        className={[
                          "td-chart-add-element__choice",
                          active ? "td-chart-add-element__choice--active" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        onClick={() => onApplyChoice(choice.id)}
                      >
                        <ChoiceIcon size={16} aria-hidden="true" />
                        <span>{choice.label}</span>
                      </button>
                    </li>
                  );
                })}
                <li className="td-chart-add-element__flyout-sep" role="separator" />
                <li>
                  <button
                    type="button"
                    role="menuitem"
                    className="td-chart-add-element__more"
                    onClick={() => onMoreOptions(root.elementId)}
                  >
                    {root.moreOptionsLabel}
                  </button>
                </li>
              </ul>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
