import { ChevronRight, Minus } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { AnchoredPanelPortal } from "./AnchoredPanelPortal";

import { ColorPickerPopover } from "./ColorPickerPopover";
import { cssToColorValue } from "./colorUtils";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";
import { useClickOutside } from "./useClickOutside";

export type ShapeOutlineMenuProps = {
  color?: string;
  strokeWidth?: number;
  minWidth?: number;
  maxWidth?: number;
  onColorChange: (color: string) => void;
  onNoOutline?: () => void;
  onStrokeWidthChange?: (width: number) => void;
  onDashed?: () => void;
  onLineStyle?: () => void;
  onArrows?: () => void;
  labels?: ShapeColorLabels;
  outlineLabel?: string;
};

const WIDTH_PRESETS = [0.5, 1, 1.5, 2, 3, 4, 6, 8];

export function ShapeOutlineMenu({
  color,
  strokeWidth = 2,
  minWidth = 0,
  maxWidth = 20,
  onColorChange,
  onNoOutline,
  onStrokeWidthChange,
  onDashed,
  onLineStyle,
  onArrows,
  labels,
  outlineLabel,
}: ShapeOutlineMenuProps) {
  const L = mergeShapeColorLabels(labels);
  const [open, setOpen] = useState(false);
  const [submenu, setSubmenu] = useState<"thickness" | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => {
    setOpen(false);
    setSubmenu(null);
  });

  const previewColor = color && cssToColorValue(color).alpha > 0 ? color : "transparent";

  return (
    <div className="delpi-ui-shape-menu" ref={rootRef}>
      <button
        type="button"
        className="delpi-ui-shape-menu__trigger"
        aria-label={outlineLabel ?? L.outline}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
          <Minus size={18} strokeWidth={Math.min(4, strokeWidth)} />
          <span
            className="delpi-ui-shape-menu__trigger-swatch delpi-ui-shape-menu__trigger-swatch--outline"
            style={{ borderColor: previewColor === "transparent" ? undefined : previewColor }}
          />
        </span>
        <span className="delpi-ui-shape-menu__trigger-label">{outlineLabel ?? L.outline}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal open={open} anchorRef={rootRef} panelRef={panelRef} role="menu">
          <ColorPickerPopover
            value={color}
            onChange={onColorChange}
            onNoFill={onNoOutline}
            noFillLabel={L.noOutline}
            showNoFill={Boolean(onNoOutline)}
            labels={labels}
          />
          <ul className="delpi-ui-shape-menu__submenus">
            {onStrokeWidthChange ? (
              <SubmenuItem
                label={L.thickness}
                open={submenu === "thickness"}
                onToggle={() => setSubmenu((prev) => (prev === "thickness" ? null : "thickness"))}
              >
                <div className="delpi-ui-shape-outline__width-grid">
                  {WIDTH_PRESETS.filter((w) => w >= minWidth && w <= maxWidth).map((width) => (
                    <button
                      key={width}
                      type="button"
                      className={
                        strokeWidth === width
                          ? "delpi-ui-shape-outline__width delpi-ui-shape-outline__width--active"
                          : "delpi-ui-shape-outline__width"
                      }
                      onClick={() => onStrokeWidthChange(width)}
                    >
                      {width} pt
                    </button>
                  ))}
                  <label className="delpi-ui-shape-outline__width-custom">
                    <input
                      type="number"
                      min={minWidth}
                      max={maxWidth}
                      value={strokeWidth}
                      aria-label={L.thickness}
                      onChange={(event) => onStrokeWidthChange(Number(event.target.value) || minWidth)}
                    />
                  </label>
                </div>
              </SubmenuItem>
            ) : null}
            {onDashed ? (
              <li>
                <button type="button" className="delpi-ui-shape-menu__submenu-action" onClick={onDashed}>
                  {L.dashed}
                </button>
              </li>
            ) : null}
            {onLineStyle ? (
              <li>
                <button type="button" className="delpi-ui-shape-menu__submenu-action" onClick={onLineStyle}>
                  {L.lineStyle}
                </button>
              </li>
            ) : null}
            {onArrows ? (
              <li>
                <button type="button" className="delpi-ui-shape-menu__submenu-action" onClick={onArrows}>
                  {L.arrows}
                </button>
              </li>
            ) : null}
          </ul>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

function SubmenuItem({
  label,
  open,
  onToggle,
  children,
}: {
  label: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <li className="delpi-ui-shape-menu__submenu">
      <button type="button" className="delpi-ui-shape-menu__submenu-toggle" onClick={onToggle}>
        {label}
        <ChevronRight size={14} aria-hidden="true" />
      </button>
      {open ? <div className="delpi-ui-shape-menu__submenu-panel">{children}</div> : null}
    </li>
  );
}
