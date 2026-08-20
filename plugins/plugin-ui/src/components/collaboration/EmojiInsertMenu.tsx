import { useRef, type RefObject } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  EMOJI_CATALOG,
  type EmojiCatalogItem,
} from "../../content/emojiCatalog";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";

export type EmojiInsertMenuClassNames = {
  panel: string;
  grid: string;
  option: string;
};

export type EmojiInsertMenuProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  anchorRef: RefObject<HTMLElement | null>;
  onSelect: (item: EmojiCatalogItem) => void;
  classNames: EmojiInsertMenuClassNames;
  /** Nome acessível do painel (host). */
  listAriaLabel: string;
  items?: readonly EmojiCatalogItem[];
  portalScopeClassName?: string;
};

export function emojiInsertMenuBemClasses(prefix: string): EmojiInsertMenuClassNames {
  const base = `${prefix}-emoji-insert-menu`;
  const ui = "delpi-ui-emoji-insert-menu";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    panel: pair(base, ui),
    grid: pair(`${base}__grid`, `${ui}__grid`),
    option: pair(`${base}__option`, `${ui}__option`),
  };
}

/**
 * Grade curada de emoji para o Formatar do MentionComposer (e «+» de reações).
 * Catálogo JSON no kit — sem emoji-mart / GIF.
 */
export function EmojiInsertMenu({
  open,
  onOpenChange,
  anchorRef,
  onSelect,
  classNames,
  listAriaLabel,
  items = EMOJI_CATALOG,
  portalScopeClassName,
}: EmojiInsertMenuProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  if (!open) return null;

  const dismiss = () => onOpenChange(false);

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      density="compact"
      preferredPlacement="top"
      portalScopeClassName={portalScopeClassName}
      className={classNames.panel}
      role="dialog"
      aria-label={listAriaLabel}
      onDismiss={dismiss}
    >
      <div className={classNames.grid} role="listbox" aria-label={listAriaLabel}>
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            role="option"
            className={classNames.option}
            aria-label={item.label}
            title={item.label}
            onMouseDown={(event) => {
              event.preventDefault();
              onSelect(item);
              dismiss();
            }}
          >
            <span aria-hidden="true">{item.glyph}</span>
          </button>
        ))}
      </div>
    </AnchoredPanelPortal>
  );
}

export type DashboardEmojiInsertMenuProps = Omit<EmojiInsertMenuProps, "classNames">;

export function createDashboardEmojiInsertMenu(prefix: string) {
  const classNames = emojiInsertMenuBemClasses(prefix);
  return function DashboardEmojiInsertMenu(props: DashboardEmojiInsertMenuProps) {
    return <EmojiInsertMenu classNames={classNames} {...props} />;
  };
}
