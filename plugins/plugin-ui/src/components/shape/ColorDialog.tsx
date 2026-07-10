import { useEffect, useState, type ReactNode } from "react";

import { ModalShell, modalShellBemClasses } from "../feedback/ModalShell";
import { ColorCustomPanel, ColorTransparencyRow } from "./ColorCustomPanel";
import { ColorStandardRow, ColorThemeGrid } from "./ColorThemeGrid";
import { DELPI_STANDARD_COLORS, DELPI_THEME_COLOR_GRID } from "./colorPalettes";
import { colorToCss, cssToColorValue, normalizeHex } from "./colorUtils";
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
  const initial = cssToColorValue(value ?? "#ffffff");
  const [draft, setDraft] = useState<ColorValue>(initial);

  useEffect(() => {
    if (open) {
      setDraft(cssToColorValue(value ?? "#ffffff"));
      setTab("standard");
    }
  }, [open, value]);

  const confirm = () => {
    onConfirm(colorToCss(draft));
    onClose();
  };

  return (
    <ModalShell
      open={open}
      title={L.colorDialogTitle}
      onClose={onClose}
      classNames={classNames}
      className="delpi-ui-shape-dialog"
      overlayClassName="delpi-ui-shape-dialog-overlay"
    >
      <div className="delpi-ui-shape-dialog__layout">
        <div className="delpi-ui-shape-dialog__main">
          <div className="delpi-ui-shape-dialog__tabs" role="tablist">
            <TabButton active={tab === "standard"} onClick={() => setTab("standard")}>
              {L.tabStandard}
            </TabButton>
            <TabButton active={tab === "custom"} onClick={() => setTab("custom")}>
              {L.tabCustom}
            </TabButton>
          </div>

          {tab === "standard" ? (
            <div className="delpi-ui-shape-dialog__colors-box">
              <p className="delpi-ui-shape-dialog__colors-label">{L.themeColors}</p>
              <ColorThemeGrid
                rows={DELPI_THEME_COLOR_GRID}
                value={colorToCss(draft)}
                onSelect={(color) => setDraft({ hex: normalizeHex(color), alpha: draft.alpha })}
                ariaLabel={L.themeColors}
              />
              <p className="delpi-ui-shape-dialog__colors-label">{L.standardColors}</p>
              <ColorStandardRow
                colors={DELPI_STANDARD_COLORS}
                value={colorToCss(draft)}
                onSelect={(color) => setDraft({ hex: normalizeHex(color), alpha: draft.alpha })}
                ariaLabel={L.standardColors}
              />
            </div>
          ) : (
            <ColorCustomPanel
              value={draft}
              onChange={setDraft}
              labels={{
                red: L.red,
                green: L.green,
                blue: L.blue,
                hex: L.hex,
                colorModel: L.colorModel,
              }}
            />
          )}

          <ColorTransparencyRow value={draft} onChange={setDraft} label={L.transparency} />
        </div>

        <aside className="delpi-ui-shape-dialog__aside">
          <button type="button" className="delpi-ui-shape-btn delpi-ui-shape-btn--primary" onClick={confirm}>
            {L.ok}
          </button>
          <button type="button" className="delpi-ui-shape-btn delpi-ui-shape-btn--ghost" onClick={onClose}>
            {L.cancel}
          </button>
          <div className="delpi-ui-shape-dialog__preview-split" aria-hidden="true">
            <div
              className="delpi-ui-shape-dialog__preview-half delpi-ui-shape-dialog__preview-half--new"
              style={{ background: colorToCss(draft) }}
            >
              <span>{L.newColor}</span>
            </div>
            <div
              className="delpi-ui-shape-dialog__preview-half delpi-ui-shape-dialog__preview-half--current"
              style={{ background: colorToCss(initial) }}
            >
              <span>{L.currentColor}</span>
            </div>
          </div>
        </aside>
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
