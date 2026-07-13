import { ComboboxNumberControl, FieldLabel } from "@delpi/plugin-ui/index";
import { useMemo } from "react";
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";

import {
  STAGE_GRID_SIZE_MIN_PX,
  clampStageGridSizePx,
  stageGridSizeMaxPx,
  stageGridSizePresetsForDesign,
} from "../utils/stageGridSize";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { Modal } from "./ui/Modal";

type Props = {
  open: boolean;
  onClose: () => void;
};

/** Modal para escolher o tamanho da célula da grade (presets + digitação). */
export function StageGridSettingsModal({ open, onClose }: Props) {
  const {
    viewportProfile,
    showStageGrid,
    setShowStageGrid,
    stageGridSizePx,
    setStageGridSizePx,
  } = useComunicadoEditor();

  const design = useMemo(
    () => resolveViewportPixelSize(viewportProfile || "1080p"),
    [viewportProfile],
  );
  const maxPx = stageGridSizeMaxPx(design);
  const presets = useMemo(() => stageGridSizePresetsForDesign(design), [design]);
  const value = clampStageGridSizePx(stageGridSizePx, design);

  return (
    <Modal open={open} title="Tamanho da grade" onClose={onClose} className="td-modal--grid-settings">
      <p className="td-grid-settings__lead">
        Define o espaçamento da grade no palco (em pixels do slide). Mínimo{" "}
        {STAGE_GRID_SIZE_MIN_PX} px; máximo metade do menor lado ({maxPx} px neste viewport).
      </p>

      <div className="td-grid-settings__field">
        <FieldLabel
          label="Tamanho da célula (px)"
          hint="Escolha um valor da lista ou digite um tamanho intermediário."
          className="td-field__label"
        />
        <ComboboxNumberControl
          className="td-grid-settings__combobox"
          aria-label="Tamanho da célula da grade"
          value={value}
          options={presets}
          min={STAGE_GRID_SIZE_MIN_PX}
          max={maxPx}
          clamp={(raw) => clampStageGridSizePx(raw, design)}
          portalScopeClassName="dashboard-tv-dashboard"
          onChange={(next) => {
            setStageGridSizePx(clampStageGridSizePx(next, design));
            if (!showStageGrid) setShowStageGrid(true);
          }}
        />
      </div>

      <div className="td-grid-settings__actions">
        <button type="button" className="td-btn td-btn--primary" onClick={onClose}>
          Concluir
        </button>
      </div>
    </Modal>
  );
}
