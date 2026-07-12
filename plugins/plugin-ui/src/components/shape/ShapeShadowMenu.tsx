import { Cloud } from "lucide-react";
import { useRef, useState, type ChangeEvent } from "react";

import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import {
  boxShadowsEqual,
  formatBoxShadow,
  patchBoxShadow,
  resolveBoxShadowModel,
  type BoxShadowModel,
} from "./boxShadowModel";
import { ColorPickerPopover } from "./ColorPickerPopover";
import { colorToCss, cssToColorValue } from "./colorUtils";
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

type ShadowFieldKey = "offsetX" | "offsetY" | "blur" | "spread" | "opacityPercent";

function clampField(key: ShadowFieldKey, value: number): number {
  if (key === "offsetX" || key === "offsetY") return Math.min(80, Math.max(-80, value));
  if (key === "blur") return Math.min(120, Math.max(0, value));
  if (key === "spread") return Math.min(60, Math.max(-40, value));
  return Math.min(100, Math.max(0, value));
}

/** Menu de sombra: presets + X/Y/blur/spread/cor/opacidade (padrão Figma/CSS). */
export function ShapeShadowMenu({
  value,
  presets,
  onChange,
  labels,
  shadowLabel,
}: ShapeShadowMenuProps) {
  const L = mergeShapeColorLabels(labels);
  const [open, setOpen] = useState(false);
  const [colorOpen, setColorOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => {
    setOpen(false);
    setColorOpen(false);
  });

  const hasShadow = Boolean(value?.trim());
  const model = resolveBoxShadowModel(value);
  const activePresetId = presets.find((preset) =>
    boxShadowsEqual(preset.value, value),
  )?.id;
  const isCustom = hasShadow && !activePresetId;

  const applyModel = (next: BoxShadowModel) => {
    onChange(formatBoxShadow(next));
  };

  const applyPatch = (patch: Partial<BoxShadowModel>) => {
    onChange(patchBoxShadow(value, patch));
  };

  const handleNumberChange = (key: ShadowFieldKey, raw: string) => {
    const parsed = Number(raw.replace(",", "."));
    if (!Number.isFinite(parsed)) return;
    const clamped = clampField(key, parsed);
    if (key === "opacityPercent") {
      applyPatch({ opacity: clamped / 100 });
      return;
    }
    applyPatch({ [key]: clamped });
  };

  const handleColorChange = (color: string) => {
    const parsed = cssToColorValue(color, model.colorHex);
    // Swatches sólidos do tema: preserva opacidade atual da sombra.
    if (parsed.alpha >= 1 && !color.trim().toLowerCase().startsWith("rgba")) {
      applyPatch({ colorHex: parsed.hex });
      return;
    }
    applyPatch({
      colorHex: parsed.hex,
      opacity: parsed.alpha > 0 ? parsed.alpha : model.opacity,
    });
  };

  const colorCss = colorToCss({ hex: model.colorHex, alpha: model.opacity });
  const fields: Array<{ key: ShadowFieldKey; label: string; value: number; step?: number }> = [
    { key: "offsetX", label: L.shadowOffsetX, value: model.offsetX },
    { key: "offsetY", label: L.shadowOffsetY, value: model.offsetY },
    { key: "blur", label: L.shadowBlur, value: model.blur },
    { key: "spread", label: L.shadowSpread, value: model.spread },
    {
      key: "opacityPercent",
      label: L.shadowOpacity,
      value: Math.round(model.opacity * 100),
      step: 1,
    },
  ];

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
        >
          <ul className="delpi-ui-shape-effects__list delpi-ui-shape-shadow__presets">
            {presets.map((preset) => {
              const selected = preset.id === activePresetId;
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
                      setColorOpen(false);
                    }}
                  >
                    {preset.label}
                  </button>
                </li>
              );
            })}
          </ul>

          {isCustom ? (
            <p className="delpi-ui-shape-shadow__custom-hint">{L.shadowCustom}</p>
          ) : null}

          <div
            className={[
              "delpi-ui-shape-shadow__fields",
              !hasShadow ? "delpi-ui-shape-shadow__fields--inactive" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label={L.shadow}
          >
            {fields.map((field) => (
              <label key={field.key} className="delpi-ui-shape-shadow__field">
                <span>{field.label}</span>
                <input
                  type="number"
                  step={field.step ?? 1}
                  value={hasShadow && Number.isFinite(field.value) ? field.value : ""}
                  placeholder={String(field.value)}
                  aria-label={field.label}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => {
                    handleNumberChange(field.key, event.target.value);
                  }}
                />
              </label>
            ))}
          </div>

          <div className="delpi-ui-shape-shadow__color">
            <button
              type="button"
              className="delpi-ui-shape-menu__submenu-toggle"
              aria-expanded={colorOpen}
              onClick={() => {
                if (!hasShadow) applyModel(resolveBoxShadowModel(undefined));
                setColorOpen((prev) => !prev);
              }}
            >
              <span className="delpi-ui-shape-shadow__color-label">
                <span
                  className="delpi-ui-shape-menu__trigger-swatch"
                  style={{ background: colorCss }}
                  aria-hidden="true"
                />
                {L.shadowColor}
              </span>
            </button>
            {colorOpen ? (
              <ColorPickerPopover
                value={model.colorHex}
                onChange={handleColorChange}
                showNoFill={false}
                labels={labels}
              />
            ) : null}
          </div>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
