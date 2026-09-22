import { useEffect, useState } from "react";
import {
  TopBarUserIdentity,
  initialsAvatarBemClasses,
  topBarUserIdentityBemClasses,
} from "@delpi/plugin-ui/index";

import { fetchMeProfile } from "../data/api/meApi";
import { useMyPersonProfilePhotoUrl } from "../hooks/useMyPersonProfilePhotoUrl";
import { usePortalAccessToken } from "../state/portalChrome";

const USER = topBarUserIdentityBemClasses("ds");
const AVATAR = initialsAvatarBemClasses("ds");

/** Identity chrome da TopBar — display-only (TM sem página de perfil própria). */
export function PortalTopBarUserIdentity() {
  const getAccessToken = usePortalAccessToken();
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const photoUrl = useMyPersonProfilePhotoUrl(true, getAccessToken);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    void fetchMeProfile(getAccessToken, controller.signal)
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
  }, [getAccessToken]);

  return (
    <TopBarUserIdentity
      classNames={USER}
      avatarClassNames={AVATAR}
      displayName={displayName}
      fallbackLabel="Usuário"
      avatarUrl={photoUrl}
      loading={loading}
      portalScopeClassName="dashboard-transformometro"
      ariaLabel={displayName ? `Usuário: ${displayName}` : "Usuário"}
    />
  );
}
