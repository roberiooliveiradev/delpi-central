import { Shapes } from "lucide-react";
import { useRef, useState } from "react";

import { AnchoredPanelPortal } from "./AnchoredPanelPortal";

import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels, ShapeStylePreset } from "./types";
import { useClickOutside } from "./useClickOutside";

export type ShapeStyleGalleryProps = {
  themePresets?: ShapeStylePreset[];
  quickPresets?: ShapeStylePreset[];
  selectedId?: string;
  onSelect: (preset: ShapeStylePreset) => void;
  labels?: ShapeColorLabels;
  previewText?: string;
};

const DEFAULT_THEME_PRESETS: ShapeStylePreset[] = [
  { id: "theme-1", fill: "#ffffff", stroke: "#089bdb", strokeWidth: 2 },
  { id: "theme-2", fill: "#089bdb", stroke: "#003866", strokeWidth: 1 },
  { id: "theme-3", fill: "#003866", stroke: "#47bfff", strokeWidth: 1 },
  { id: "theme-4", fill: "#f2a100", stroke: "#44546a", strokeWidth: 2 },
  { id: "theme-5", fill: "#2e7d32", stroke: "#ffffff", strokeWidth: 1 },
  { id: "theme-6", fill: "transparent", stroke: "#089bdb", strokeWidth: 3 },
];

const DEFAULT_QUICK_PRESETS: ShapeStylePreset[] = [
  {
    id: "quick-1",
    fill: "#ffffff",
    stroke: "#000000",
    strokeWidth: 1,
    boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
  },
  { id: "quick-2", fill: "#089bdb", stroke: "transparent", strokeWidth: 0 },
  { id: "quick-3", fill: "transparent", stroke: "#7e14ff", strokeWidth: 2 },
  { id: "quick-4", fill: "#44546a", stroke: "#ffffff", strokeWidth: 1 },
];

export function ShapeStyleGallery({
  themePresets = DEFAULT_THEME_PRESETS,
  quickPresets = DEFAULT_QUICK_PRESETS,
  selectedId,
  onSelect,
  labels,
  previewText = "Abc",
}: ShapeStyleGalleryProps) {
  const L = mergeShapeColorLabels(labels);

  return (
    <div className="delpi-ui-shape-style-gallery">
      <section className="delpi-ui-shape-style-gallery__section">
        <h4 className="delpi-ui-shape-style-gallery__heading">{L.themeStyles}</h4>
        <PresetGrid
          presets={themePresets}
          selectedId={selectedId}
          previewText={previewText}
          onSelect={onSelect}
        />
      </section>
      <section className="delpi-ui-shape-style-gallery__section">
        <h4 className="delpi-ui-shape-style-gallery__heading">{L.presets}</h4>
        <PresetGrid
          presets={quickPresets}
          selectedId={selectedId}
          previewText={previewText}
          onSelect={onSelect}
        />
      </section>
    </div>
  );
}

export type ShapeStyleMenuProps = ShapeStyleGalleryProps;

export function ShapeStyleMenu(props: ShapeStyleMenuProps) {
  const L = mergeShapeColorLabels(props.labels);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => setOpen(false));

  return (
    <div className="delpi-ui-shape-menu" ref={rootRef}>
      <button
        type="button"
        className="delpi-ui-shape-menu__trigger"
        aria-label={L.themeStyles}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
          <Shapes size={18} />
        </span>
        <span className="delpi-ui-shape-menu__trigger-label">Estilo</span>
      </button>
      {open ? (
        <AnchoredPanelPortal open={open} anchorRef={rootRef} panelRef={panelRef} role="menu">
          <ShapeStyleGallery
            {...props}
            onSelect={(preset) => {
              props.onSelect(preset);
              setOpen(false);
            }}
          />
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

function PresetGrid({
  presets,
  selectedId,
  previewText,
  onSelect,
}: {
  presets: ShapeStylePreset[];
  selectedId?: string;
  previewText: string;
  onSelect: (preset: ShapeStylePreset) => void;
}) {
  return (
    <div className="delpi-ui-shape-style-gallery__grid" role="list">
      {presets.map((preset) => {
        const active = selectedId === preset.id;
        return (
          <button
            key={preset.id}
            type="button"
            role="listitem"
            className={
              active
                ? "delpi-ui-shape-style-gallery__item delpi-ui-shape-style-gallery__item--active"
                : "delpi-ui-shape-style-gallery__item"
            }
            aria-label={preset.label ?? preset.id}
            aria-pressed={active}
            onClick={() => onSelect(preset)}
          >
            <span
              className="delpi-ui-shape-style-gallery__preview"
              style={{
                background: preset.fill && preset.fill !== "transparent" ? preset.fill : undefined,
                borderColor: preset.stroke && preset.stroke !== "transparent" ? preset.stroke : undefined,
                borderWidth: preset.strokeWidth ? `${preset.strokeWidth}px` : undefined,
                borderStyle: preset.strokeWidth ? "solid" : undefined,
                boxShadow: preset.boxShadow,
              }}
            >
              {previewText}
            </span>
          </button>
        );
      })}
    </div>
  );
}
