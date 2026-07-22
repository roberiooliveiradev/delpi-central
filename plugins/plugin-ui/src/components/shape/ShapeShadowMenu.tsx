import { Cloud } from "lucide-react";
import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { useRibbonSectionPopoverSurface } from "../ribbon/RibbonGroupSurfaceContext";
import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import {
  MAX_BOX_SHADOW_LAYERS,
  addBoxShadowLayer,
  boxShadowsEqual,
  formatBoxShadowStack,
  patchBoxShadow,
  removeBoxShadowLayer,
  resolveBoxShadowStack,
  type BoxShadowModel,
} from "./boxShadowModel";
import { ColorPickerPopover } from "./ColorPickerPopover";
import { colorToCss, cssToColorValue } from "./colorUtils";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";

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

/** Menu de sombra: presets + inset + até 2 camadas + X/Y/blur/spread/cor/opacidade. */
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
  const [layerIndex, setLayerIndex] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inline = useRibbonSectionPopoverSurface();

  const dismiss = () => {
    setOpen(false);
    setColorOpen(false);
  };

  const hasShadow = Boolean(value?.trim());
  const stack = resolveBoxShadowStack(value);
  const layerCount = stack.layers.length;
  const safeLayerIndex = Math.min(layerIndex, Math.max(0, layerCount - 1));
  const model = stack.layers[safeLayerIndex] ?? stack.layers[0]!;

  useEffect(() => {
    if (layerIndex > layerCount - 1) {
      setLayerIndex(Math.max(0, layerCount - 1));
    }
  }, [layerCount, layerIndex]);

  const activePresetId = presets.find((preset) =>
    boxShadowsEqual(preset.value, value),
  )?.id;
  const isCustom = hasShadow && !activePresetId;

  const applyStack = (nextCss: string) => {
    onChange(nextCss);
  };

  const applyPatch = (patch: Partial<BoxShadowModel>) => {
    applyStack(patchBoxShadow(value, patch, safeLayerIndex));
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

  const showColorPanel = inline || colorOpen;

  const panel = (
    <>
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
                      setLayerIndex(0);
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

          <div className="delpi-ui-shape-shadow__preview" aria-label={L.shadowPreview}>
            <div
              className="delpi-ui-shape-shadow__preview-card"
              style={{ boxShadow: hasShadow ? value : "none" }}
            />
          </div>

          <div
            className={[
              "delpi-ui-shape-shadow__mode",
              !hasShadow ? "delpi-ui-shape-shadow__fields--inactive" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            role="group"
            aria-label={L.shadow}
          >
            <button
              type="button"
              className={[
                "delpi-ui-shape-shadow__mode-btn",
                !model.inset ? "delpi-ui-shape-shadow__mode-btn--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-pressed={!model.inset}
              onClick={() => applyPatch({ inset: false })}
            >
              {L.shadowOuter}
            </button>
            <button
              type="button"
              className={[
                "delpi-ui-shape-shadow__mode-btn",
                model.inset ? "delpi-ui-shape-shadow__mode-btn--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-pressed={model.inset}
              onClick={() => applyPatch({ inset: true })}
            >
              {L.shadowInner}
            </button>
          </div>

          <div className="delpi-ui-shape-shadow__layers" role="tablist" aria-label={L.shadowLayer}>
            {stack.layers.map((_, index) => (
              <button
                key={index}
                type="button"
                role="tab"
                aria-selected={index === safeLayerIndex}
                className={[
                  "delpi-ui-shape-shadow__layer-btn",
                  index === safeLayerIndex ? "delpi-ui-shape-shadow__layer-btn--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => {
                  setLayerIndex(index);
                  setColorOpen(false);
                }}
              >
                {L.shadowLayer} {index + 1}
              </button>
            ))}
            {hasShadow && layerCount < MAX_BOX_SHADOW_LAYERS ? (
              <button
                type="button"
                className="delpi-ui-shape-shadow__layer-btn delpi-ui-shape-shadow__layer-btn--add"
                onClick={() => {
                  applyStack(addBoxShadowLayer(value));
                  setLayerIndex(1);
                  setColorOpen(false);
                }}
              >
                + {L.shadowAddLayer}
              </button>
            ) : null}
            {hasShadow && layerCount > 1 ? (
              <button
                type="button"
                className="delpi-ui-shape-shadow__layer-btn delpi-ui-shape-shadow__layer-btn--remove"
                onClick={() => {
                  applyStack(removeBoxShadowLayer(value, safeLayerIndex));
                  setLayerIndex(0);
                  setColorOpen(false);
                }}
              >
                {L.shadowRemoveLayer}
              </button>
            ) : null}
          </div>

          <div
            className={[
              "delpi-ui-shape-shadow__fields",
              !hasShadow ? "delpi-ui-shape-shadow__fields--inactive" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label={`${L.shadowLayer} ${safeLayerIndex + 1}`}
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
              aria-expanded={showColorPanel}
              onClick={() => {
                if (!hasShadow) {
                  applyStack(formatBoxShadowStack(resolveBoxShadowStack(undefined)));
                }
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
            {showColorPanel ? (
              <ColorPickerPopover
                value={model.colorHex}
                onChange={handleColorChange}
                showNoFill={false}
                labels={labels}
              />
            ) : null}
          </div>
    </>
  );

  if (inline) {
    return (
      <div
        className="delpi-ui-shape-menu delpi-ui-shape-menu--inline delpi-ui-shape-menu__panel--shadow"
        aria-label={shadowLabel ?? L.shadow}
      >
        {panel}
      </div>
    );
  }

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
          onDismiss={dismiss}
        >
          {panel}
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
