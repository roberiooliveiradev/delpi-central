import { useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  HOST_SELF_PROFILE_PATH,
  createDashboardPortalUserProfilePage,
  navigateHostPath,
} from "@delpi/plugin-ui/index";
import {
  CheckSquare,
  Home,
  MessagesSquare,
  Pencil,
  Workflow,
} from "lucide-react";

import { PortalTopBar } from "../../components/TransformometroNav";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TmStatusBadge } from "../../components/tmChromeUi";
import { PERSON_DIRECTORY_LABELS as L } from "../../content/personDirectoryLabels";
import { lookupDirectoryUsers } from "../../data/api/directoryUsersApi";
import { downloadPersonProfilePhoto } from "../../data/api/transformometroInteractionApi";
import { fetchMeProfile } from "../../data/api/meApi";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

type Props = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  userId: string;
  onNavigate: (path: string) => void;
};

/** Visual e comportamento do perfil vêm do kit; Transforma+ entrega dados, copy e atalhos. */
const TmPortalUserProfilePage = createDashboardPortalUserProfilePage({
  prefix: "ds",
  portalScopeClassName: "dashboard-transformometro",
  labels: {
    pageAriaLabel: L.pageAriaLabel,
    identityTitle: L.identityTitle,
    identitySubtitle: L.identitySubtitle,
    shortcutsTitle: L.shortcutsTitle,
    shortcutsSubtitle: L.shortcutsSubtitle,
    shortcutsAriaLabel: L.shortcutsAriaLabel,
  },
});

type Shortcut = {
  id: string;
  label: string;
  path: string;
  icon: typeof Home;
};

/**
 * Perfil do diretório no Portal Transforma+.
 * Modo leitura: identidade + atalhos do portal.
 * Editar (próprio): abre Meu Perfil Minha DELPI (`/profile`) para foto/cargo/contatos.
 */
export function PersonDirectoryPage({
  getAccessToken,
  pathname,
  userId,
  onNavigate,
}: Props) {
  const [meId, setMeId] = useState<string | null>(null);
  const [meLoading, setMeLoading] = useState(true);
  const [name, setName] = useState<string>("");
  const [email, setEmail] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setMeLoading(true);
    void fetchMeProfile(getAccessToken, controller.signal)
      .then((profile) => {
        if (!controller.signal.aborted) {
          setMeId((profile.id || "").trim() || null);
          setMeLoading(false);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setMeId(null);
          setMeLoading(false);
        }
      });
    return () => controller.abort();
  }, [getAccessToken]);

  const isSelf = useMemo((): boolean | null => {
    if (meLoading) return null;
    const me = (meId || "").trim();
    if (!me) return null;
    return me === userId.trim();
  }, [meId, meLoading, userId]);

  useEffect(() => {
    const id = userId.trim();
    if (!id) return;

    const controller = new AbortController();
    let objectUrl: string | null = null;
    setLoading(true);
    setError(null);

    void Promise.all([
      lookupDirectoryUsers([id], controller.signal, getAccessToken),
      downloadPersonProfilePhoto(id, getAccessToken).catch(() => null),
    ])
      .then(([users, blob]) => {
        if (controller.signal.aborted) return;
        const hit = users[0];
        setName(hit?.name?.trim() || L.nameFallback);
        setEmail(hit?.email?.trim() || null);
        if (blob) {
          objectUrl = URL.createObjectURL(blob);
          setPhotoUrl(objectUrl);
        } else {
          setPhotoUrl(null);
        }
        setLoading(false);
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setError(L.error);
        setLoading(false);
      });

    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [getAccessToken, userId]);

  const shortcuts = useMemo<Shortcut[]>(
    () => [
      {
        id: "home",
        label: L.shortcutHome,
        path: TRANSFORMOMETRO_ROUTES.home,
        icon: Home,
      },
      {
        id: "tasks",
        label: L.shortcutTasks,
        path: TRANSFORMOMETRO_ROUTES.myTasks,
        icon: CheckSquare,
      },
      {
        id: "rooms",
        label: L.shortcutRooms,
        path: TRANSFORMOMETRO_ROUTES.interactionRooms,
        icon: MessagesSquare,
      },
      {
        id: "processes",
        label: L.shortcutProcesses,
        path: TRANSFORMOMETRO_ROUTES.processes,
        icon: Workflow,
      },
    ],
    [],
  );

  const busy = loading || meLoading;
  const ready = !busy && !error;

  return (
    <TransformometroShell>
      <PortalTopBar
        currentPath={pathname ?? `${TRANSFORMOMETRO_ROUTES.home}/users/${userId}`}
        onNavigate={onNavigate}
      />
      <TmPortalUserProfilePage
        pagePath={{
          back: {
            label: L.back,
            href: TRANSFORMOMETRO_ROUTES.home,
            onNavigate: (event) => {
              event.preventDefault();
              onNavigate(TRANSFORMOMETRO_ROUTES.home);
            },
          },
          current: name || L.currentFallback,
        }}
        loading={busy}
        loadingNode={<p>{L.loading}</p>}
        error={error ? <p>{error}</p> : null}
        hero={
          ready
            ? {
                eyebrow: L.eyebrow,
                title: name,
                description:
                  isSelf === true ? L.descriptionSelf : L.descriptionOther,
                badge: (
                  <TmStatusBadge
                    label={isSelf === true ? L.badgeSelf : L.badgeDirectory}
                    variant={isSelf === true ? "success" : "info"}
                  />
                ),
                actions:
                  isSelf === true ? (
                    <ActionButton
                      variant="primary"
                      type="button"
                      onClick={() => navigateHostPath(HOST_SELF_PROFILE_PATH)}
                    >
                      <Pencil size={16} aria-hidden />
                      {L.editIdentity}
                    </ActionButton>
                  ) : undefined,
              }
            : undefined
        }
        identity={
          ready
            ? {
                name,
                email,
                photoUrl,
                colorKey: userId,
              }
            : null
        }
        shortcuts={
          ready
            ? shortcuts.map((item) => {
                const Icon = item.icon;
                return {
                  id: item.id,
                  label: item.label,
                  icon: <Icon size={16} aria-hidden />,
                  onSelect: () => onNavigate(item.path),
                };
              })
            : undefined
        }
      />
    </TransformometroShell>
  );
}
