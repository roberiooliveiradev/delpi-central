import { BetweenVerticalStart } from "lucide-react";
import { useId, useRef, useState } from "react";
import {
  COMUNICADO_LINE_HEIGHT_OPTIONS,
  COMUNICADO_NAMED_TEXT_STYLE_OPTIONS,
  type ComunicadoNamedTextStyle,
} from "@delpi/tv-dashboard-presentation";
import { AnchoredPanelPortal, FieldLabel, HintAction, NativeTextControl } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { TdRibbonSelect } from "../tdRibbonUi";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Props = {
  namedStyleValue: ComunicadoNamedTextStyle;
  lineHeight: number;
  letterSpacing: number;
  onNamedStyle: (value: ComunicadoNamedTextStyle) => void;
  onLineHeight: (value: number) => void;
  onLetterSpacing: (value: number) => void;
  /** Estilo nomeado (Título/Normal) — só em texto/título rico. */
  showNamedStyle?: boolean;
  /**
   * `popover` — tile + painel ancorado (ribbon).
   * `inline` — campos embutidos (sidebar).
   */
  variant?: "popover" | "inline";
};

type PanelProps = Omit<Props, "variant"> & { idPrefix: string };

function ParagraphSpacingPanel({
  namedStyleValue,
  lineHeight,
  letterSpacing,
  onNamedStyle,
  onLineHeight,
  onLetterSpacing,
  showNamedStyle = true,
  idPrefix,
}: PanelProps) {
  const styleId = `${idPrefix}-named-style`;
  const lineId = `${idPrefix}-line-height`;
  const spaceId = `${idPrefix}-letter-spacing`;

  return (
    <div
      className="td-paragraph-spacing-panel"
      role="group"
      aria-label="Estilo e espaçamento do parágrafo"
    >
      {showNamedStyle ? (
        <span className="td-deck-ribbon__stack-field">
          <FieldLabel
            htmlFor={styleId}
            label="Estilo"
            hint={H.namedStyle}
            className="td-deck-ribbon__field-label"
          />
          <TdRibbonSelect
            id={styleId}
            className="td-deck-ribbon__select td-deck-ribbon__select--style"
            aria-label="Estilo de parágrafo"
            value={namedStyleValue}
            onChange={(value) => onNamedStyle(value as ComunicadoNamedTextStyle)}
            options={COMUNICADO_NAMED_TEXT_STYLE_OPTIONS.map((option) => ({
              value: option.key,
              label: option.label,
            }))}
          />
        </span>
      ) : null}
      <span className="td-deck-ribbon__stack-field">
        <FieldLabel
          htmlFor={lineId}
          label="Entrelinhas"
          hint={H.lineHeight}
          className="td-deck-ribbon__field-label"
        />
        <TdRibbonSelect
          id={lineId}
          className="td-deck-ribbon__select td-deck-ribbon__select--compact"
          aria-label="Entrelinhas"
          value={String(lineHeight)}
          onChange={(value) => onLineHeight(Number(value))}
          options={COMUNICADO_LINE_HEIGHT_OPTIONS.map((value) => ({
            value: String(value),
            label: value === 1 ? "Simples" : value === 1.15 ? "1,15" : String(value),
          }))}
        />
      </span>
      <span className="td-deck-ribbon__stack-field">
        <FieldLabel
          htmlFor={spaceId}
          label="Espaçamento"
          hint={H.letterSpacing}
          className="td-deck-ribbon__field-label"
        />
        <NativeTextControl
          id={spaceId}
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          aria-label="Espaçamento entre caracteres (px)"
          min={-2}
          max={24}
          step={0.5}
          value={letterSpacing}
          onChange={(value) => onLetterSpacing(Number(value) || 0)}
        />
      </span>
    </div>
  );
}

/**
 * Ribbon: tile «Estilo» + Estilo/Entrelinhas/Espaçamento no popover.
 * Sidebar (`inline`): mesmos campos embutidos.
 */
export function ParagraphSpacingMenu({
  namedStyleValue,
  lineHeight,
  letterSpacing,
  onNamedStyle,
  onLineHeight,
  onLetterSpacing,
  showNamedStyle = true,
  variant = "popover",
}: Props) {
  const [open, setOpen] = useState(false);
  const reactId = useId().replace(/:/g, "");
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const panelProps: PanelProps = {
    namedStyleValue,
    lineHeight,
    letterSpacing,
    onNamedStyle,
    onLineHeight,
    onLetterSpacing,
    showNamedStyle,
    idPrefix: variant === "inline" ? `td-pane-ps-${reactId}` : `td-pop-ps-${reactId}`,
  };

  if (variant === "inline") {
    return <ParagraphSpacingPanel {...panelProps} />;
  }

  return (
    <div
      ref={rootRef}
      className="td-paragraph-spacing-entry delpi-ui-shape-menu td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus"
    >
      <HintAction hint={H.paragraphSpacing} ariaLabel="Ajuda: Estilo e espaçamento">
        <button
          type="button"
          className={[
            "delpi-ui-shape-menu__trigger",
            open ? "td-paragraph-spacing-entry__trigger--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          aria-label="Estilo e espaçamento do parágrafo"
          aria-haspopup="dialog"
          aria-expanded={open}
          onClick={() => setOpen((prev) => !prev)}
        >
          <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
            <BetweenVerticalStart size={18} />
          </span>
          <span className="delpi-ui-shape-menu__trigger-label">Estilo</span>
        </button>
      </HintAction>

      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-paragraph-spacing-popover"
          role="dialog"
          aria-label="Estilo e espaçamento do parágrafo"
          preferredPlacement="bottom"
          density="compact"
          onDismiss={() => setOpen(false)}
        >
          <ParagraphSpacingPanel {...panelProps} />
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
