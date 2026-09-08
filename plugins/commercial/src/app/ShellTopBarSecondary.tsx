import type { RefObject } from "react";

import { CommercialTopBarSearchTrigger } from "./commercialUi";
import { SHELL_NAV_CONTENT } from "../content/shellNav";
import { ShellFavoritesStrip } from "./ShellFavoritesStrip";

type ShellTopBarSecondaryProps = {
  basePath: string;
  onOpenPalette: () => void;
  searchTriggerRef: RefObject<HTMLButtonElement | null>;
  paletteOpen?: boolean;
};

/**
 * Slot secondary da TopBar — busca (Command Palette popover) + favoritos.
 */
export function ShellTopBarSecondary({
  basePath,
  onOpenPalette,
  searchTriggerRef,
  paletteOpen = false,
}: ShellTopBarSecondaryProps) {
  return (
    <div className="cm-shell-secondary">
      <CommercialTopBarSearchTrigger
        ref={searchTriggerRef}
        onOpen={onOpenPalette}
        expanded={paletteOpen}
        label={SHELL_NAV_CONTENT.searchLabel}
        shortcutLabel={SHELL_NAV_CONTENT.searchShortcutLabel}
        aria-label={SHELL_NAV_CONTENT.searchAriaLabel}
        title={SHELL_NAV_CONTENT.searchTitle}
      />
      <ShellFavoritesStrip basePath={basePath} />
    </div>
  );
}
