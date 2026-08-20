import { Plus } from "lucide-react";
import { useRef, useState } from "react";

import {
  EMOJI_CATALOG,
  QUICK_REACTION_CATALOG,
  type EmojiCatalogItem,
} from "../../content/emojiCatalog";
import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  EmojiInsertMenu,
  emojiInsertMenuBemClasses,
  type EmojiInsertMenuClassNames,
} from "./EmojiInsertMenu";

export type ReactionQuickBarClassNames = {
  root: string;
  quick: string;
  quickActive: string;
  add: string;
  emojiMenu: EmojiInsertMenuClassNames;
};

export type ReactionQuickBarProps = {
  classNames: ReactionQuickBarClassNames;
  listAriaLabel: string;
  addAriaLabel: string;
  emojiMenuAriaLabel: string;
  /** Default: kit `QUICK_REACTION_CATALOG` (5). */
  quickItems?: readonly EmojiCatalogItem[];
  /** Highlight when session user already reacted with that code. */
  activeCodes?: ReadonlySet<string> | readonly string[];
  onPick: (code: string) => void;
  catalogItems?: readonly EmojiCatalogItem[];
  codeForItem?: (item: EmojiCatalogItem) => string;
  portalScopeClassName?: string;
  className?: string;
  disabled?: boolean;
};

export function reactionQuickBarBemClasses(
  prefix: string,
): ReactionQuickBarClassNames {
  const base = `${prefix}-reaction-quick-bar`;
  const ui = "delpi-ui-reaction-quick-bar";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    quick: pair(`${base}__quick`, `${ui}__quick`),
    quickActive: pair(
      `${base}__quick ${base}__quick--active`,
      `${ui}__quick ${ui}__quick--active`,
    ),
    add: pair(`${base}__add`, `${ui}__add`),
    emojiMenu: emojiInsertMenuBemClasses(prefix),
  };
}

function toActiveSet(
  activeCodes: ReactionQuickBarProps["activeCodes"],
): Set<string> {
  if (!activeCodes) return new Set();
  if (activeCodes instanceof Set) return activeCodes;
  return new Set(
    [...activeCodes].map((code) => String(code || "").trim()).filter(Boolean),
  );
}

/**
 * Toolbar compacta: 5 reações rápidas + «+» (EmojiInsertMenu do catálogo).
 * Pensada para a barra de opções do MessageThread (hover).
 */
export function ReactionQuickBar({
  classNames,
  listAriaLabel,
  addAriaLabel,
  emojiMenuAriaLabel,
  quickItems = QUICK_REACTION_CATALOG,
  activeCodes,
  onPick,
  catalogItems = EMOJI_CATALOG,
  codeForItem,
  portalScopeClassName,
  className,
  disabled = false,
}: ReactionQuickBarProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const addAnchorRef = useRef<HTMLButtonElement>(null);
  const [emojiOpen, setEmojiOpen] = useState(false);
  const active = toActiveSet(activeCodes);

  return (
    <div className={rootClass} role="group" aria-label={listAriaLabel}>
      {quickItems.map((item) => {
        const code = item.id;
        const isActive = active.has(code);
        return (
          <button
            key={code}
            type="button"
            className={isActive ? classNames.quickActive : classNames.quick}
            aria-label={item.label}
            aria-pressed={isActive}
            title={item.label}
            disabled={disabled}
            onClick={() => onPick(code)}
          >
            <span aria-hidden>{item.glyph}</span>
          </button>
        );
      })}
      <button
        ref={addAnchorRef}
        type="button"
        className={classNames.add}
        aria-label={addAriaLabel}
        aria-expanded={emojiOpen}
        disabled={disabled}
        onClick={() => setEmojiOpen((open) => !open)}
      >
        <Plus size={14} aria-hidden />
      </button>
      <EmojiInsertMenu
        open={emojiOpen}
        onOpenChange={setEmojiOpen}
        anchorRef={addAnchorRef}
        classNames={classNames.emojiMenu}
        listAriaLabel={emojiMenuAriaLabel}
        items={catalogItems}
        portalScopeClassName={portalScopeClassName}
        preferredPlacement="bottom"
        onSelect={(item) => {
          const code = (codeForItem?.(item) ?? item.id).trim();
          if (code) onPick(code);
          setEmojiOpen(false);
        }}
      />
    </div>
  );
}

export type DashboardReactionQuickBarProps = Omit<
  ReactionQuickBarProps,
  "classNames"
>;

export function createDashboardReactionQuickBar(prefix: string) {
  const classNames = reactionQuickBarBemClasses(prefix);
  return function DashboardReactionQuickBar(props: DashboardReactionQuickBarProps) {
    return <ReactionQuickBar classNames={classNames} {...props} />;
  };
}
