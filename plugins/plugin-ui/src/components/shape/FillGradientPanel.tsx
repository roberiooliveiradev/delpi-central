import { Minus, Plus } from "lucide-react";
import { useState } from "react";

import { ColorStandardRow, ColorThemeGrid } from "./ColorThemeGrid";
import {
  DEFAULT_LINEAR_GRADIENT_PRESETS,
  MAX_GRADIENT_STOPS,
  MIN_GRADIENT_STOPS,
  fillToCssBackground,
  normalizeFillAngle,
  normalizeGradientStops,
  type DelpiFillGradient,
  type DelpiGradientStop,
} from "./fillTypes";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";

type Props = {
  value: DelpiFillGradient;
  onChange: (fill: DelpiFillGradient) => void;
  labels?: ShapeColorLabels;
  themeRows: readonly (readonly string[])[];
  standardColors: readonly string[];
  presets?: readonly DelpiFillGradient[];
};

export function FillGradientPanel({
  value,
  onChange,
  labels,
  themeRows,
  standardColors,
  presets = DEFAULT_LINEAR_GRADIENT_PRESETS,
}: Props) {
  const L = mergeShapeColorLabels(labels);
  const stops = normalizeGradientStops(value.stops);
  const [activeIndex, setActiveIndex] = useState(0);
  const safeIndex = Math.min(activeIndex, stops.length - 1);
  const active = stops[safeIndex] ?? stops[0]!;

  function emit(next: Partial<DelpiFillGradient> & { stops?: DelpiGradientStop[] }) {
    onChange({
      kind: "gradient",
      angle: normalizeFillAngle(next.angle ?? value.angle),
      stops: normalizeGradientStops(next.stops ?? stops),
    });
  }

  function patchActive(patch: Partial<DelpiGradientStop>) {
    emit({
      stops: stops.map((stop, index) => (index === safeIndex ? { ...stop, ...patch } : stop)),
    });
  }

  function addStop() {
    if (stops.length >= MAX_GRADIENT_STOPS) return;
    const left = stops[safeIndex] ?? stops[0]!;
    const right = stops[safeIndex + 1] ?? stops[stops.length - 1]!;
    const position = Math.round((left.position + right.position) / 2);
    const nextStops = normalizeGradientStops([...stops, { color: left.color, position }]);
    const inserted = nextStops.findIndex((stop) => stop.position === position);
    emit({ stops: nextStops });
    setActiveIndex(inserted >= 0 ? inserted : nextStops.length - 1);
  }

  function removeStop() {
    if (stops.length <= MIN_GRADIENT_STOPS) return;
    const nextStops = stops.filter((_, index) => index !== safeIndex);
    emit({ stops: nextStops });
    setActiveIndex(Math.max(0, safeIndex - 1));
  }

  return (
    <div className="delpi-ui-fill-gradient">
      {presets.length > 0 ? (
        <section className="delpi-ui-color-picker__section">
          <h4 className="delpi-ui-color-picker__heading">{L.fillPresets}</h4>
          <div className="delpi-ui-fill-presets" role="list">
            {presets.map((preset, index) => (
              <button
                key={`${preset.angle}-${index}`}
                type="button"
                className="delpi-ui-fill-preset"
                style={{ background: fillToCssBackground(preset) }}
                aria-label={`${L.fillPresets} ${index + 1}`}
                onClick={() => onChange({ ...preset, stops: normalizeGradientStops(preset.stops) })}
              />
            ))}
          </div>
        </section>
      ) : null}

      <label className="delpi-ui-fill-angle">
        <span>{L.fillAngle}</span>
        <input
          type="number"
          min={0}
          max={359}
          value={normalizeFillAngle(value.angle)}
          onChange={(event) => emit({ angle: Number(event.target.value) })}
        />
      </label>

      <div className="delpi-ui-fill-stops">
        <div
          className="delpi-ui-fill-stops__bar"
          style={{ background: fillToCssBackground({ ...value, stops }) }}
        >
          {stops.map((stop, index) => (
            <button
              key={`${stop.position}-${index}`}
              type="button"
              className={[
                "delpi-ui-fill-stops__mark",
                index === safeIndex ? "delpi-ui-fill-stops__mark--active" : null,
              ]
                .filter(Boolean)
                .join(" ")}
              style={{ left: `${stop.position}%`, background: stop.color }}
              aria-label={`${L.fillStopPosition} ${stop.position}%`}
              onClick={() => setActiveIndex(index)}
            />
          ))}
        </div>
        <div className="delpi-ui-fill-stops__actions">
          <button
            type="button"
            className="delpi-ui-fill-stops__btn"
            aria-label={L.fillAddStop}
            disabled={stops.length >= MAX_GRADIENT_STOPS}
            onClick={addStop}
          >
            <Plus size={14} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="delpi-ui-fill-stops__btn"
            aria-label={L.fillRemoveStop}
            disabled={stops.length <= MIN_GRADIENT_STOPS}
            onClick={removeStop}
          >
            <Minus size={14} aria-hidden="true" />
          </button>
        </div>
      </div>

      <label className="delpi-ui-fill-angle">
        <span>{L.fillStopPosition}</span>
        <input
          type="number"
          min={0}
          max={100}
          value={Math.round(active.position)}
          onChange={(event) => patchActive({ position: Number(event.target.value) })}
        />
      </label>
      <label className="delpi-ui-fill-angle">
        <span>{L.fillStopOpacity}</span>
        <input
          type="number"
          min={0}
          max={100}
          value={Math.round((active.opacity ?? 1) * 100)}
          onChange={(event) => patchActive({ opacity: Number(event.target.value) / 100 })}
        />
      </label>

      <section className="delpi-ui-color-picker__section">
        <h4 className="delpi-ui-color-picker__heading">{L.themeColors}</h4>
        <ColorThemeGrid
          rows={themeRows}
          value={active.color}
          onSelect={(color) => patchActive({ color })}
          ariaLabel={L.themeColors}
        />
      </section>
      <section className="delpi-ui-color-picker__section">
        <h4 className="delpi-ui-color-picker__heading">{L.standardColors}</h4>
        <ColorStandardRow
          colors={standardColors}
          value={active.color}
          onSelect={(color) => patchActive({ color })}
          ariaLabel={L.standardColors}
        />
      </section>
    </div>
  );
}
