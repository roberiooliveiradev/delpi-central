import type { ReactNode } from "react";
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Minus,
  WrapText,
} from "lucide-react";
import { resolveCanvasTableWrapActive } from "@delpi/tv-dashboard-presentation";

import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";

export type CanvasTableTextAlign = "left" | "center" | "right";
export type CanvasTableVerticalAlign = "top" | "middle" | "bottom";

type Props = {
  textAlign?: CanvasTableTextAlign | null;
  verticalAlign?: CanvasTableVerticalAlign | null;
  whiteSpace?: "normal" | "nowrap" | "pre-wrap" | null;
  color?: string | null;
  backgroundColor?: string | null;
  onAlign: (align: CanvasTableTextAlign) => void;
  onVerticalAlign: (align: CanvasTableVerticalAlign) => void;
  onToggleWrap: () => void;
  onSetNowrap: () => void;
  onColorChange: (color: string) => void;
  onBackgroundChange: (color: string) => void;
  onNoFill: () => void;
  footer?: ReactNode;
  className?: string;
};

/**
 * Menu de formato da **célula** Grade — align H/V, wrap, cores.
 * Chrome `td-chart-style-menu`. Bordas ficam para S29.
 */
export function CanvasTableCellFormatMenu({
  textAlign,
  verticalAlign,
  whiteSpace,
  color,
  backgroundColor,
  onAlign,
  onVerticalAlign,
  onToggleWrap,
  onSetNowrap,
  onColorChange,
  onBackgroundChange,
  onNoFill,
  footer,
  className,
}: Props) {
  const wrapActive = resolveCanvasTableWrapActive(whiteSpace);

  return (
    <div
      className={["td-chart-style-menu", className].filter(Boolean).join(" ")}
      role="menu"
      aria-label="Formato da célula da Grade"
    >
      <section className="td-chart-style-menu__section">
        <h4>Alinhamento horizontal</h4>
        <div className="td-chart-style-menu__styles">
          {(
            [
              { id: "left", label: "Esquerda", icon: AlignLeft },
              { id: "center", label: "Centro", icon: AlignCenter },
              { id: "right", label: "Direita", icon: AlignRight },
            ] as const
          ).map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                type="button"
                role="menuitemradio"
                aria-checked={textAlign === item.id}
                className={[
                  "td-chart-style-menu__style",
                  textAlign === item.id ? "td-chart-style-menu__style--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onAlign(item.id)}
              >
                <Icon size={16} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="td-chart-style-menu__section">
        <h4>Alinhamento vertical</h4>
        <div className="td-chart-style-menu__styles">
          {(
            [
              { id: "top", label: "Topo" },
              { id: "middle", label: "Meio" },
              { id: "bottom", label: "Base" },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              type="button"
              role="menuitemradio"
              aria-checked={(verticalAlign ?? "middle") === item.id}
              className={[
                "td-chart-style-menu__style",
                (verticalAlign ?? "middle") === item.id
                  ? "td-chart-style-menu__style--active"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onVerticalAlign(item.id)}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="td-chart-style-menu__section">
        <h4>Quebra de linha</h4>
        <div className="td-chart-style-menu__styles">
          <button
            type="button"
            role="menuitemcheckbox"
            aria-checked={wrapActive}
            className={[
              "td-chart-style-menu__style",
              wrapActive ? "td-chart-style-menu__style--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={onToggleWrap}
          >
            <WrapText size={16} aria-hidden="true" />
            <span>Quebrar</span>
          </button>
          <button
            type="button"
            role="menuitemradio"
            aria-checked={!wrapActive}
            className={[
              "td-chart-style-menu__style",
              !wrapActive ? "td-chart-style-menu__style--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={onSetNowrap}
          >
            <Minus size={16} aria-hidden="true" />
            <span>1 linha</span>
          </button>
        </div>
      </section>

      <section className="td-chart-style-menu__section">
        <h4>Cores</h4>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
          <TvRibbonColorPicker
            label="Texto"
            variant="text"
            showAutomatic
            value={color ?? undefined}
            onChange={onColorChange}
            onAutomatic={onColorChange}
          />
          <TvRibbonColorPicker
            label="Fundo"
            variant="fill"
            showNoFill
            value={backgroundColor ?? undefined}
            onChange={onBackgroundChange}
            onNoFill={onNoFill}
          />
        </div>
      </section>

      {footer ? <div className="td-chart-style-menu__footer">{footer}</div> : null}
    </div>
  );
}
