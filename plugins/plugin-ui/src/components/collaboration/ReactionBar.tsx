import { Plus } from "lucide-react";
import { useRef, useState } from "react";

import {
  EMOJI_CATALOG,
  type EmojiCatalogItem,
} from "../../content/emojiCatalog";
import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  EmojiInsertMenu,
  emojiInsertMenuBemClasses,
  type EmojiInsertMenuClassNames,
} from "./EmojiInsertMenu";

export type ReactionBarItem = {
  code: string;
  label: string;
  count: number;
  reactedByMe?: boolean;
};

export type ReactionBarClassNames = {
  root: string;
  chip: string;
  chipActive: string;
  count: string;
  add: string;
  emojiMenu: EmojiInsertMenuClassNames;
};

export type ReactionBarProps = {
  items: readonly ReactionBarItem[];
  classNames: ReactionBarClassNames;
  /**
   * @deprecated Prefer `emojiAdd` («+» + EmojiInsertMenu). Kept for simple catalogs.
   */
  availableCodes?: readonly { code: string; label: string }[];
  onToggle?: (code: string) => void;
  onAdd?: (code: string) => void;
  addAriaLabel?: string;
  listAriaLabel: string;
  /** Opens curated emoji grid from «+» (Sala / collaboration). */
  emojiAdd?: {
    listAriaLabel: string;
    items?: readonly EmojiCatalogItem[];
    /** Default: emoji `id` as reaction code. */
    codeForItem?: (item: EmojiCatalogItem) => string;
    portalScopeClassName?: string;
  };
  className?: string;
};

export function reactionBarBemClasses(prefix: string): ReactionBarClassNames {
  const base = `${prefix}-reaction-bar`;
  const ui = "delpi-ui-reaction-bar";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    chip: pair(`${base}__chip`, `${ui}__chip`),
    chipActive: pair(
      `${base}__chip ${base}__chip--active`,
      `${ui}__chip ${ui}__chip--active`,
    ),
    count: pair(`${base}__count`, `${ui}__count`),
    add: pair(`${base}__add`, `${ui}__add`),
    emojiMenu: emojiInsertMenuBemClasses(prefix),
  };
}

/**
 * Reaction chips. Codes and labels come from the host catalog.
 * «+» opens EmojiInsertMenu when `emojiAdd` is set.
 */
export function ReactionBar({
  items,
  classNames,
  availableCodes = [],
  onToggle,
  onAdd,
  addAriaLabel,
  listAriaLabel,
  emojiAdd,
  className,
}: ReactionBarProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const addAnchorRef = useRef<HTMLButtonElement>(null);
  const [emojiOpen, setEmojiOpen] = useState(false);
  const unused = availableCodes.filter(
    (opt) => !items.some((item) => item.code === opt.code),
  );
  const useEmojiMenu = Boolean(emojiAdd && onAdd && addAriaLabel);

  return (
    <div className={rootClass} role="group" aria-label={listAriaLabel}>
      {items.map((item) => (
        <button
          key={item.code}
          type="button"
          className={item.reactedByMe ? classNames.chipActive : classNames.chip}
          aria-pressed={Boolean(item.reactedByMe)}
          aria-label={item.label}
          disabled={!onToggle}
          onClick={() => onToggle?.(item.code)}
        >
          <span>{item.label}</span>
          {item.count > 0 ? (
            <span className={classNames.count}>{item.count}</span>
          ) : null}
        </button>
      ))}
      {useEmojiMenu ? (
        <>
          <button
            ref={addAnchorRef}
            type="button"
            className={classNames.add}
            aria-label={addAriaLabel}
            aria-expanded={emojiOpen}
            onClick={() => setEmojiOpen((open) => !open)}
          >
            <Plus size={14} aria-hidden />
          </button>
          <EmojiInsertMenu
            open={emojiOpen}
            onOpenChange={setEmojiOpen}
            anchorRef={addAnchorRef}
            classNames={classNames.emojiMenu}
            listAriaLabel={emojiAdd!.listAriaLabel}
            items={emojiAdd!.items ?? EMOJI_CATALOG}
            portalScopeClassName={emojiAdd!.portalScopeClassName}
            onSelect={(item) => {
              const code = (emojiAdd!.codeForItem?.(item) ?? item.id).trim();
              if (code) onAdd?.(code);
              setEmojiOpen(false);
            }}
          />
        </>
      ) : onAdd && unused.length > 0 && addAriaLabel ? (
        unused.map((opt) => (
          <button
            key={`add-${opt.code}`}
            type="button"
            className={classNames.add}
            aria-label={`${addAriaLabel}: ${opt.label}`}
            onClick={() => onAdd(opt.code)}
          >
            {opt.label}
          </button>
        ))
      ) : null}
    </div>
  );
}

export type DashboardReactionBarProps = Omit<ReactionBarProps, "classNames">;

export function createDashboardReactionBar(prefix: string) {
  const classNames = reactionBarBemClasses(prefix);
  return function DashboardReactionBar(props: DashboardReactionBarProps) {
    return <ReactionBar classNames={classNames} {...props} />;
  };
}
