import { useEffect, useState } from "react";

import { ModalShell, modalShellBemClasses } from "../feedback/ModalShell";
import { ColorMorePanel } from "./ColorMorePanel";
import { cssToColorValue } from "./colorUtils";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";

export type ColorDialogProps = {
  open: boolean;
  value?: string;
  onClose: () => void;
  onConfirm: (color: string) => void;
  labels?: ShapeColorLabels;
};

/**
 * Modal legado «Cores» (catálogo / demos). No editor, use o popover «Mais cores»
 * em ColorPickerPopover.
 */
export function ColorDialog({ open, value, onClose, onConfirm, labels }: ColorDialogProps) {
  const L = mergeShapeColorLabels(labels);
  const classNames = modalShellBemClasses("delpi-ui-shape");
  const [panelKey, setPanelKey] = useState(0);

  useEffect(() => {
    if (open) {
      setPanelKey((key) => key + 1);
      void cssToColorValue(value ?? "#ffffff");
    }
  }, [open, value]);

  return (
    <ModalShell
      open={open}
      title={L.colorDialogTitle}
      onClose={onClose}
      classNames={classNames}
      className="delpi-ui-shape-dialog"
      overlayClassName="delpi-ui-shape-dialog-overlay"
    >
      {open ? (
        <ColorMorePanel
          key={panelKey}
          value={value}
          onConfirm={(color) => {
            onConfirm(color);
            onClose();
          }}
          onCancel={onClose}
          labels={labels}
        />
      ) : null}
    </ModalShell>
  );
}
