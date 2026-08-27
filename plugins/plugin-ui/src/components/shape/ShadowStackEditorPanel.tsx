import { useEffect, useState, type ChangeEvent } from "react";

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
import {
  MAX_TEXT_SHADOW_LAYERS,
  addTextShadowLayer,
  formatTextShadowStack,
  patchTextShadow,
  removeTextShadowLayer,
  resolveTextShadowStack,
  textShadowsEqual,
  type TextShadowModel,
} from "./textShadowModel";
import type { ShapeColorLabels } from "./types";

export type ShadowStackPreset = {
  id: string;
  label: string;
  /** CSS shadow; omitido = sem sombra. */
  value?: string;
};

export type ShadowStackEditorPanelProps = {
  mode: "box" | "text";
  value?: string;
  presets: readonly ShadowStackPreset[];
  onChange: (value: string | undefined) => void;
  labels?: ShapeColorLabels;
};

type ShadowFieldKey = "offsetX" | "offsetY" | "blur" | "spread" | "opacityPercent";

function clampField(key: ShadowFieldKey, value: number): number {
  if (key === "offsetX" || key === "offsetY") return Math.min(80, Math.max(-80, value));
  if (key === "blur") return Math.min(120, Math.max(0, value));
  if (key === "spread") return Math.min(60, Math.max(-40, value));
  return Math.min(100, Math.max(0, value));
}

type ShadowLayerModel = {
  inset?: boolean;
  offsetX: number;
  offsetY: number;
  blur: number;
  spread?: number;
  colorHex: string;
  opacity: number;
};

/** Painel compartilhado de presets + pilha + campos numéricos (forma ou texto). */
export function ShadowStackEditorPanel({
  mode,
  value,
  presets,
  onChange,
  labels,
}: ShadowStackEditorPanelProps) {
  const L = mergeShapeColorLabels(labels);
  const [colorOpen, setColorOpen] = useState(false);
  const [layerIndex, setLayerIndex] = useState(0);
  const isText = mode === "text";

  const hasShadow = Boolean(value?.trim());
  const maxLayers = isText ? MAX_TEXT_SHADOW_LAYERS : MAX_BOX_SHADOW_LAYERS;
  const stack = isText ? resolveTextShadowStack(value) : resolveBoxShadowStack(value);
  const layerCount = stack.layers.length;
  const safeLayerIndex = Math.min(layerIndex, Math.max(0, layerCount - 1));
  const rawLayer = stack.layers[safeLayerIndex] ?? stack.layers[0]!;
  const model: ShadowLayerModel = isText
    ? (rawLayer as TextShadowModel)
    : {
        inset: (rawLayer as BoxShadowModel).inset,
        offsetX: rawLayer.offsetX,
        offsetY: rawLayer.offsetY,
        blur: rawLayer.blur,
        spread: (rawLayer as BoxShadowModel).spread,
        colorHex: rawLayer.colorHex,
        opacity: rawLayer.opacity,
      };

  useEffect(() => {
    if (layerIndex > layerCount - 1) {
      setLayerIndex(Math.max(0, layerCount - 1));
    }
  }, [layerCount, layerIndex]);

  const shadowsEqual = isText ? textShadowsEqual : boxShadowsEqual;
  const activePresetId = presets.find((preset) => shadowsEqual(preset.value, value))?.id;
  const isCustom = hasShadow && !activePresetId;

  const applyStack = (nextCss: string) => {
    onChange(nextCss);
  };

  const applyPatch = (patch: Partial<ShadowLayerModel>) => {
    if (isText) {
      const textPatch: Partial<TextShadowModel> = {
        offsetX: patch.offsetX,
        offsetY: patch.offsetY,
        blur: patch.blur,
        colorHex: patch.colorHex,
        opacity: patch.opacity,
      };
      applyStack(patchTextShadow(value, textPatch, safeLayerIndex));
      return;
    }
    applyStack(
      patchBoxShadow(
        value,
        {
          inset: patch.inset,
          offsetX: patch.offsetX,
          offsetY: patch.offsetY,
          blur: patch.blur,
          spread: patch.spread,
          colorHex: patch.colorHex,
          opacity: patch.opacity,
        },
        safeLayerIndex,
      ),
    );
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
    ...(isText
      ? []
      : [{ key: "spread" as const, label: L.shadowSpread, value: model.spread ?? 0 }]),
    {
      key: "opacityPercent",
      label: L.shadowOpacity,
      value: Math.round(model.opacity * 100),
      step: 1,
    },
  ];

  const showColorPanel = colorOpen;
  const defaultStackCss = isText
    ? formatTextShadowStack(resolveTextShadowStack(undefined))
    : formatBoxShadowStack(resolveBoxShadowStack(undefined));

  return (
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
        {isText ? (
          <span
            className="delpi-ui-text-shadow__preview-sample"
            style={{ textShadow: hasShadow ? value : "none" }}
            aria-hidden="true"
          >
            Ag
          </span>
        ) : (
          <div
            className="delpi-ui-shape-shadow__preview-card"
            style={{ boxShadow: hasShadow ? value : "none" }}
          />
        )}
      </div>

      {!isText ? (
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
            aria-pressed={Boolean(model.inset)}
            onClick={() => applyPatch({ inset: true })}
          >
            {L.shadowInner}
          </button>
        </div>
      ) : null}

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
        {hasShadow && layerCount < maxLayers ? (
          <button
            type="button"
            className="delpi-ui-shape-shadow__layer-btn delpi-ui-shape-shadow__layer-btn--add"
            onClick={() => {
              applyStack(isText ? addTextShadowLayer(value) : addBoxShadowLayer(value));
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
              applyStack(
                isText
                  ? removeTextShadowLayer(value, safeLayerIndex)
                  : removeBoxShadowLayer(value, safeLayerIndex),
              );
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
              applyStack(defaultStackCss);
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
}
