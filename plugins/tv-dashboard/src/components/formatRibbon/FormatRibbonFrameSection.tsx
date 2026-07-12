import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  isPointShapeKind,
  type ComunicadoBlock,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { useComunicadoEditor } from "../comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

const SIZE_KEYS = ["w", "h"] as const;
const POSITION_KEYS = ["x", "y"] as const;

const FRAME_LABELS: Record<"x" | "y" | "w" | "h", string> = {
  x: "X %",
  y: "Y %",
  w: "Larg. %",
  h: "Alt. %",
};

function formatFrameValue(value: number): number {
  return Number((Number.isFinite(value) ? value : 0).toFixed(1));
}

/** Ajusta eixo do frame mantendo o bloco dentro do palco (0–100%). */
export function patchComunicadoFrame(
  frame: ComunicadoFrame,
  key: keyof ComunicadoFrame,
  raw: number,
): ComunicadoFrame {
  const value = Number.isFinite(raw) ? raw : frame[key];
  if (key === "w" || key === "h") {
    const size = Math.max(0.5, Math.min(100, value));
    const next = { ...frame, [key]: size };
    if (key === "w") {
      next.x = Math.max(0, Math.min(100 - size, frame.x));
    } else {
      next.y = Math.max(0, Math.min(100 - size, frame.y));
    }
    return next;
  }
  const max = key === "x" ? 100 - frame.w : 100 - frame.h;
  return { ...frame, [key]: Math.max(0, Math.min(max, value)) };
}

/**
 * Posição / tamanho / rotação do bloco no palco — faixa Forma (qualquer tipo).
 * Espelha «Posição e tamanho» do inspetor, para edição rápida na top bar.
 */
export function FormatRibbonFrameSection() {
  const { selected, selectedIds, updateSelected, updateSelectedStyle } = useComunicadoEditor();

  if (!selected || selectedIds.length > 1) return null;

  const pointOnly =
    selected.type === "shape" && isPointShapeKind(selected.shape);
  const frameKeys = pointOnly
    ? POSITION_KEYS
    : ([...POSITION_KEYS, ...SIZE_KEYS] as const);

  const setFrameKey = (key: "x" | "y" | "w" | "h", raw: number) => {
    updateSelected({
      frame: patchComunicadoFrame(selected.frame, key, raw),
    } as Partial<ComunicadoBlock>);
  };

  return (
    <DeckRibbonGroup label="Posição e tamanho" hint={E.position ?? H.shapeSize} wide>
      <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
        {frameKeys.map((key) => (
          <span key={key} className="td-deck-ribbon__frame-field">
            <label className="td-deck-ribbon__field-label" htmlFor={`td-ribbon-frame-${key}`}>
              {FRAME_LABELS[key]}
            </label>
            <NativeTextControl
              id={`td-ribbon-frame-${key}`}
              type="number"
              className="td-deck-ribbon__number td-deck-ribbon__number--compact"
              min={key === "w" || key === "h" ? 0.5 : 0}
              max={100}
              step={0.5}
              aria-label={FRAME_LABELS[key]}
              value={formatFrameValue(selected.frame[key])}
              onChange={(value) => setFrameKey(key, Number(value))}
            />
          </span>
        ))}
        <span className="td-deck-ribbon__frame-field">
          <label className="td-deck-ribbon__field-label" htmlFor="td-ribbon-frame-rotation">
            Rot. °
          </label>
          <NativeTextControl
            id="td-ribbon-frame-rotation"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={-180}
            max={180}
            step={1}
            aria-label="Rotação em graus"
            value={selected.style?.rotation ?? 0}
            onChange={(value) =>
              updateSelectedStyle({
                rotation: Math.max(-180, Math.min(180, Number(value) || 0)),
              })
            }
          />
        </span>
      </div>
    </DeckRibbonGroup>
  );
}
