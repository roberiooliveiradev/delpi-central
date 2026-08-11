import { ArrowLeftRight } from "lucide-react";
import { useRef, useState } from "react";

import { useRibbonSectionPopoverSurface } from "../ribbon/RibbonGroupSurfaceContext";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";

export type TransitionGalleryOption = {
  id: string;
  label: string;
  description?: string;
  previewStyle?: string;
};

export type TransitionGalleryProps = {
  options: readonly TransitionGalleryOption[];
  value?: string | null;
  onChange: (id: string) => void;
  ariaLabel?: string;
};

export function TransitionGallery({
  options,
  value,
  onChange,
  ariaLabel = "Transições",
}: TransitionGalleryProps) {
  return (
    <div className="delpi-ui-transition-gallery" role="listbox" aria-label={ariaLabel}>
      {options.map((option) => {
        const active = value === option.id;
        const previewStyle = (option.previewStyle ?? option.id) || "none";
        return (
          <button
            key={option.id}
            type="button"
            role="option"
            aria-selected={active}
            className={[
              "delpi-ui-transition-gallery__item",
              active ? "delpi-ui-transition-gallery__item--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onChange(option.id)}
          >
            <span
              className="delpi-ui-transition-gallery__preview"
              data-transition={previewStyle}
              aria-hidden="true"
            >
              <span className="delpi-ui-transition-gallery__frame delpi-ui-transition-gallery__frame--from">
                A
              </span>
              <span className="delpi-ui-transition-gallery__frame delpi-ui-transition-gallery__frame--to">
                B
              </span>
            </span>
            <span className="delpi-ui-transition-gallery__label">{option.label}</span>
            {option.description ? (
              <span className="delpi-ui-transition-gallery__description">{option.description}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

export type TransitionGalleryPopoverProps = TransitionGalleryProps & {
  triggerLabel?: string;
};

export function TransitionGalleryPopover({
  triggerLabel = "Transição",
  ...props
}: TransitionGalleryPopoverProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inSectionPopover = useRibbonSectionPopoverSurface();

  return (
    <div className="delpi-ui-transition-gallery-popover" ref={rootRef}>
      <button
        type="button"
        className="delpi-ui-transition-gallery-popover__trigger"
        aria-label={triggerLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ArrowLeftRight size={18} aria-hidden="true" />
        <span>{triggerLabel}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal
          open
          anchorRef={rootRef}
          panelRef={panelRef}
          role="dialog"
          aria-label={props.ariaLabel ?? triggerLabel}
          density="compact"
          exclusive={!inSectionPopover}
          onDismiss={() => setOpen(false)}
        >
          <TransitionGallery
            {...props}
            onChange={(id) => {
              props.onChange(id);
              setOpen(false);
            }}
          />
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

