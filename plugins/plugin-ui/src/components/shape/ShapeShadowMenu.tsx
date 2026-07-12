import { Cloud } from "lucide-react";
import { useRef, useState } from "react";

import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";
import { useClickOutside } from "./useClickOutside";

export type ShapeShadowPreset = {
  id: string;
  label: string;
  /** CSS box-shadow; omitido/undefined = sem sombra. */
  value?: string;
};

export type ShapeShadowMenuProps = {
  value?: string;
  presets: readonly ShapeShadowPreset[];
  onChange: (value: string | undefined) => void;
  labels?: ShapeColorLabels;
  shadowLabel?: string;
};

/** Menu de sombra no padrão Preench./Contorno (ícone + painel). */
export function ShapeShadowMenu({
  value,
  presets,
  onChange,
  labels,
  shadowLabel,
}: ShapeShadowMenuProps) {
  const L = mergeShapeColorLabels(labels);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => setOpen(false));

  const activeId =
    presets.find((preset) => (preset.value ?? "") === (value ?? ""))?.id ??
    presets.find((preset) => !preset.value)?.id ??
    presets[0]?.id;
  const hasShadow = Boolean(value?.trim());

  return (
    <div className="delpi-ui-shape-menu" ref={rootRef}>
      <button
        type="button"
        className="delpi-ui-shape-menu__trigger"
        aria-label={shadowLabel ?? L.shadow}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
          <Cloud size={18} strokeWidth={hasShadow ? 2.25 : 1.75} />
        </span>
        <span className="delpi-ui-shape-menu__trigger-label">{shadowLabel ?? L.shadow}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          className="delpi-ui-shape-menu__panel--narrow"
          role="menu"
        >
          <ul className="delpi-ui-shape-effects__list">
            {presets.map((preset) => {
              const selected = preset.id === activeId;
              return (
                <li key={preset.id} className="delpi-ui-shape-effects__item">
                  <button
                    type="button"
                    className={[
                      "delpi-ui-shape-effects__toggle",
                      selected ? "delpi-ui-shape-effects__toggle--selected" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    aria-checked={selected}
                    role="menuitemradio"
                    onClick={() => {
                      onChange(preset.value);
                      setOpen(false);
                    }}
                  >
                    {preset.label}
                  </button>
                </li>
              );
            })}
          </ul>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
