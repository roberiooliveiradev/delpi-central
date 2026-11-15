/**
 * Perfil de usuário do Portal — `/users/{userId}` com PortalUserProfilePage.
 * Self-only via BFF `/me/profile` (sem endpoint de outro usuário → 403).
 */
import {
  HOST_SELF_PROFILE_PATH,
  createDashboardPortalUserProfilePage,
  navigateHostPath,
  portalUserProfileAccessBemClasses,
} from "@delpi/plugin-ui/index";
import { Home, LayoutDashboard } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import {
  ApiError,
  cfApiUrl,
  httpGetImageBlob,
} from "../../api/httpClient";
import { getMyProfile, type MyProfile } from "../../api/meApi";
import {
  CF_PORTAL_SCOPE,
  CfEmptyState,
  CfLoadingCard,
  CfSectionCard,
  CfStatusBadge,
  UI_PREFIX,
  cfEmptyStateClassNames,
  cfSectionCardClassNames,
  cfSectionLabels,
} from "../../app/controllershipFinanceUi";
import {
  buildPluginPath,
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";

type UserProfilePageProps = {
  basePath: string;
  userId: string;
};

const CfPortalUserProfilePage = createDashboardPortalUserProfilePage({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
  classNames: { section: cfSectionCardClassNames },
  labels: {
    section: cfSectionLabels,
    identityTitle: "Identidade",
    identitySubtitle: "Dados corporativos do Core",
    shortcutsTitle: "Atalhos",
    shortcutsSubtitle: "Navegação rápida neste portal",
    shortcutsAriaLabel: "Atalhos do portal",
    jobTitleLabel: "Cargo",
    emailLabel: "E-mail",
    phoneLabel: "Telefone",
    mobileLabel: "Celular",
    whatsappLabel: "WhatsApp",
  },
});

const ACCESS = portalUserProfileAccessBemClasses(UI_PREFIX);

const PERMISSION_LABELS: Record<string, string> = {
  "controllership-finance.access": "Acesso ao portal",
  "controllership-finance.manage": "Gestão da Central de Fechamento",
  "controllership-finance.access.dre": "Documentos recebidos (DRE)",
};

function personField(
  profile: Record<string, unknown> | null,
  key: string,
): string | null {
  const value = profile?.[key];
  return typeof value === "string" && value.trim() ? value : null;
}

export function UserProfilePage({ basePath, userId }: UserProfilePageProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);

  const routeKey = (userId || "").trim() || "me";

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setForbidden(false);
    void getMyProfile({ signal: controller.signal })
      .then((mine) => {
        if (controller.signal.aborted) return;
        const selfId = (mine.id || "").trim();
        const isSelfRoute =
          routeKey === "me" || (Boolean(selfId) && routeKey === selfId);
        if (!isSelfRoute) {
          setForbidden(true);
          setProfile(null);
          return;
        }
        setProfile(mine);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && (err.status === 403 || err.status === 401)) {
          setForbidden(true);
          setError(null);
        } else {
          setError(err instanceof Error ? err.message : "Falha ao carregar perfil.");
        }
        setProfile(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [routeKey]);

  useEffect(() => {
    if (!profile) {
      setPhotoUrl(null);
      return;
    }
    const controller = new AbortController();
    let objectUrl: string | null = null;
    void httpGetImageBlob(cfApiUrl("/viewer-photo"), controller.signal)
      .then((blob) => {
        if (controller.signal.aborted || !blob) return;
        objectUrl = URL.createObjectURL(blob);
        setPhotoUrl(objectUrl);
      })
      .catch(() => {
        if (!controller.signal.aborted) setPhotoUrl(null);
      });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [profile]);

  const isSelf = profile !== null;

  const person = profile?.personProfile ?? null;
  const corporateName =
    personField(person, "fullName") ??
    personField(person, "name") ??
    profile?.displayName ??
    "—";
  const corporateEmail =
    personField(person, "email") ?? profile?.email ?? null;
  const jobTitle =
    personField(person, "jobTitle") ?? personField(person, "role") ?? null;

  const shortcuts = useMemo(() => {
    const items: Array<{
      id: string;
      label: string;
      icon: ReactNode;
      onSelect: () => void;
    }> = [
      {
        id: "home",
        label: "Início",
        icon: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
        onSelect: () => navigatePluginView("home", { basePath }),
      },
      {
        id: "entry_audit",
        label: "Auditoria de Entradas",
        icon: <LayoutDashboard size={16} strokeWidth={1.75} aria-hidden="true" />,
        onSelect: () => navigatePluginView("entry_audit", { basePath }),
      },
    ];
    return items;
  }, [basePath]);

  const permissionItems = useMemo(() => {
    const codes = [
      ...new Set(
        (profile?.permissions ?? [])
          .map((code) => String(code).trim())
          .filter(Boolean),
      ),
    ];
    return codes
      .filter((code) => code in PERMISSION_LABELS || code.startsWith("controllership-finance."))
      .sort((a, b) => a.localeCompare(b, "pt-BR"))
      .map((code) => ({
        code,
        label: PERMISSION_LABELS[code] ?? code,
      }));
  }, [profile?.permissions]);

  if (loading) {
    return <CfLoadingCard title="Carregando perfil…" />;
  }

  if (forbidden) {
    return (
      <CfEmptyState
        classNames={cfEmptyStateClassNames}
        title="Perfil indisponível"
        message="Só é possível abrir o próprio perfil neste portal."
      />
    );
  }

  if (error || !profile) {
    return (
      <CfEmptyState
        classNames={cfEmptyStateClassNames}
        title="Não foi possível carregar o perfil"
        message={error ?? "Tente novamente em instantes."}
      />
    );
  }

  return (
    <CfPortalUserProfilePage
      className="cf-user-profile"
      isSelf={isSelf}
      onEditSelf={
        isSelf ? () => navigateHostPath(HOST_SELF_PROFILE_PATH) : undefined
      }
      pagePath={{
        back: {
          label: "Início",
          href: buildPluginPath("home", basePath),
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(buildPluginPath("home", basePath));
          },
        },
        current: corporateName,
      }}
      loading={false}
      hero={{
        eyebrow: "Controladoria & Finanças",
        title: corporateName,
        description: jobTitle || corporateEmail || undefined,
      }}
      identity={{
        name: corporateName,
        email: corporateEmail,
        jobTitle,
        photoUrl,
        colorKey: profile.id,
        portalScopeClassName: CF_PORTAL_SCOPE,
      }}
      identityHint={CF_HELP.profile.identity}
      shortcuts={shortcuts}
      shortcutsHint={CF_HELP.profile.permissions}
      sections={
        permissionItems.length ? (
          <CfSectionCard
            title="Acesso neste portal"
            subtitle="Permissões efetivas do Core"
            hint={CF_HELP.profile.permissions}
          >
            <div className={ACCESS.access}>
              <ul className={ACCESS.accessList}>
                {permissionItems.map((item) => (
                  <li key={item.code}>
                    <CfStatusBadge label={item.label} variant="info" />
                  </li>
                ))}
              </ul>
            </div>
          </CfSectionCard>
        ) : undefined
      }
    />
  );
}
