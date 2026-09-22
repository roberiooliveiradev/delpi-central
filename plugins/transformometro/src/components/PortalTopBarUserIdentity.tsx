import { useEffect, useState } from "react";
import {
  TopBarUserIdentity,
  initialsAvatarBemClasses,
  topBarUserIdentityBemClasses,
} from "@delpi/plugin-ui/index";

import { fetchMeProfile } from "../data/api/meApi";
import { useMyPersonProfilePhotoUrl } from "../hooks/useMyPersonProfilePhotoUrl";
import { usePortalAccessToken } from "../state/portalChrome";
import {
  buildTransformometroUserPath,
  navigateTransformometroUserProfile,
  transformometroUserLinkTitle,
} from "../utils/userProfileLinks";

const USER = topBarUserIdentityBemClasses("ds");
const AVATAR = initialsAvatarBemClasses("ds");

/**
 * Identity chrome da TopBar — nome/foto via Core; clique abre o perfil
 * do Portal Transforma+ (`/apps/transformometro/users/:id`).
 * Identidade global Minha DELPI (`/profile`) fica no shell do host (sidebar).
 */
export function PortalTopBarUserIdentity() {
  const getAccessToken = usePortalAccessToken();
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const photoUrl = useMyPersonProfilePhotoUrl(true, getAccessToken);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    void fetchMeProfile(getAccessToken, controller.signal)
      .then((profile) => {
        if (!controller.signal.aborted) {
          setDisplayName(profile.name || null);
          setUserId(profile.id || null);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setDisplayName(null);
          setUserId(null);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [getAccessToken]);

  const label = (displayName ?? "").trim() || "Usuário";
  const href = userId ? buildTransformometroUserPath(userId) : null;

  return (
    <TopBarUserIdentity
      classNames={USER}
      avatarClassNames={AVATAR}
      displayName={displayName}
      fallbackLabel="Usuário"
      avatarUrl={photoUrl}
      loading={loading}
      portalScopeClassName="dashboard-transformometro"
      href={href ?? undefined}
      title={href ? transformometroUserLinkTitle(label) : undefined}
      ariaLabel={href ? `Abrir meu perfil: ${label}` : undefined}
      onNavigate={
        href && userId
          ? (event) => {
              event.preventDefault();
              navigateTransformometroUserProfile(userId, userId);
            }
          : undefined
      }
    />
  );
}
