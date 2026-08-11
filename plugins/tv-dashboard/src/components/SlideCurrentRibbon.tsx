import { Copy, Download, Eye, EyeOff, Trash2 } from "lucide-react";

import type { Slide } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DECK_HOME_ACTION_KEYTIPS } from "../utils/deckKeyTips";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

type Props = {
  selectedSlide: Slide | null;
  selectedSlides?: Slide[];
  onDuplicate?: (targets: Slide[]) => void;
  onToggleActive?: (targets: Slide[]) => void;
  onRemove?: (targets: Slide[]) => void;
  onExportPng?: () => void;
  onExportPdf?: () => void;
  onExportPptx?: () => void;
  exportBusy?: boolean;
};

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const C = TV_DASHBOARD_HELP_TOOLTIPS.filmstripContextMenu;
const K = DECK_HOME_ACTION_KEYTIPS;

function formatCount(template: string, count: number): string {
  return template.replace("{count}", String(count));
}

/** Ações da tela atual — aba Tela do editor. Export cobre a seleção do filmstrip. */
export function SlideCurrentRibbon({
  selectedSlide,
  selectedSlides: selectedSlidesProp,
  onDuplicate,
  onToggleActive,
  onRemove,
  onExportPng,
  onExportPdf,
  onExportPptx,
  exportBusy = false,
}: Props) {
  const targets =
    selectedSlidesProp && selectedSlidesProp.length > 0
      ? selectedSlidesProp
      : selectedSlide
        ? [selectedSlide]
        : [];
  const primary = selectedSlide ?? targets[targets.length - 1] ?? null;
  if (!primary || targets.length === 0) return null;

  const hasDeckActions = Boolean(onDuplicate || onToggleActive || onRemove);
  const hasExport = Boolean(onExportPng || onExportPdf || onExportPptx);
  if (!hasDeckActions && !hasExport) return null;

  const many = targets.length > 1;
  const allInactive = targets.every((slide) => !slide.isActive);

  return (
    <DeckRibbonGroup
      groupId="slide-current"
      label={many ? formatCount(H.currentSlides, targets.length) : "Tela atual"}
      hint={many ? formatCount(H.currentSlides, targets.length) : H.currentSlide}
    >
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        {onToggleActive ? (
          <DeckRibbonTile
            icon={allInactive ? EyeOff : Eye}
            label={allInactive ? "Ativar" : "Pausar"}
            hint={allInactive ? H.activate : H.pause}
            keyTip={K.toggleActive}
            onClick={() => onToggleActive(targets)}
          />
        ) : null}
        {onDuplicate ? (
          <DeckRibbonTile
            icon={Copy}
            label={many ? formatCount(C.duplicateMany, targets.length) : "Duplicar"}
            hint={many ? formatCount(C.duplicateMany, targets.length) : H.duplicate}
            keyTip={K.duplicate}
            onClick={() => onDuplicate(targets)}
          />
        ) : null}
        {onExportPng ? (
          <DeckRibbonTile
            icon={Download}
            label={exportBusy ? "…" : "PNG"}
            hint={many ? formatCount(H.exportPngMany, targets.length) : H.exportPng}
            disabled={exportBusy}
            keyTip={K.exportPng}
            onClick={onExportPng}
          />
        ) : null}
        {onExportPdf ? (
          <DeckRibbonTile
            icon={Download}
            label={exportBusy ? "…" : "PDF"}
            hint={many ? formatCount(H.exportPdfMany, targets.length) : H.exportPdf}
            disabled={exportBusy}
            keyTip={K.exportPdf}
            onClick={onExportPdf}
          />
        ) : null}
        {onExportPptx ? (
          <DeckRibbonTile
            icon={Download}
            label={exportBusy ? "…" : "PPTX"}
            hint={many ? H.exportPptxMany : H.exportPptx}
            disabled={exportBusy}
            keyTip={K.exportPptx}
            onClick={onExportPptx}
          />
        ) : null}
        {onRemove ? (
          <DeckRibbonTile
            icon={Trash2}
            label={many ? formatCount(C.deleteMany, targets.length) : "Excluir"}
            hint={many ? formatCount(C.deleteMany, targets.length) : H.delete}
            keyTip={K.remove}
            onClick={() => onRemove(targets)}
          />
        ) : null}
      </div>
    </DeckRibbonGroup>
  );
}
