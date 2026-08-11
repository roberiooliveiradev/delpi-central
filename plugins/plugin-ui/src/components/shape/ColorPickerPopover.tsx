import { ALargeSmall, Droplet, Image, Palette, Pipette } from "lucide-react";
import { useRef, useState } from "react";

import { useRibbonSectionPopoverSurface } from "../ribbon/RibbonGroupSurfaceContext";
import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import { DELPI_STANDARD_COLORS, DELPI_THEME_COLOR_GRID } from "./colorPalettes";
import { ColorMorePanel } from "./ColorMorePanel";
import { ColorStandardRow, ColorThemeGrid } from "./ColorThemeGrid";
import { resolveAutomaticTextColor, AUTOMATIC_TEXT_COLOR, isAutomaticTextColor, isTransparentCssColor, resolveColorTriggerPreviewMode } from "./colorUtils";
import { FillGradientPanel } from "./FillGradientPanel";
import {
  fillToCssBackground,
  normalizeGradientStops,
  solidFromFill,
  type DelpiFill,
  type DelpiFillKind,
} from "./fillTypes";
import { isEyedropperSupported, pickColorWithEyedropper } from "./pickColorWithEyedropper";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";

/** Perfil do seletor: fill/outline sempre oferecem «sem…»; text oferece «Automático». */
export type ColorPickerVariant = "default" | "fill" | "outline" | "text";

export type ColorPickerPopoverProps = {
  value?: string;
  onChange: (color: string) => void;
  onNoFill?: () => void;
  noFillLabel?: string;
  showNoFill?: boolean;
  /** Cor de texto Automático — contraste com o fundo informado. */
  showAutomatic?: boolean;
  contrastBackground?: string | null;
  onAutomatic?: (color: "#000000" | "#ffffff") => void;
  automaticLabel?: string;
  /**
   * Atalho de comportamento:
   * - fill → Sem fundo (transparent)
   * - outline → Sem contorno
   * - text → Automático
   */
  variant?: ColorPickerVariant;
  /**
   * Override do conta-gotas. Sem callback, usa EyeDropper nativo quando disponível.
   */
  onEyedropper?: () => void;
  labels?: ShapeColorLabels;
  themeRows?: readonly (readonly string[])[];
  standardColors?: readonly string[];
  /** Cores usadas recentemente (histórico de sessão do host). */
  recentColors?: readonly string[];
  /** Preenchimento rico. Sem `onFillChange` o popover fica só hex (hosts RichText etc.). */
  fill?: DelpiFill;
  onFillChange?: (fill: DelpiFill) => void;
  allowedFillKinds?: readonly DelpiFillKind[];
  className?: string;
};

function resolveNoFillEnabled(
  variant: ColorPickerVariant | undefined,
  showNoFill: boolean | undefined,
): boolean {
  if (showNoFill != null) return showNoFill;
  return variant === "fill" || variant === "outline";
}

function resolveAutomaticEnabled(
  variant: ColorPickerVariant | undefined,
  showAutomatic: boolean | undefined,
): boolean {
  if (showAutomatic != null) return showAutomatic;
  return variant === "text";
}

export function ColorPickerPopover({
  value,
  onChange,
  onNoFill,
  noFillLabel,
  showNoFill,
  showAutomatic,
  contrastBackground,
  onAutomatic,
  automaticLabel,
  variant = "default",
  onEyedropper,
  labels,
  themeRows = DELPI_THEME_COLOR_GRID,
  standardColors = DELPI_STANDARD_COLORS,
  recentColors,
  fill,
  onFillChange,
  allowedFillKinds = ["solid"],
  className,
}: ColorPickerPopoverProps) {
  const L = mergeShapeColorLabels(labels);
  const showGradient = Boolean(onFillChange) && allowedFillKinds.includes("gradient");
  const [mode, setMode] = useState<DelpiFillKind>(
    showGradient && fill?.kind === "gradient" ? "gradient" : "solid",
  );
  const [moreOpen, setMoreOpen] = useState(false);
  const [eyedropperBusy, setEyedropperBusy] = useState(false);
  const moreBtnRef = useRef<HTMLButtonElement>(null);
  const morePanelRef = useRef<HTMLDivElement>(null);

  const noFillEnabled = resolveNoFillEnabled(variant, showNoFill);
  const automaticEnabled = resolveAutomaticEnabled(variant, showAutomatic);
  const eyedropperEnabled = Boolean(onEyedropper) || isEyedropperSupported();
  const noFillSelected = noFillEnabled && isTransparentCssColor(value);
  const automaticSelected = automaticEnabled && isAutomaticTextColor(value);
  const recent =
    recentColors?.filter(
      (color) => typeof color === "string" && color.trim() && color !== "transparent" && color !== "auto",
    ) ?? [];

  const handleNoFill = () => {
    onFillChange?.({ kind: "none" });
    if (onNoFill) {
      onNoFill();
      return;
    }
    onChange("transparent");
  };

  const handleAutomatic = () => {
    // Persiste sentinel — o paint resolve contraste contra o fundo atual.
    if (onAutomatic) {
      onAutomatic(resolveAutomaticTextColor(contrastBackground));
    }
    onChange(AUTOMATIC_TEXT_COLOR);
  };

  const defaultNoFillLabel =
    variant === "outline" ? L.noOutline : L.noFill;

  const handleSelect = (color: string) => {
    onChange(color);
    onFillChange?.({ kind: "solid", color });
  };

  const switchMode = (next: DelpiFillKind) => {
    setMode(next);
    if (!onFillChange) return;
    if (next === "solid") {
      const color = solidFromFill(fill) === "transparent" ? value || "#0f172a" : solidFromFill(fill);
      onFillChange({ kind: "solid", color });
      onChange(color);
      return;
    }
    if (fill?.kind === "gradient") {
      onFillChange(fill);
      return;
    }
    const base = value && value !== "transparent" && value !== "auto" ? value : "#0f172a";
    onFillChange({
      kind: "gradient",
      angle: 180,
      stops: normalizeGradientStops([
        { color: base, position: 0 },
        { color: "#1e3a5f", position: 100 },
      ]),
    });
  };

  const handleEyedropper = async () => {
    if (onEyedropper) {
      onEyedropper();
      return;
    }
    if (eyedropperBusy || !isEyedropperSupported()) return;
    setEyedropperBusy(true);
    try {
      const color = await pickColorWithEyedropper();
      if (color) handleSelect(color);
    } finally {
      setEyedropperBusy(false);
    }
  };

  return (
    <div className={["delpi-ui-color-picker", className].filter(Boolean).join(" ")}>
      {showGradient ? (
        <div className="delpi-ui-fill-mode" role="tablist" aria-label={L.fill}>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "solid"}
            className={[
              "delpi-ui-fill-mode__btn",
              mode === "solid" ? "delpi-ui-fill-mode__btn--active" : null,
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => switchMode("solid")}
          >
            {L.fillSolid}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "gradient"}
            className={[
              "delpi-ui-fill-mode__btn",
              mode === "gradient" ? "delpi-ui-fill-mode__btn--active" : null,
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => switchMode("gradient")}
          >
            {L.fillGradient}
          </button>
        </div>
      ) : null}

      {showGradient && mode === "gradient" ? (
        <FillGradientPanel
          value={
            fill?.kind === "gradient"
              ? fill
              : {
                  kind: "gradient",
                  angle: 180,
                  stops: normalizeGradientStops([
                    { color: value && value !== "transparent" ? value : "#0f172a", position: 0 },
                    { color: "#1e3a5f", position: 100 },
                  ]),
                }
          }
          onChange={(next) => onFillChange?.(next)}
          labels={labels}
          themeRows={themeRows}
          standardColors={standardColors}
        />
      ) : null}

      {!showGradient || mode === "solid" ? (
        <>
      {automaticEnabled || noFillEnabled ? (
        <ul className="delpi-ui-color-picker__actions delpi-ui-color-picker__actions--leading">
          {automaticEnabled ? (
            <li>
              <button
                type="button"
                className={[
                  "delpi-ui-color-picker__action",
                  automaticSelected ? "delpi-ui-color-picker__action--selected" : null,
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-pressed={automaticSelected}
                onClick={handleAutomatic}
              >
                <span
                  className="delpi-ui-color-picker__action-icon delpi-ui-color-picker__action-icon--auto"
                  aria-hidden="true"
                >
                  <ALargeSmall size={12} />
                </span>
                {automaticLabel ?? L.automatic}
              </button>
            </li>
          ) : null}
          {noFillEnabled ? (
            <li>
              <button
                type="button"
                className={[
                  "delpi-ui-color-picker__action",
                  noFillSelected ? "delpi-ui-color-picker__action--selected" : null,
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-pressed={noFillSelected}
                onClick={handleNoFill}
              >
                <span
                  className="delpi-ui-color-picker__action-icon delpi-ui-color-picker__action-icon--none"
                  aria-hidden="true"
                />
                {noFillLabel ?? defaultNoFillLabel}
              </button>
            </li>
          ) : null}
        </ul>
      ) : null}

      {recent.length > 0 ? (
        <section className="delpi-ui-color-picker__section">
          <h4 className="delpi-ui-color-picker__heading">{L.recentColors}</h4>
          <ColorStandardRow
            colors={recent}
            value={value}
            onSelect={handleSelect}
            ariaLabel={L.recentColors}
          />
        </section>
      ) : null}

      <section className="delpi-ui-color-picker__section">
        <h4 className="delpi-ui-color-picker__heading">{L.themeColors}</h4>
        <ColorThemeGrid rows={themeRows} value={value} onSelect={handleSelect} ariaLabel={L.themeColors} />
      </section>

      <section className="delpi-ui-color-picker__section">
        <h4 className="delpi-ui-color-picker__heading">{L.standardColors}</h4>
        <ColorStandardRow
          colors={standardColors}
          value={value}
          onSelect={handleSelect}
          ariaLabel={L.standardColors}
        />
      </section>

      <ul className="delpi-ui-color-picker__actions">
        <li>
          <button
            ref={moreBtnRef}
            type="button"
            className="delpi-ui-color-picker__action"
            aria-expanded={moreOpen}
            aria-haspopup="dialog"
            onClick={() => setMoreOpen((open) => !open)}
          >
            <Palette size={16} aria-hidden="true" />
            {L.moreColors}
          </button>
        </li>
        {eyedropperEnabled ? (
          <li>
            <button
              type="button"
              className="delpi-ui-color-picker__action"
              disabled={eyedropperBusy}
              onClick={() => {
                void handleEyedropper();
              }}
            >
              <Pipette size={16} aria-hidden="true" />
              {L.eyedropper}
            </button>
          </li>
        ) : null}
      </ul>

      {moreOpen ? (
        <AnchoredPanelPortal
          open={moreOpen}
          anchorRef={moreBtnRef}
          panelRef={morePanelRef}
          variant="bare"
          exclusive={false}
          preferredPlacement="right"
          className="delpi-ui-color-more-popover"
          role="dialog"
          aria-label={L.colorDialogTitle}
          onDismiss={() => setMoreOpen(false)}
        >
          <ColorMorePanel
            value={value}
            labels={labels}
            onConfirm={(color) => {
              handleSelect(color);
              setMoreOpen(false);
            }}
            onCancel={() => setMoreOpen(false)}
          />
        </AnchoredPanelPortal>
      ) : null}
        </>
      ) : null}
    </div>
  );
}

export type ColorPickerPopoverTriggerProps = ColorPickerPopoverProps & {
  triggerLabel: string;
  triggerAriaLabel?: string;
  previewClassName?: string;
  /** Classes no root do gatilho (ex.: `--ribbon`, `--inline`) — não confundir com `className` do popover. */
  triggerClassName?: string;
  onClose?: () => void;
};

/** Popover ancorado a um botão-gatilho (uso em ribbon). */
export function ColorPickerPopoverTrigger({
  triggerLabel,
  triggerAriaLabel,
  previewClassName,
  triggerClassName,
  value,
  onChange,
  onClose,
  className,
  variant,
  ...popoverProps
}: ColorPickerPopoverTriggerProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const dismiss = () => {
    setOpen(false);
    onClose?.();
  };

  const previewMode =
    popoverProps.fill?.kind === "gradient" ? "color" : resolveColorTriggerPreviewMode(value, variant);
  const previewBackground =
    popoverProps.fill?.kind === "gradient"
      ? fillToCssBackground(popoverProps.fill)
      : previewMode === "color" && value
        ? value
        : undefined;

  return (
    <div
      className={["delpi-ui-color-picker-trigger", triggerClassName].filter(Boolean).join(" ")}
      ref={rootRef}
    >
      <button
        type="button"
        className="delpi-ui-color-picker-trigger__button"
        aria-label={triggerAriaLabel ?? triggerLabel}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span
          className={[
            "delpi-ui-color-picker-trigger__preview",
            previewMode === "none" ? "delpi-ui-color-picker-trigger__preview--none" : null,
            previewMode === "auto" ? "delpi-ui-color-picker-trigger__preview--auto" : null,
            previewClassName,
          ]
            .filter(Boolean)
            .join(" ")}
          style={previewBackground ? { background: previewBackground } : undefined}
          aria-hidden="true"
        />
        <span className="delpi-ui-color-picker-trigger__label">{triggerLabel}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          className="delpi-ui-color-picker-trigger__panel--portal"
          role="dialog"
          aria-label={triggerLabel}
          exclusive={!inSectionPopover}
          onDismiss={dismiss}
        >
          <ColorPickerPopover
            {...popoverProps}
            variant={variant}
            className={className}
            value={value}
            onChange={(color) => {
              onChange(color);
            }}
          />
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

export type ShapeFillMenuProps = {
  value?: string;
  onChange: (color: string) => void;
  onNoFill?: () => void;
  onImage?: () => void;
  onGradient?: () => void;
  onTexture?: () => void;
  onEyedropper?: () => void;
  labels?: ShapeColorLabels;
  fillLabel?: string;
  fill?: DelpiFill;
  onFillChange?: (fill: DelpiFill) => void;
  allowedFillKinds?: readonly DelpiFillKind[];
};

export function ShapeFillMenu({
  value,
  onChange,
  onNoFill,
  onImage,
  onGradient,
  onTexture,
  onEyedropper,
  labels,
  fillLabel,
  fill,
  onFillChange,
  allowedFillKinds,
}: ShapeFillMenuProps) {
  const L = mergeShapeColorLabels(labels);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const previewMode =
    fill?.kind === "gradient" ? "color" : resolveColorTriggerPreviewMode(value, "fill");
  const previewBackground =
    fill?.kind === "gradient"
      ? fillToCssBackground(fill)
      : previewMode === "color" && value
        ? value
        : undefined;

  return (
    <div className="delpi-ui-shape-menu" ref={rootRef}>
      <button
        type="button"
        className="delpi-ui-shape-menu__trigger"
        aria-label={fillLabel ?? L.fill}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
          <Droplet size={18} />
          <span
            className={[
              "delpi-ui-shape-menu__trigger-swatch",
              previewMode === "none" ? "delpi-ui-shape-menu__trigger-swatch--none" : null,
            ]
              .filter(Boolean)
              .join(" ")}
            style={previewBackground ? { background: previewBackground } : undefined}
          />
        </span>
        <span className="delpi-ui-shape-menu__trigger-label">{fillLabel ?? L.fill}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          role="menu"
          exclusive={!inSectionPopover}
          onDismiss={() => setOpen(false)}
        >
          <ColorPickerPopover
            variant="fill"
            value={value}
            onChange={(color) => {
              onChange(color);
            }}
            fill={fill}
            onFillChange={onFillChange}
            allowedFillKinds={allowedFillKinds}
            onNoFill={
              onNoFill ??
              (() => {
                onChange("transparent");
              })
            }
            onEyedropper={onEyedropper}
            labels={labels}
          />
          <ul className="delpi-ui-shape-menu__extras">
            {onImage ? (
              <li>
                <button type="button" className="delpi-ui-shape-menu__extra" onClick={onImage}>
                  <Image size={16} aria-hidden="true" />
                  {L.image}
                </button>
              </li>
            ) : null}
            {onGradient ? (
              <li>
                <button type="button" className="delpi-ui-shape-menu__extra" onClick={onGradient}>
                  {L.gradient}
                </button>
              </li>
            ) : null}
            {onTexture ? (
              <li>
                <button type="button" className="delpi-ui-shape-menu__extra" onClick={onTexture}>
                  {L.texture}
                </button>
              </li>
            ) : null}
          </ul>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
