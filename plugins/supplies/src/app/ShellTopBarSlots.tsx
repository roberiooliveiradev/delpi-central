import { HelpTooltip } from "@delpi/plugin-ui/index";
import type { RefObject } from "react";
import { useEffect, useState } from "react";

import { fetchMeProfile, firstNameFromDisplay } from "../api/meApi";
import { SP_HELP } from "../content/helpTooltips";
import { SHELL_NAV_CONTENT } from "../content/shellNav";
import {
  buildSelfProfileSearch,
  buildUserProfilePath,
} from "../features/users/UserProfilePage";
import { navigatePluginPath } from "./pluginNavigation";
import { useSuppliesSession } from "./SuppliesSessionContext";
import { SuppliesAvatar, SuppliesTopBarSearchTrigger } from "./suppliesUi";

type ShellTopBarSecondaryProps = {
  searchTriggerRef: RefObject<HTMLButtonElement | null>;
  paletteOpen?: boolean;
  onOpenPalette: () => void;
};

/** Slot secondary — busca Ctrl+K (kit), igual Comercial. */
export function ShellTopBarSecondary({
  searchTriggerRef,
  paletteOpen = false,
  onOpenPalette,
}: ShellTopBarSecondaryProps) {
  return (
    <div className="sp-shell-secondary">
      <SuppliesTopBarSearchTrigger
        ref={searchTriggerRef}
        onOpen={onOpenPalette}
        label={SHELL_NAV_CONTENT.searchLabel}
        shortcutLabel={SHELL_NAV_CONTENT.searchShortcutLabel}
        aria-label={SHELL_NAV_CONTENT.searchAriaLabel}
        title={SHELL_NAV_CONTENT.searchTitle}
        expanded={paletteOpen}
      />
    </div>
  );
}

type ShellTopBarActionsProps = {
  basePath: string;
};

/**
 * Slot actions — avatar+nome → perfil self + hint de coexistência.
 * Ajuda fica só na nav (padrão Comercial).
 */
export function ShellTopBarActions({ basePath }: ShellTopBarActionsProps) {
  const session = useSuppliesSession();
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void fetchMeProfile(controller.signal)
      .then((profile) => setDisplayName(profile.name || null))
      .catch(() => {
        if (!controller.signal.aborted) setDisplayName(null);
      });
    return () => controller.abort();
  }, []);

  const userId = session.userId;
  const label =
    (displayName || "").trim() ||
    firstNameFromDisplay(displayName) ||
    SHELL_NAV_CONTENT.userMenu.nameFallback;
  const href = userId
    ? buildUserProfilePath(userId, basePath, buildSelfProfileSearch(basePath))
    : undefined;

  return (
    <div className="sp-shell-actions">
      {href ? (
        <a
          className="sp-shell-user"
          href={href}
          title={SHELL_NAV_CONTENT.userMenu.profileTitle}
          aria-label={SHELL_NAV_CONTENT.userMenu.profileAriaLabel}
          onClick={(event) => {
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            if (event.button !== 0) return;
            event.preventDefault();
            navigatePluginPath(href);
          }}
        >
          <SuppliesAvatar name={label} size="sm" />
          <span className="sp-shell-user__name delpi-ui-topbar-collapse-label">{label}</span>
        </a>
      ) : null}
      <HelpTooltip content={SP_HELP.coexistence} ariaLabel="Ajuda: Portal vs apps antigos" />
    </div>
  );
}
