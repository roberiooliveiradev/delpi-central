import { useEffect, useMemo, useState } from "react";
import {
  HOST_SELF_PROFILE_PATH,
  SectionCard,
  createDashboardPortalUserProfilePage,
  navigateHostPath,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";
import {
  CheckSquare,
  Home,
  MessagesSquare,
  Workflow,
} from "lucide-react";

import { InlineErrorState } from "../../components/ErrorStateBox";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { PortalTopBar } from "../../components/TransformometroNav";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TmStatusBadge } from "../../components/tmChromeUi";
import { PERSON_DIRECTORY_LABELS as L } from "../../content/personDirectoryLabels";
import {
  fetchPersonProfileIdentity,
  downloadPersonProfilePhoto,
  type PersonProfileIdentityDto,
} from "../../data/api/transformometroInteractionApi";
import { fetchMeProfile } from "../../data/api/meApi";
import { lookupDirectoryUsers } from "../../data/api/directoryUsersApi";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  TRANSFORMOMETRO_ACCESS_PERMISSION,
  TRANSFORMOMETRO_MANAGE_PERMISSION,
  usePortalSessionAccess,
} from "../../state/portalChrome";

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

const SECTION = sectionCardPacBemClasses("ds");
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

type Shortcut = {
  id: string;
  label: string;
  path: string;
  icon: typeof Home;
};

/**
 * Perfil do diretório no Portal Transforma+.
 * Identidade corporativa (cargo/contatos) e acesso da sessão são transversais Minha DELPI.
 * Editar (próprio): abre Meu Perfil Minha DELPI (`/profile`).
 */
export function PersonDirectoryPage({
  getAccessToken,
  pathname,
  userId,
  onNavigate,
}: Props) {
  const session = usePortalSessionAccess();
  const [meId, setMeId] = useState<string | null>(null);
  const [meLoading, setMeLoading] = useState(true);
  const [name, setName] = useState<string>("");
  const [email, setEmail] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [personProfile, setPersonProfile] = useState<PersonProfileIdentityDto | null>(null);
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
    setPersonProfile(null);

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

  useEffect(() => {
    const id = userId.trim();
    if (!id || loading || error) {
      if (!id || error) setPersonProfile(null);
      return undefined;
    }
    const controller = new AbortController();
    void fetchPersonProfileIdentity(id, getAccessToken)
      .then((profile) => {
        if (!controller.signal.aborted) setPersonProfile(profile);
      })
      .catch(() => {
        if (!controller.signal.aborted) setPersonProfile(null);
      });
    return () => controller.abort();
  }, [getAccessToken, userId, loading, error]);

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

  const permissionItems = useMemo(() => {
    const codes = [...new Set(session.permissions.map((code) => code.trim()).filter(Boolean))]
      .filter(
        (code) =>
          code === TRANSFORMOMETRO_ACCESS_PERMISSION ||
          code === TRANSFORMOMETRO_MANAGE_PERMISSION,
      )
      .sort((a, b) => a.localeCompare(b, "pt-BR"));
    return codes.map((code) => ({
      code,
      label:
        code === TRANSFORMOMETRO_MANAGE_PERMISSION
          ? L.permissionManage
          : L.permissionAccess,
    }));
  }, [session.permissions]);

  const busy = loading || meLoading;
  const ready = !busy && !error;
  const jobTitle = personProfile?.job_title ?? null;
  const supporting =
    (jobTitle || "").trim() || (email || "").trim() || undefined;

  return (
    <TransformometroShell>
      <PortalTopBar
        currentPath={pathname ?? `${TRANSFORMOMETRO_ROUTES.home}/users/${userId}`}
        onNavigate={onNavigate}
      />
      <TmPortalUserProfilePage
        isSelf={isSelf}
        onEditSelf={
          isSelf === true
            ? () => navigateHostPath(HOST_SELF_PROFILE_PATH)
            : undefined
        }
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
        loadingNode={<LoadingActivityCard title={L.loading} />}
        error={error ? <InlineErrorState title={L.error} message={error} /> : null}
        hero={
          ready
            ? {
                eyebrow: L.eyebrow,
                title: name,
                description: supporting,
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
                jobTitle: personProfile?.job_title ?? null,
                phone: personProfile?.phone_e164 ?? null,
                mobile: personProfile?.mobile_e164 ?? null,
                whatsapp: personProfile?.whatsapp_e164 ?? null,
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
        sections={
          ready ? (
            <SectionCard
              classNames={SECTION}
              labels={SECTION_LABELS}
              title={L.accessTitle}
              subtitle={L.accessSubtitle}
            >
              {isSelf === true ? (
                <div className="ds-user-profile__access">
                  {session.isSuperadmin ? (
                    <div className="ds-user-profile__access-group">
                      <h3 className="ds-user-profile__access-heading">Contexto admin</h3>
                      <div className="ds-nav-row">
                        <TmStatusBadge label={L.superadmin} variant="warning" />
                      </div>
                    </div>
                  ) : null}
                  <div className="ds-user-profile__access-group">
                    <h3 className="ds-user-profile__access-heading">Capacidades da sessão</h3>
                    <div className="ds-nav-row">
                      {session.permissions.includes(TRANSFORMOMETRO_ACCESS_PERMISSION) ||
                      session.isSuperadmin ? (
                        <TmStatusBadge label={L.capabilityAccess} variant="info" />
                      ) : null}
                      {session.canManage ? (
                        <TmStatusBadge label={L.capabilityManage} variant="info" />
                      ) : null}
                    </div>
                  </div>
                  <div className="ds-user-profile__access-group">
                    <h3 className="ds-user-profile__access-heading">Permissões RBAC</h3>
                    {permissionItems.length > 0 ? (
                      <ul className="ds-user-profile__permission-list">
                        {permissionItems.map((item) => (
                          <li key={item.code}>
                            <strong>{item.label}</strong>
                            <code>{item.code}</code>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="ds-muted">{L.accessSelfOnly}</p>
                    )}
                  </div>
                </div>
              ) : isSelf === false ? (
                <p className="ds-muted">{L.accessSelfOnly}</p>
              ) : (
                <p className="ds-muted">{L.accessLoading}</p>
              )}
            </SectionCard>
          ) : null
        }
      />
    </TransformometroShell>
  );
}
