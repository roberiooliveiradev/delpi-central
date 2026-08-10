import { ChevronDown, Maximize2 } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import {
  bumpDisplayFormatDecimalPlaces,
  displayFormatTriggerLabel,
  isNumericDisplayCategory,
  togglePercentDisplayFormat,
  toggleThousandsDisplayFormat,
  type DisplayFormatSpec,
  type DisplayFormatTarget,
} from "../../displayFormat";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { DisplayFormatDialog } from "./DisplayFormatDialog";
import { DisplayFormatMenu } from "./DisplayFormatMenu";
import { DisplayFormatTargetHint } from "./DisplayFormatTargetHint";
import { DEFAULT_DISPLAY_FORMAT_CN } from "./displayFormatClasses";

export type DisplayFormatRibbonGroupProps = {
  spec: DisplayFormatSpec;
  onChange: (spec: DisplayFormatSpec) => void;
  target: DisplayFormatTarget;
  sampleValue?: unknown;
  density?: "ribbon" | "compact";
  portalScopeClassName?: string;
};

export function DisplayFormatRibbonGroup({
  spec,
  onChange,
  target,
  sampleValue,
  density = "ribbon",
  portalScopeClassName,
}: DisplayFormatRibbonGroupProps) {
  const cn = DEFAULT_DISPLAY_FORMAT_CN;
  const [menuOpen, setMenuOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const numeric = isNumericDisplayCategory(spec.category);
  /* Eixo X (categoria): % ainda aplica nos valores via displayFormatSelection. */
  const percentShortcutEnabled = numeric || target === "chartCategory";

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  return (
    <div
      ref={rootRef}
      className={[cn.group, density === "compact" ? cn.groupCompact : ""].filter(Boolean).join(" ")}
    >
      <DisplayFormatTargetHint target={target} />
      <button
        type="button"
        className={cn.trigger}
        aria-haspopup="listbox"
        aria-expanded={menuOpen}
        aria-controls={menuId}
        onClick={() => setMenuOpen((open) => !open)}
      >
        <span>{displayFormatTriggerLabel(spec)}</span>
        <ChevronDown size={14} aria-hidden />
      </button>
      {menuOpen ? (
        <AnchoredPanelPortal
          open
          anchorRef={rootRef}
          panelRef={panelRef}
          variant="bare"
          density="compact"
          matchAnchorWidth
          portalScopeClassName={portalScopeClassName}
          onDismiss={() => setMenuOpen(false)}
          aria-label="Categorias de formato"
        >
          <div id={menuId} ref={panelRef}>
            <DisplayFormatMenu
              spec={spec}
              onSelect={(next) => {
                onChange(next);
                setMenuOpen(false);
              }}
              onMore={() => {
                setMenuOpen(false);
                setDialogOpen(true);
              }}
            />
          </div>
        </AnchoredPanelPortal>
      ) : null}
      <div className={cn.shortcuts}>
        <button
          type="button"
          className={cn.shortcut}
          disabled={!percentShortcutEnabled}
          title="Porcentagem"
          aria-label="Porcentagem"
          onClick={() => onChange(togglePercentDisplayFormat(spec))}
        >
          %
        </button>
        <button
          type="button"
          className={cn.shortcut}
          disabled={!numeric}
          title="Separador de milhar"
          aria-label="Separador de milhar"
          onClick={() => onChange(toggleThousandsDisplayFormat(spec))}
        >
          000
        </button>
        <button
          type="button"
          className={cn.shortcut}
          disabled={!numeric}
          title="Diminuir casas decimais"
          aria-label="Diminuir casas decimais"
          onClick={() => onChange(bumpDisplayFormatDecimalPlaces(spec, -1))}
        >
          .0←
        </button>
        <button
          type="button"
          className={cn.shortcut}
          disabled={!numeric}
          title="Aumentar casas decimais"
          aria-label="Aumentar casas decimais"
          onClick={() => onChange(bumpDisplayFormatDecimalPlaces(spec, 1))}
        >
          .0→
        </button>
        <button
          type="button"
          className={cn.launcher}
          title="Mais formatos"
          aria-label="Mais formatos de número"
          onClick={() => setDialogOpen(true)}
        >
          <Maximize2 size={14} aria-hidden />
        </button>
      </div>
      <DisplayFormatDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        spec={spec}
        onApply={onChange}
        sampleValue={sampleValue}
        target={target}
        portalScopeClassName={portalScopeClassName}
      />
    </div>
  );
}
