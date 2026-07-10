import { useLayoutEffect, useState, type CSSProperties, type RefObject } from "react";
import { createPortal } from "react-dom";
import * as LucideIcons from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";
import { COMUNICADO_ICON_OPTIONS } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Props = {
  anchorRef: RefObject<HTMLDivElement | null>;
  onSelect: (iconName: string) => void;
};

export function ComunicadoIconLibraryMenu({ anchorRef, onSelect }: Props) {
  const [style, setStyle] = useState<CSSProperties>({ visibility: "hidden" });

  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    if (!anchor) return;

    const rect = anchor.getBoundingClientRect();
    const panelWidth = 300;
    const left = Math.min(Math.max(8, rect.left), window.innerWidth - panelWidth - 8);

    setStyle({
      position: "fixed",
      top: rect.bottom + 4,
      left,
      width: panelWidth,
      maxHeight: "min(50vh, 360px)",
      zIndex: 5000,
      visibility: "visible",
    });
  }, [anchorRef]);

  return createPortal(
    <div className="td-shape-library td-shape-library--portal" role="menu" aria-label="Biblioteca de ícones" style={style}>
      <section className="td-shape-library__section">
        <h4 className="td-shape-library__title">Ícones</h4>
        <div className="td-shape-library__grid td-shape-library__grid--icons">
          {COMUNICADO_ICON_OPTIONS.map((item) => {
            const Icon = (LucideIcons as Record<string, LucideIcons.LucideIcon>)[item.name];
            if (!Icon) return null;

            return (
              <HintAction
                key={item.name}
                hint={`${H.insertIcon} — ${item.label}`}
                ariaLabel={`Inserir ícone ${item.label}`}
                placement="right"
              >
                <button
                  type="button"
                  role="menuitem"
                  className="td-shape-library__item"
                  aria-label={item.label}
                  onClick={() => onSelect(item.name)}
                >
                  <span className="td-shape-library__icon-wrap">
                    <Icon size={22} aria-hidden="true" />
                  </span>
                  <span className="td-shape-library__label">{item.label}</span>
                </button>
              </HintAction>
            );
          })}
        </div>
      </section>
    </div>,
    document.body,
  );
}
