import { useCallback, useRef, type PointerEvent as ReactPointerEvent } from "react";

import {
  clampAlpha,
  clampByte,
  colorValueToHsv,
  hexToRgb,
  hsvToColorValue,
  hueToHex,
  normalizeHex,
  rgbToHex,
} from "./colorUtils";
import type { ColorValue } from "./types";

type Labels = {
  red: string;
  green: string;
  blue: string;
  hex: string;
  colorModel: string;
};

type Props = {
  value: ColorValue;
  onChange: (value: ColorValue) => void;
  labels: Labels;
};

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function ColorCustomPanel({ value, onChange, labels }: Props) {
  const hsv = colorValueToHsv(value);
  const svRef = useRef<HTMLDivElement>(null);
  const hueRef = useRef<HTMLDivElement>(null);

  const applyHsv = useCallback(
    (next: { h?: number; s?: number; v?: number }) => {
      onChange(
        hsvToColorValue(
          {
            h: next.h ?? hsv.h,
            s: next.s ?? hsv.s,
            v: next.v ?? hsv.v,
          },
          value.alpha,
        ),
      );
    },
    [hsv.h, hsv.s, hsv.v, onChange, value.alpha],
  );

  const pickSv = useCallback(
    (clientX: number, clientY: number) => {
      const node = svRef.current;
      if (!node) return;
      const rect = node.getBoundingClientRect();
      const s = clamp01((clientX - rect.left) / rect.width);
      const v = clamp01(1 - (clientY - rect.top) / rect.height);
      applyHsv({ s, v });
    },
    [applyHsv],
  );

  const pickHue = useCallback(
    (clientY: number) => {
      const node = hueRef.current;
      if (!node) return;
      const rect = node.getBoundingClientRect();
      const ratio = clamp01((clientY - rect.top) / rect.height);
      applyHsv({ h: ratio * 360 });
    },
    [applyHsv],
  );

  const onSvPointer = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    pickSv(event.clientX, event.clientY);
  };

  const onSvPointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.buttons !== 1) return;
    pickSv(event.clientX, event.clientY);
  };

  const onHuePointer = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    pickHue(event.clientY);
  };

  const onHuePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.buttons !== 1) return;
    pickHue(event.clientY);
  };

  const { r, g, b } = hexToRgb(value.hex);

  const updateRgb = (channel: "r" | "g" | "b", next: number) => {
    const rgb = { r, g, b, [channel]: clampByte(next) };
    onChange({ hex: rgbToHex(rgb.r, rgb.g, rgb.b), alpha: value.alpha });
  };

  const hueColor = hueToHex(hsv.h);

  return (
    <div className="delpi-ui-shape-dialog__custom">
      <div className="delpi-ui-shape-dialog__pickers">
        <div
          ref={svRef}
          className="delpi-ui-shape-dialog__sv"
          role="application"
          aria-label="Saturação e brilho"
          style={{
            backgroundImage: `linear-gradient(to top, #000, transparent), linear-gradient(to right, #fff, ${hueColor})`,
          }}
          onPointerDown={onSvPointer}
          onPointerMove={onSvPointerMove}
        >
          <span
            className="delpi-ui-shape-dialog__sv-cursor"
            style={{
              left: `${hsv.s * 100}%`,
              top: `${(1 - hsv.v) * 100}%`,
            }}
            aria-hidden="true"
          />
        </div>
        <div
          ref={hueRef}
          className="delpi-ui-shape-dialog__hue"
          role="slider"
          aria-label="Matiz"
          aria-valuemin={0}
          aria-valuemax={360}
          aria-valuenow={Math.round(hsv.h)}
          onPointerDown={onHuePointer}
          onPointerMove={onHuePointerMove}
        >
          <span
            className="delpi-ui-shape-dialog__hue-cursor"
            style={{ top: `${(hsv.h / 360) * 100}%` }}
            aria-hidden="true"
          />
        </div>
      </div>

      <label className="delpi-ui-shape-dialog__model">
        <span>{labels.colorModel}</span>
        <select defaultValue="rgb" aria-label={labels.colorModel}>
          <option value="rgb">RGB</option>
        </select>
      </label>

      <div className="delpi-ui-shape-dialog__rgb">
        <NumberField label={labels.red} value={r} onChange={(next) => updateRgb("r", next)} />
        <NumberField label={labels.green} value={g} onChange={(next) => updateRgb("g", next)} />
        <NumberField label={labels.blue} value={b} onChange={(next) => updateRgb("b", next)} />
      </div>

      <label className="delpi-ui-shape-dialog__hex">
        <span>{labels.hex}</span>
        <span className="delpi-ui-shape-dialog__hex-field">
          <span className="delpi-ui-shape-dialog__hex-prefix" aria-hidden="true">
            #
          </span>
          <input
            type="text"
            inputMode="text"
            autoComplete="off"
            spellCheck={false}
            value={normalizeHex(value.hex).slice(1).toUpperCase()}
            maxLength={6}
            onChange={(event) => {
              const raw = event.target.value.replace(/[^0-9a-f]/gi, "").slice(0, 6);
              if (raw.length === 3 || raw.length === 6) {
                onChange({ hex: normalizeHex(`#${raw}`), alpha: value.alpha });
              }
            }}
          />
        </span>
      </label>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="delpi-ui-shape-dialog__number">
      <span>{label}</span>
      <input
        type="number"
        min={0}
        max={255}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

export function ColorTransparencyRow({
  value,
  onChange,
  label,
}: {
  value: ColorValue;
  onChange: (value: ColorValue) => void;
  label: string;
}) {
  const transparencyPct = Math.round((1 - value.alpha) * 100);
  return (
    <label className="delpi-ui-shape-dialog__alpha">
      <span>{label}</span>
      <input
        type="range"
        min={0}
        max={100}
        value={transparencyPct}
        onChange={(event) =>
          onChange({
            ...value,
            alpha: clampAlpha(1 - Number(event.target.value) / 100),
          })
        }
      />
      <span className="delpi-ui-shape-dialog__alpha-value">{transparencyPct}%</span>
    </label>
  );
}
