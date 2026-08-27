import { Cloud } from "lucide-react";
import { useRef, useState } from "react";

import { useRibbonSectionPopoverSurface } from "../ribbon/RibbonGroupSurfaceContext";
import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import { ShadowStackEditorPanel, type ShadowStackPreset } from "./ShadowStackEditorPanel";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";

export type TextShadowPreset = ShadowStackPreset;

export type TextShadowMenuProps = {
  value?: string;
  presets: readonly TextShadowPreset[];
  onChange: (value: string | undefined) => void;
  labels?: ShapeColorLabels;
  shadowLabel?: string;
  /** Quando true, renderiza só o painel (sidebar / popover aninhado). */
  inline?: boolean;
};

/** Menu de sombra tipográfica — paridade com ShapeShadowMenu (sem inset/spread). */
export function TextShadowMenu({
  value,
  presets,
  onChange,
  labels,
  shadowLabel,
  inline = false,
}: TextShadowMenuProps) {
  const L = mergeShapeColorLabels(labels);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const dismiss = () => setOpen(false);
  const hasShadow = Boolean(value?.trim());

  const panel = (
    <ShadowStackEditorPanel
      mode="text"
      value={value}
      presets={presets}
      onChange={onChange}
      labels={labels}
    />
  );

  if (inline || inSectionPopover) {
    return panel;
  }

  return (
    <div className="delpi-ui-shape-menu delpi-ui-text-shadow-menu" ref={rootRef}>
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
          {panel}
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
