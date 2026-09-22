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

/** Canonical Minha DELPI self-profile (Portal host) — TM does not own identity. */
const HOST_SELF_PROFILE_PATH = "/profile";

/**
 * Identity chrome da TopBar — nome/foto via Core; clique abre `/profile` do host.
 * Sem página de perfil do Transformômetro e sem menu de domínio inventado.
 */
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

  const label = (displayName ?? "").trim() || "Usuário";

  return (
    <TopBarUserIdentity
      classNames={USER}
      avatarClassNames={AVATAR}
      displayName={displayName}
      fallbackLabel="Usuário"
      avatarUrl={photoUrl}
      loading={loading}
      portalScopeClassName="dashboard-transformometro"
      href={HOST_SELF_PROFILE_PATH}
      title="Abrir meu perfil Minha DELPI"
      ariaLabel={`Abrir meu perfil: ${label}`}
    />
  );
}
