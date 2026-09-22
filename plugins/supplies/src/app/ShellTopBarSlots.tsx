import type { RefObject } from "react";
import { useCallback, useEffect, useState } from "react";
import { Settings2 } from "lucide-react";

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

/** Canonical Minha DELPI self-profile (Portal host). */
const HOST_SELF_PROFILE_PATH = "/profile";

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
 * Slot actions — avatar → `/profile` (identidade canônica Minha DELPI).
 * Nome abre menu com preferências do Portal Suprimentos (domínio local).
 */
export function ShellTopBarActions({ basePath }: ShellTopBarActionsProps) {
  const session = useSuppliesSession();
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
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
  const goToHostProfile = useCallback(() => {
    setMenuOpen(false);
    window.location.assign(HOST_SELF_PROFILE_PATH);
  }, []);

  const goToPortalPreferences = useCallback(() => {
    if (!userId) return;
    setMenuOpen(false);
    const href = buildUserProfilePath(
      userId,
      basePath,
      buildSelfProfileSearch(basePath),
    );
    navigatePluginPath(href);
  }, [basePath, userId]);

  if (!userId) return null;

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
        portalScopeClassName="dashboard-supplies-portal"
        avatarHref={HOST_SELF_PROFILE_PATH}
        onAvatarNavigate={goToHostProfile}
        avatarTitle={SHELL_NAV_CONTENT.userMenu.profileTitle}
        onLabelClick={() => setMenuOpen((open) => !open)}
        labelAriaLabel={SHELL_NAV_CONTENT.userMenu.menuOpenAriaLabel}
        labelHasPopup="menu"
        labelExpanded={menuOpen}
        open={menuOpen}
        onOpenChange={setMenuOpen}
        menuAriaLabel={SHELL_NAV_CONTENT.userMenu.menuAriaLabel}
        menuItems={[
          {
            id: "host-profile",
            label: SHELL_NAV_CONTENT.userMenu.hostProfileLabel,
            onSelect: goToHostProfile,
          },
          {
            id: "portal-preferences",
            label: SHELL_NAV_CONTENT.userMenu.portalPreferencesLabel,
            icon: Settings2,
            onSelect: goToPortalPreferences,
          },
        ]}
        ariaLabel={`Usuário: ${label}`}
      />
    </div>
  );
}
