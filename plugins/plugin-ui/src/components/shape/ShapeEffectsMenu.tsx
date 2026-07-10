import { ChevronRight, Sparkles } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { AnchoredPanelPortal } from "./AnchoredPanelPortal";

import { mergeShapeColorLabels } from "./shapeLabels";
import type { ShapeColorLabels } from "./types";
import { useClickOutside } from "./useClickOutside";

export type ShapeEffectItem = {
  id: string;
  label: string;
  options?: { id: string; label: string }[];
};

export type ShapeEffectsMenuProps = {
  items?: ShapeEffectItem[];
  onSelect?: (effectId: string, optionId?: string) => void;
  labels?: ShapeColorLabels;
};

const DEFAULT_EFFECT_KEYS = [
  "preset",
  "shadow",
  "reflection",
  "glow",
  "softEdges",
  "bevel",
  "rotation3d",
] as const satisfies readonly (keyof ShapeColorLabels)[];

function defaultEffectItems(L: ReturnType<typeof mergeShapeColorLabels>): ShapeEffectItem[] {
  return DEFAULT_EFFECT_KEYS.map((key) => ({ id: key, label: L[key] }));
}

export function ShapeEffectsMenu({ items, onSelect, labels }: ShapeEffectsMenuProps) {
  const L = mergeShapeColorLabels(labels);
  const resolvedItems = items ?? defaultEffectItems(L);
  const [open, setOpen] = useState(false);
  const [activeSubmenu, setActiveSubmenu] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => {
    setOpen(false);
    setActiveSubmenu(null);
  });

  return (
    <div className="delpi-ui-shape-menu" ref={rootRef}>
      <button
        type="button"
        className="delpi-ui-shape-menu__trigger"
        aria-label={L.effects}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
          <Sparkles size={18} />
        </span>
        <span className="delpi-ui-shape-menu__trigger-label">{L.effects}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          className="delpi-ui-shape-menu__panel--narrow"
          role="menu"
        >
          <ul className="delpi-ui-shape-effects__list">
            {resolvedItems.map((item) => (
              <EffectRow
                key={item.id}
                item={item}
                open={activeSubmenu === item.id}
                onToggle={() => setActiveSubmenu((prev) => (prev === item.id ? null : item.id))}
                onSelect={(optionId) => {
                  onSelect?.(item.id, optionId);
                  setOpen(false);
                  setActiveSubmenu(null);
                }}
              />
            ))}
          </ul>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

function EffectRow({
  item,
  open,
  onToggle,
  onSelect,
}: {
  item: ShapeEffectItem;
  open: boolean;
  onToggle: () => void;
  onSelect: (optionId?: string) => void;
}) {
  const hasOptions = item.options && item.options.length > 0;

  return (
    <li className="delpi-ui-shape-effects__item">
      <button
        type="button"
        className="delpi-ui-shape-effects__toggle"
        onClick={() => {
          if (hasOptions) {
            onToggle();
            return;
          }
          onSelect();
        }}
      >
        {item.label}
        {hasOptions ? <ChevronRight size={14} aria-hidden="true" /> : null}
      </button>
      {open && hasOptions ? (
        <ul className="delpi-ui-shape-effects__options">
          {item.options!.map((option) => (
            <li key={option.id}>
              <button type="button" className="delpi-ui-shape-effects__option" onClick={() => onSelect(option.id)}>
                {option.label}
              </button>
            </li>
          ))}
        </ul>
      ) : open && !hasOptions ? (
        <PlaceholderPanel>{item.label}</PlaceholderPanel>
      ) : null}
    </li>
  );
}

function PlaceholderPanel({ children }: { children: ReactNode }) {
  return <div className="delpi-ui-shape-effects__placeholder">{children}</div>;
}
