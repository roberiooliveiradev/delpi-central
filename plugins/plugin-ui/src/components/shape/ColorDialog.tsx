import { useEffect, useId, useState, type ReactNode } from "react";

import { ModalShell, modalShellBemClasses } from "../feedback/ModalShell";
import { DELPI_DIALOG_STANDARD_COLORS } from "./colorPalettes";
import { ColorSwatch } from "./ColorThemeGrid";
import {
  clampAlpha,
  clampByte,
  colorToCss,
  cssToColorValue,
  normalizeHex,
  parseHexColor,
  rgbToHex,
} from "./colorUtils";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ColorValue, ShapeColorLabels } from "./types";

export type ColorDialogProps = {
  open: boolean;
  value?: string;
  onClose: () => void;
  onConfirm: (color: string) => void;
  labels?: ShapeColorLabels;
};

export function ColorDialog({ open, value, onClose, onConfirm, labels }: ColorDialogProps) {
  const L = mergeShapeColorLabels(labels);
  const classNames = modalShellBemClasses("delpi-ui-shape");
  const [tab, setTab] = useState<"standard" | "custom">("standard");
  const initial = cssToColorValue(value ?? "#089bdb");
  const [draft, setDraft] = useState<ColorValue>(initial);

  useEffect(() => {
    if (open) {
      setDraft(cssToColorValue(value ?? "#089bdb"));
      setTab("standard");
    }
  }, [open, value]);

  const { r, g, b } = {
    r: clampByte(parseInt(normalizeHex(draft.hex).slice(1, 3), 16)),
    g: clampByte(parseInt(normalizeHex(draft.hex).slice(3, 5), 16)),
    b: clampByte(parseInt(normalizeHex(draft.hex).slice(5, 7), 16)),
  };

  const updateRgb = (channel: "r" | "g" | "b", next: number) => {
    const rgb = { r, g, b, [channel]: clampByte(next) };
    setDraft((prev) => ({ ...prev, hex: rgbToHex(rgb.r, rgb.g, rgb.b) }));
  };

  const footer = (
    <>
      <button type="button" className="delpi-ui-shape-btn delpi-ui-shape-btn--ghost" onClick={onClose}>
        {L.cancel}
      </button>
      <button
        type="button"
        className="delpi-ui-shape-btn delpi-ui-shape-btn--primary"
        onClick={() => {
          onConfirm(colorToCss(draft));
          onClose();
        }}
      >
        {L.ok}
      </button>
    </>
  );

  return (
    <ModalShell
      open={open}
      title={L.colorDialogTitle}
      onClose={onClose}
      classNames={{
        ...classNames,
        footer: "delpi-ui-shape-dialog__footer",
      }}
      footer={footer}
      className="delpi-ui-shape-dialog"
      overlayClassName="delpi-ui-shape-dialog-overlay"
    >
      <div className="delpi-ui-shape-dialog__tabs" role="tablist">
        <TabButton active={tab === "standard"} onClick={() => setTab("standard")}>
          {L.tabStandard}
        </TabButton>
        <TabButton active={tab === "custom"} onClick={() => setTab("custom")}>
          {L.tabCustom}
        </TabButton>
      </div>

      {tab === "standard" ? (
        <div className="delpi-ui-shape-dialog__standard-grid">
          {DELPI_DIALOG_STANDARD_COLORS.map((color) => (
            <ColorSwatch
              key={color}
              color={color}
              selected={normalizeHex(draft.hex) === normalizeHex(color)}
              onSelect={(next) => setDraft({ hex: next, alpha: draft.alpha })}
              className="delpi-ui-color-swatch--hexagon"
            />
          ))}
        </div>
      ) : (
        <div className="delpi-ui-shape-dialog__custom">
          <div className="delpi-ui-shape-dialog__spectrum-wrap">
            <input
              type="color"
              className="delpi-ui-shape-dialog__spectrum"
              value={normalizeHex(draft.hex)}
              aria-label="Espectro de cor"
              onChange={(event) => {
                const parsed = parseHexColor(event.target.value, draft.alpha);
                if (parsed) setDraft(parsed);
              }}
            />
          </div>
          <div className="delpi-ui-shape-dialog__rgb">
            <NumberField label={L.red} value={r} onChange={(next) => updateRgb("r", next)} />
            <NumberField label={L.green} value={g} onChange={(next) => updateRgb("g", next)} />
            <NumberField label={L.blue} value={b} onChange={(next) => updateRgb("b", next)} />
          </div>
          <label className="delpi-ui-shape-dialog__hex">
            <span>{L.hex}</span>
            <input
              type="text"
              value={normalizeHex(draft.hex).slice(1).toUpperCase()}
              maxLength={6}
              onChange={(event) => {
                const parsed = parseHexColor(`#${event.target.value}`, draft.alpha);
                if (parsed) setDraft(parsed);
              }}
            />
          </label>
          <label className="delpi-ui-shape-dialog__alpha">
            <span>{L.transparency}</span>
            <input
              type="range"
              min={0}
              max={100}
              value={Math.round((1 - draft.alpha) * 100)}
              onChange={(event) =>
                setDraft((prev) => ({
                  ...prev,
                  alpha: clampAlpha(1 - Number(event.target.value) / 100),
                }))
              }
            />
            <span className="delpi-ui-shape-dialog__alpha-value">
              {Math.round((1 - draft.alpha) * 100)}%
            </span>
          </label>
        </div>
      )}

      <div className="delpi-ui-shape-dialog__preview">
        <PreviewSwatch label={L.newColor} color={draft} />
        <PreviewSwatch label={L.currentColor} color={initial} />
      </div>
    </ModalShell>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      className={
        active
          ? "delpi-ui-shape-dialog__tab delpi-ui-shape-dialog__tab--active"
          : "delpi-ui-shape-dialog__tab"
      }
      onClick={onClick}
    >
      {children}
    </button>
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
  const id = useId();
  return (
    <label className="delpi-ui-shape-dialog__number" htmlFor={id}>
      <span>{label}</span>
      <input
        id={id}
        type="number"
        min={0}
        max={255}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function PreviewSwatch({ label, color }: { label: string; color: ColorValue }) {
  return (
    <div className="delpi-ui-shape-dialog__preview-item">
      <span className="delpi-ui-shape-dialog__preview-label">{label}</span>
      <span
        className="delpi-ui-shape-dialog__preview-swatch"
        style={{ background: colorToCss(color) }}
        aria-hidden="true"
      />
    </div>
  );
}
