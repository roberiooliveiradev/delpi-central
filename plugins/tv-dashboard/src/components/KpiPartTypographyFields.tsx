import type { ReactNode } from "react";
import {
  Bold,
  Italic,
  Strikethrough,
  Underline,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
} from "lucide-react";
import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  COMUNICADO_TEXT_SHADOW_PRESETS,
  KPI_PART_FONT_SIZE_DEFAULTS,
  buildTextDecoration,
  parseTextDecorationFlags,
  resolveKpiPartFontSize,
  resolveTextShadowPresetId,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartStyle,
  type ComunicadoTextDecoration,
  type KpiTextPartKind,
} from "@delpi/tv-dashboard-presentation";

import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";

type TypographyPatch = {
  fontSize?: number;
  fontWeight?: string;
  fontStyle?: string;
  color?: string;
  textDecoration?: string;
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  textAlign?: "left" | "center" | "right" | "justify";
};

type Props = {
  partKind: Extract<ComunicadoKpiPartRef["kind"], "title" | "value" | "hint">;
  style: ComunicadoKpiPartStyle | undefined;
  contrastBackground: string;
  colorLabel: string;
  onPatch: (patch: TypographyPatch) => void;
};

function ToggleBtn({
  label,
  active,
  onClick,
  children,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      className={`td-btn td-btn--sm${active ? " td-btn--active" : ""}`}
      aria-pressed={active}
      aria-label={label}
      title={label}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

/**
 * Tipografia da parte KPI no sidebar — espelho compacto da ribbon Fonte / Efeitos / Parágrafo.
 */
export function KpiPartTypographyFields({
  partKind,
  style,
  contrastBackground,
  colorLabel,
  onPatch,
}: Props) {
  const fontSize = resolveKpiPartFontSize(partKind as KpiTextPartKind, style);
  const deco = parseTextDecorationFlags(style?.textDecoration as ComunicadoTextDecoration | undefined);
  const bold = style?.fontWeight === "bold" || style?.fontWeight === "700";
  const italic = style?.fontStyle === "italic";
  const shadowPreset = resolveTextShadowPresetId(style?.textShadow);
  const textAlign = style?.textAlign ?? "left";
  const partLabel =
    partKind === "value" ? "Valor" : partKind === "title" ? "Título" : "Subtítulo";

  return (
    <div className="td-kpi-part-typography">
      <p className="td-deck-inspector__hint">Fonte · {partLabel}</p>
      <div className="td-part-inspector-toolbar__fields-row">
        <DeckField id={`td-kpi-typo-${partKind}-size`} label="Tamanho">
          <NativeTextControl
            id={`td-kpi-typo-${partKind}-size`}
            type="number"
            min={8}
            value={fontSize}
            onChange={(value) => {
              const next = Number(value);
              if (!Number.isFinite(next)) return;
              onPatch({
                fontSize: Math.max(8, Math.round(next)),
              });
            }}
            placeholder={String(KPI_PART_FONT_SIZE_DEFAULTS[partKind])}
          />
        </DeckField>
        <DeckField id={`td-kpi-typo-${partKind}-color`} label={colorLabel}>
          <TvRibbonColorPicker
            inline
            variant="text"
            contrastBackground={contrastBackground}
            label={colorLabel}
            value={style?.color ?? ""}
            onChange={(color) => onPatch({ color })}
          />
        </DeckField>
      </div>
      <div className="td-kpi-part-typography__toggles" role="group" aria-label="Estilo tipográfico">
        <ToggleBtn
          label="Negrito"
          active={bold}
          onClick={() => onPatch({ fontWeight: bold ? "normal" : "bold" })}
        >
          <Bold size={14} aria-hidden />
        </ToggleBtn>
        <ToggleBtn
          label="Itálico"
          active={italic}
          onClick={() => onPatch({ fontStyle: italic ? "normal" : "italic" })}
        >
          <Italic size={14} aria-hidden />
        </ToggleBtn>
        <ToggleBtn
          label="Sublinhado"
          active={deco.underline}
          onClick={() =>
            onPatch({
              textDecoration: buildTextDecoration(!deco.underline, deco.strikethrough),
            })
          }
        >
          <Underline size={14} aria-hidden />
        </ToggleBtn>
        <ToggleBtn
          label="Tachado"
          active={deco.strikethrough}
          onClick={() =>
            onPatch({
              textDecoration: buildTextDecoration(deco.underline, !deco.strikethrough),
            })
          }
        >
          <Strikethrough size={14} aria-hidden />
        </ToggleBtn>
      </div>

      <p className="td-deck-inspector__hint">Efeitos tipográficos</p>
      <DeckField id={`td-kpi-typo-${partKind}-shadow`} label="Sombra do texto">
        <FormSelectControl
          id={`td-kpi-typo-${partKind}-shadow`}
          ariaLabel="Sombra do texto"
          value={shadowPreset}
          onChange={(value) => {
            const preset = COMUNICADO_TEXT_SHADOW_PRESETS.find((item) => item.id === value);
            onPatch({ textShadow: preset?.value ?? "none" });
          }}
          options={COMUNICADO_TEXT_SHADOW_PRESETS.map((preset) => ({
            value: preset.id,
            label: preset.label,
          }))}
        />
      </DeckField>
      <div className="td-part-inspector-toolbar__fields-row">
        <DeckField id={`td-kpi-typo-${partKind}-stroke`} label="Contorno do texto">
          <TvRibbonColorPicker
            inline
            variant="outline"
            label="Contorno do texto"
            value={style?.textStrokeColor ?? "transparent"}
            onChange={(color) =>
              onPatch({
                textStrokeColor: color,
                textStrokeWidth:
                  style?.textStrokeWidth && style.textStrokeWidth > 0 ? style.textStrokeWidth : 1,
              })
            }
            onNoFill={() => onPatch({ textStrokeColor: "transparent", textStrokeWidth: 0 })}
          />
        </DeckField>
        <DeckField id={`td-kpi-typo-${partKind}-stroke-w`} label="Espessura">
          <NativeTextControl
            id={`td-kpi-typo-${partKind}-stroke-w`}
            type="number"
            min={0}
            max={8}
            step={0.5}
            value={style?.textStrokeWidth ?? 0}
            onChange={(value) => onPatch({ textStrokeWidth: Math.max(0, Number(value) || 0) })}
          />
        </DeckField>
      </div>

      <p className="td-deck-inspector__hint">Parágrafo</p>
      <div className="td-kpi-part-typography__toggles" role="group" aria-label="Alinhamento">
        {(
          [
            ["left", AlignLeft, "Esquerda"],
            ["center", AlignCenter, "Centro"],
            ["right", AlignRight, "Direita"],
            ["justify", AlignJustify, "Justificado"],
          ] as const
        ).map(([align, Icon, label]) => (
          <ToggleBtn
            key={align}
            label={label}
            active={textAlign === align}
            onClick={() => onPatch({ textAlign: align })}
          >
            <Icon size={14} aria-hidden />
          </ToggleBtn>
        ))}
      </div>
    </div>
  );
}
