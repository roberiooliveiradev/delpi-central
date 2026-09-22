import type { RefObject } from "react";
import { useEffect, useState } from "react";

import { fetchMeProfile, firstNameFromDisplay } from "../api/meApi";
import { SHELL_NAV_CONTENT } from "../content/shellNav";
import {
  buildSelfProfileSearch,
  buildUserProfilePath,
} from "../features/users/UserProfilePage";
import { navigatePluginPath } from "./pluginNavigation";
import { ShellFavoritesStrip } from "./ShellFavoritesStrip";
import { useSuppliesSession } from "./SuppliesSessionContext";
import { useMyPersonProfile } from "./useMyPersonProfile";
import {
  SuppliesTopBarSearchTrigger,
  SuppliesTopBarUserIdentity,
  SuppliesTopBarUtilityCluster,
} from "./suppliesUi";

type ShellTopBarSecondaryProps = {
  basePath: string;
  searchTriggerRef: RefObject<HTMLButtonElement | null>;
  paletteOpen?: boolean;
  onOpenPalette: () => void;
};

/** Slot secondary — busca Ctrl+K + Favoritos (padrão Comercial). */
export function ShellTopBarSecondary({
  basePath,
  searchTriggerRef,
  paletteOpen = false,
  onOpenPalette,
}: ShellTopBarSecondaryProps) {
  return (
    <SuppliesTopBarUtilityCluster>
      <SuppliesTopBarSearchTrigger
        ref={searchTriggerRef}
        onOpen={onOpenPalette}
        label={SHELL_NAV_CONTENT.searchLabel}
        shortcutLabel={SHELL_NAV_CONTENT.searchShortcutLabel}
        aria-label={SHELL_NAV_CONTENT.searchAriaLabel}
        title={SHELL_NAV_CONTENT.searchTitle}
        expanded={paletteOpen}
      />
      <ShellFavoritesStrip basePath={basePath} />
    </SuppliesTopBarUtilityCluster>
  );
}

type ShellTopBarActionsProps = {
  basePath: string;
};

/**
 * Slot actions — avatar+nome → perfil self (chrome shared TopBarUserIdentity).
 * Foto vem da Core (person-profile); prefs do Portal ficam em /users/:id.
 */
export function ShellTopBarActions({ basePath }: ShellTopBarActionsProps) {
  const session = useSuppliesSession();
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { photoUrl } = useMyPersonProfile(Boolean(session.userId));

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    void fetchMeProfile(controller.signal)
      .then((profile) => {
        if (!controller.signal.aborted) {
          setDisplayName(profile.name || null);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setDisplayName(null);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, []);

  const userId = session.userId;
  if (!userId) return null;

  const href = buildUserProfilePath(userId, basePath, buildSelfProfileSearch(basePath));
  const label =
    (displayName || "").trim() ||
    firstNameFromDisplay(displayName) ||
    SHELL_NAV_CONTENT.userMenu.nameFallback;

  return (
    <div className="sp-shell-actions">
      <SuppliesTopBarUserIdentity
        displayName={displayName}
        fallbackLabel={SHELL_NAV_CONTENT.userMenu.nameFallback}
        avatarUrl={photoUrl}
        loading={loading}
        href={href}
        title={SHELL_NAV_CONTENT.userMenu.profileTitle}
        ariaLabel={SHELL_NAV_CONTENT.userMenu.profileAriaLabel}
        portalScopeClassName="dashboard-supplies-portal"
        onNavigate={() => navigatePluginPath(href)}
      />
    </div>
  );
}
