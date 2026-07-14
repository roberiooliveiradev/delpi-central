import { ALargeSmall, FlipVertical2 } from "lucide-react";
import { useState } from "react";
import {
  COMUNICADO_TEXT_SHADOW_PRESETS,
  resolveTextShadowPresetId,
} from "@delpi/tv-dashboard-presentation";
import { FieldLabel, HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { TextFormatStyleSnapshot } from "../../utils/selectedTextFormatTarget";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { TdRibbonSelect } from "../tdRibbonUi";
import { Modal } from "../ui/Modal";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Espessuras do contorno tipográfico (pt). */
const TEXT_STROKE_WIDTH_OPTIONS = [0, 0.5, 1, 1.5, 2, 3, 4, 6, 8] as const;

type Props = {
  formatStyle: TextFormatStyleSnapshot | undefined;
  onUpdate: (patch: TextFormatStyleSnapshot) => void;
};

/**
 * Tile «Efeitos» + modal central com Contorno, Espessura, Sombra e Reflexo
 * (concentra os controles estilo WordArt / Efeitos de texto do PPT).
 */
export function TextEffectsMenu({ formatStyle, onUpdate }: Props) {
  const [open, setOpen] = useState(false);
  const hasEffects = Boolean(
    formatStyle?.textStrokeColor ||
      (formatStyle?.textStrokeWidth ?? 0) > 0 ||
      formatStyle?.textShadow ||
      formatStyle?.textReflection,
  );

  return (
    <div className="td-text-effects-entry td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
      <HintAction hint={H.textEffects} ariaLabel="Ajuda: Efeitos de texto">
        <button
          type="button"
          className={[
            "delpi-ui-shape-menu__trigger",
            hasEffects ? "td-text-effects-entry__trigger--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          aria-label="Efeitos de texto"
          aria-haspopup="dialog"
          aria-expanded={open}
          onClick={() => setOpen(true)}
        >
          <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
            <ALargeSmall size={18} strokeWidth={hasEffects ? 2.25 : 1.75} />
          </span>
          <span className="delpi-ui-shape-menu__trigger-label">Efeitos</span>
        </button>
      </HintAction>

      <Modal
        open={open}
        title="Efeitos de texto"
        onClose={() => setOpen(false)}
        className="td-modal--text-effects"
        footer={
          <div className="td-modal-actions td-modal-actions--end">
            <button type="button" className="td-btn td-btn--primary" onClick={() => setOpen(false)}>
              Concluir
            </button>
          </div>
        }
      >
        <div className="td-text-effects-modal" role="group" aria-label="Efeitos de texto">
          <div className="td-text-effects-modal__row">
            <TvRibbonColorPicker
              hint={H.textStroke}
              label="Contorno"
              ariaLabel="Contorno do texto"
              variant="outline"
              value={formatStyle?.textStrokeColor ?? ""}
              onChange={(color) =>
                onUpdate({
                  textStrokeColor: color,
                  textStrokeWidth:
                    formatStyle?.textStrokeWidth && formatStyle.textStrokeWidth > 0
                      ? formatStyle.textStrokeWidth
                      : 1,
                })
              }
              onNoFill={() =>
                onUpdate({
                  textStrokeColor: undefined,
                  textStrokeWidth: 0,
                })
              }
            />
            <div className="td-text-effects-modal__field">
              <FieldLabel
                htmlFor="td-modal-text-stroke-w"
                label="Espessura"
                hint={H.textStroke}
                className="td-deck-ribbon__field-label"
              />
              <TdRibbonSelect
                id="td-modal-text-stroke-w"
                className="td-deck-ribbon__select--stroke-w"
                aria-label="Espessura do contorno"
                value={String(formatStyle?.textStrokeWidth ?? 0)}
                options={TEXT_STROKE_WIDTH_OPTIONS.map((width) => ({
                  value: String(width),
                  label: width === 0 ? "Sem" : `${width} pt`,
                }))}
                onChange={(value) => {
                  const width = Math.max(0, Number(value) || 0);
                  onUpdate({
                    textStrokeWidth: width,
                    textStrokeColor:
                      width > 0
                        ? formatStyle?.textStrokeColor || formatStyle?.color || "#0f172a"
                        : undefined,
                  });
                }}
              />
            </div>
          </div>

          <div className="td-text-effects-modal__row">
            <div className="td-text-effects-modal__field td-text-effects-modal__field--shadow">
              <FieldLabel
                htmlFor="td-modal-text-shadow"
                label="Sombra"
                hint={H.textEffects}
                className="td-deck-ribbon__field-label"
              />
              <TdRibbonSelect
                id="td-modal-text-shadow"
                className="td-deck-ribbon__select--shadow"
                aria-label="Sombra do texto"
                value={resolveTextShadowPresetId(formatStyle?.textShadow)}
                options={[
                  ...COMUNICADO_TEXT_SHADOW_PRESETS.map((preset) => ({
                    value: preset.id,
                    label: preset.label,
                  })),
                  ...(resolveTextShadowPresetId(formatStyle?.textShadow) === "custom"
                    ? [{ value: "custom", label: "Personalizada" }]
                    : []),
                ]}
                onChange={(value) => {
                  const preset = COMUNICADO_TEXT_SHADOW_PRESETS.find((item) => item.id === value);
                  onUpdate({
                    textShadow: value === "none" ? "" : (preset?.value ?? formatStyle?.textShadow),
                  });
                }}
              />
            </div>
            <HintAction hint={H.textReflection} ariaLabel="Ajuda: Reflexo tipográfico">
              <button
                type="button"
                className={[
                  "td-text-effects-modal__reflection",
                  formatStyle?.textReflection ? "td-text-effects-modal__reflection--on" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-pressed={Boolean(formatStyle?.textReflection)}
                onClick={() =>
                  onUpdate({ textReflection: !formatStyle?.textReflection })
                }
              >
                <FlipVertical2 size={16} aria-hidden="true" />
                Reflexo
              </button>
            </HintAction>
          </div>
        </div>
      </Modal>
    </div>
  );
}
