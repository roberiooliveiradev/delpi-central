import { ALargeSmall, Droplet, Image, Palette, Pipette } from "lucide-react";
import { useRef, useState } from "react";

import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import { DELPI_STANDARD_COLORS, DELPI_THEME_COLOR_GRID } from "./colorPalettes";
import { ColorDialog } from "./ColorDialog";
import { ColorStandardRow, ColorThemeGrid } from "./ColorThemeGrid";
import { cssToColorValue, resolveAutomaticTextColor, AUTOMATIC_TEXT_COLOR } from "./colorUtils";
import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";
import { useClickOutside } from "./useClickOutside";

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
  onEyedropper?: () => void;
  labels?: ShapeColorLabels;
  themeRows?: readonly (readonly string[])[];
  standardColors?: readonly string[];
  /** Cores usadas recentemente (histórico de sessão do host). */
  recentColors?: readonly string[];
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
  className,
}: ColorPickerPopoverProps) {
  const L = mergeShapeColorLabels(labels);
  const [dialogOpen, setDialogOpen] = useState(false);

  const noFillEnabled = resolveNoFillEnabled(variant, showNoFill);
  const automaticEnabled = resolveAutomaticEnabled(variant, showAutomatic);
  const recent =
    recentColors?.filter(
      (color) => typeof color === "string" && color.trim() && color !== "transparent" && color !== "auto",
    ) ?? [];

  const handleNoFill = () => {
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
  };

  return (
    <div className={["delpi-ui-color-picker", className].filter(Boolean).join(" ")}>
      {automaticEnabled || noFillEnabled ? (
        <ul className="delpi-ui-color-picker__actions delpi-ui-color-picker__actions--leading">
          {automaticEnabled ? (
            <li>
              <button
                type="button"
                className="delpi-ui-color-picker__action"
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
              <button type="button" className="delpi-ui-color-picker__action" onClick={handleNoFill}>
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
          <button type="button" className="delpi-ui-color-picker__action" onClick={() => setDialogOpen(true)}>
            <Palette size={16} aria-hidden="true" />
            {L.moreColors}
          </button>
        </li>
        {onEyedropper ? (
          <li>
            <button type="button" className="delpi-ui-color-picker__action" onClick={onEyedropper}>
              <Pipette size={16} aria-hidden="true" />
              {L.eyedropper}
            </button>
          </li>
        ) : null}
      </ul>

      <ColorDialog
        open={dialogOpen}
        value={value}
        onClose={() => setDialogOpen(false)}
        onConfirm={handleSelect}
        labels={labels}
      />
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
  ...popoverProps
}: ColorPickerPopoverTriggerProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => {
    setOpen(false);
    onClose?.();
  });

  const previewColor = value && cssToColorValue(value).alpha > 0 ? value : "transparent";

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
          className={["delpi-ui-color-picker-trigger__preview", previewClassName].filter(Boolean).join(" ")}
          style={{ background: previewColor === "transparent" ? undefined : previewColor }}
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
        >
          <ColorPickerPopover
            {...popoverProps}
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
}: ShapeFillMenuProps) {
  const L = mergeShapeColorLabels(labels);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => setOpen(false));

  const previewColor = value && cssToColorValue(value).alpha > 0 ? value : "transparent";

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
            className="delpi-ui-shape-menu__trigger-swatch"
            style={{ background: previewColor === "transparent" ? undefined : previewColor }}
          />
        </span>
        <span className="delpi-ui-shape-menu__trigger-label">{fillLabel ?? L.fill}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal open={open} anchorRef={rootRef} panelRef={panelRef} role="menu">
          <ColorPickerPopover
            variant="fill"
            value={value}
            onChange={(color) => {
              onChange(color);
            }}
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
