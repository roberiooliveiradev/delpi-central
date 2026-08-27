import { Cloud } from "lucide-react";
import { useRef, useState } from "react";

import { useRibbonSectionPopoverSurface } from "../ribbon/RibbonGroupSurfaceContext";
import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import { ShadowStackEditorPanel, type ShadowStackPreset } from "./ShadowStackEditorPanel";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";

export type ShapeShadowPreset = ShadowStackPreset;

export type ShapeShadowMenuProps = {
  value?: string;
  presets: readonly ShapeShadowPreset[];
  onChange: (value: string | undefined) => void;
  labels?: ShapeColorLabels;
  shadowLabel?: string;
};

/** Menu de sombra de forma: presets + inset + até 2 camadas. */
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
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const dismiss = () => setOpen(false);
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
          className="delpi-ui-shape-menu__panel--shadow"
          role="menu"
          exclusive={!inSectionPopover}
          onDismiss={dismiss}
        >
          <ShadowStackEditorPanel
            mode="box"
            value={value}
            presets={presets}
            onChange={onChange}
            labels={labels}
          />
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
