import {
  EmptyState,
  HOST_SELF_PROFILE_PATH,
  createDashboardPortalUserProfilePage,
  navigateHostPath,
} from "@delpi/plugin-ui/index";
import {
  BriefcaseBusiness,
  CalendarCheck,
  Home,
  LayoutDashboard,
  Mail,
  MessageCircle,
  Phone,
  Shield,
  UsersRound,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { fetchMeProfile } from "../../api/meApi";
import { httpGetBlob } from "../../api/httpClient";
import {
  getUserProfile,
  userProfilePhotoAbsoluteUrl,
  type UserProfileDto,
  type UserProfilePortfolioDto,
} from "../../api/userProfileApi";
import { buildWhatsAppUrl } from "../../content/whatsapp";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialEntityLink,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
  CM_PORTAL_SCOPE,
  UI_PREFIX,
} from "../../app/commercialUi";
import {
  buildPluginPath,
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import { resolvePagePathBack } from "../../app/commercialNavigationReturn";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { buildShellPortfolioCustomersSearch } from "../../app/shellUserPortfolioNav";
import { portfolioLinkTitle } from "../../content/entityLinkHints";
import { CM_HELP } from "../../content/helpTooltips";
import {
  formatPortfolioCountValue,
  formatPortfolioRoleLabel,
  formatPortfoliosCount,
  listCommercialPermissions,
  listGrantedCapabilities,
  USER_ACCESS_COPY,
} from "../../content/userAccess";
import { directoryUserLabelOrFallback } from "../../shared/directoryUserLabel";
import { buildSellerPortfolioDetailPath } from "../../utils/sellerPortfoliosDeepLink";

type UserProfilePageProps = {
  basePath: string;
  userId: string;
};

type ShortcutItem = {
  id: string;
  label: string;
  icon: ReactNode;
  onSelect: () => void;
};

/** Visual e comportamento do perfil vêm do kit; Comercial entrega dados, copy e seções. */
const CommercialPortalUserProfilePage = createDashboardPortalUserProfilePage({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
  classNames: { section: cmSectionCardClassNames },
  labels: {
    section: cmSectionLabels,
    identityTitle: USER_ACCESS_COPY.identityTitle,
    identitySubtitle: USER_ACCESS_COPY.identitySubtitle,
    shortcutsTitle: USER_ACCESS_COPY.shortcutsTitle,
    shortcutsSubtitle: USER_ACCESS_COPY.shortcutsSubtitle,
    shortcutsAriaLabel: USER_ACCESS_COPY.shortcutsAriaLabel,
    jobTitleLabel: USER_ACCESS_COPY.jobTitleLabel,
    emailLabel: USER_ACCESS_COPY.emailLabel,
    phoneLabel: USER_ACCESS_COPY.phoneLabel,
    mobileLabel: USER_ACCESS_COPY.mobileLabel,
    whatsappLabel: USER_ACCESS_COPY.whatsappLabel,
  },
});

export function UserProfilePage({ basePath, userId }: UserProfilePageProps) {
  const {
    currentUserId,
    loading: scopeLoading,
    canManagePortfolios,
    canViewWorklist,
    canManageFollowups,
    canViewAnalytics,
    canViewProposals,
    canUseTeamScope,
    canViewWorklistTeam,
    canAccessMyPortfolio,
    canBillingNotify,
    isAdmin,
    setSellerIdFilter,
  } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfileDto | null>(null);
  const [photoObjectUrl, setPhotoObjectUrl] = useState<string | null>(null);
  const [mePermissions, setMePermissions] = useState<string[]>([]);
  const [meIsSuperadmin, setMeIsSuperadmin] = useState(false);

  /** null = ainda não sabemos o usuário da sessão (evita flash de “outro usuário”). */
  const isSelf = useMemo((): boolean | null => {
    if (scopeLoading) return null;
    const me = (currentUserId || "").trim();
    if (!me) return null;
    return me === userId.trim();
  }, [currentUserId, scopeLoading, userId]);

  const isOther = isSelf === false;

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const data = await getUserProfile(userId, signal);
        if (signal?.aborted) return;
        setProfile(data);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setProfile(null);
        setError(err instanceof Error ? err.message : "Falha ao carregar perfil.");
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [userId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  useEffect(() => {
    if (isSelf !== true) {
      setMePermissions([]);
      setMeIsSuperadmin(false);
      return undefined;
    }
    const controller = new AbortController();
    void fetchMeProfile(controller.signal)
      .then((me) => {
        if (controller.signal.aborted) return;
        setMePermissions(me.permissions || []);
        setMeIsSuperadmin(Boolean(me.is_superadmin));
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setMePermissions([]);
          setMeIsSuperadmin(false);
        }
      });
    return () => controller.abort();
  }, [isSelf]);

  useEffect(() => {
    let revoked: string | null = null;
    let cancelled = false;
    if (!profile?.has_photo) {
      setPhotoObjectUrl(null);
      return undefined;
    }
    void httpGetBlob(userProfilePhotoAbsoluteUrl(userId))
      .then((blob) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        revoked = url;
        setPhotoObjectUrl(url);
      })
      .catch(() => {
        if (!cancelled) setPhotoObjectUrl(null);
      });
    return () => {
      cancelled = true;
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [profile?.has_photo, profile?.updated_at, userId]);

  const permissionItems = useMemo(
    () => listCommercialPermissions(mePermissions),
    [mePermissions],
  );
  const capabilityItems = useMemo(
    () =>
      isSelf === true
        ? listGrantedCapabilities({
            access: canViewWorklist || canViewAnalytics || canViewProposals,
            manage: canManagePortfolios || canUseTeamScope,
            billing_notify: canBillingNotify,
          })
        : [],
    [
      canBillingNotify,
      canManagePortfolios,
      canUseTeamScope,
      canViewAnalytics,
      canViewProposals,
      canViewWorklist,
      isSelf,
    ],
  );

  const portfolioIds = useMemo(
    () => profile?.portfolios.map((item) => item.id).filter(Boolean) ?? [],
    [profile?.portfolios],
  );

  const canAssignTaskToProfile =
    Boolean(canManageFollowups) &&
    Boolean(canViewWorklistTeam || isAdmin) &&
    isOther;

  const shortcuts = useMemo(() => {
    const items: ShortcutItem[] = [
      {
        id: "home",
        label: USER_ACCESS_COPY.shortcutHome,
        icon: <Home size={18} aria-hidden />,
        onSelect: () => navigatePluginView("home", { basePath }),
      },
    ];
    if (canViewWorklist) {
      items.push({
        id: "tasks",
        label: USER_ACCESS_COPY.shortcutTasks,
        icon: <CalendarCheck size={18} aria-hidden />,
        onSelect: () => navigatePluginView("my_tasks", { basePath }),
      });
    }
    if (canAccessMyPortfolio) {
      items.push({
        id: "customers",
        label: USER_ACCESS_COPY.shortcutCustomers,
        icon: <BriefcaseBusiness size={18} aria-hidden />,
        onSelect: () => navigatePluginView("customers", { basePath }),
      });
    }
    if (canViewAnalytics) {
      items.push({
        id: "overview",
        label: USER_ACCESS_COPY.shortcutOverview,
        icon: <LayoutDashboard size={18} aria-hidden />,
        onSelect: () => navigatePluginView("overview", { basePath }),
      });
    }
    if (canManagePortfolios || isAdmin) {
      items.push({
        id: "admin",
        label: USER_ACCESS_COPY.shortcutAdmin,
        icon: <Shield size={18} aria-hidden />,
        onSelect: () => navigatePluginView("administration", { basePath }),
      });
    }

    const email = (profile?.email || "").trim();
    if (email) {
      items.push({
        id: "mailto",
        label: USER_ACCESS_COPY.shortcutEmail,
        icon: <Mail size={18} aria-hidden />,
        onSelect: () => {
          window.location.href = `mailto:${email}`;
        },
      });
    }
    const phone = (profile?.phone_e164 || profile?.mobile_e164 || "").trim();
    if (phone) {
      items.push({
        id: "tel",
        label: USER_ACCESS_COPY.shortcutCall,
        icon: <Phone size={18} aria-hidden />,
        onSelect: () => {
          window.location.href = `tel:${phone.replace(/\s+/g, "")}`;
        },
      });
    }
    const whatsapp = (profile?.whatsapp_e164 || "").trim();
    if (whatsapp) {
      items.push({
        id: "whatsapp",
        label: USER_ACCESS_COPY.shortcutWhatsapp,
        icon: <MessageCircle size={18} aria-hidden />,
        onSelect: () => {
          window.open(
            buildWhatsAppUrl(whatsapp, ""),
            "_blank",
            "noopener,noreferrer",
          );
        },
      });
    }
    if (canAssignTaskToProfile) {
      items.push({
        id: "assign-task",
        label: USER_ACCESS_COPY.shortcutAssignTask,
        icon: <CalendarCheck size={18} aria-hidden />,
        onSelect: () =>
          navigatePluginView("my_tasks", {
            basePath,
            search: `?createTask=1&assignee_user_id=${encodeURIComponent(userId)}`,
          }),
      });
    }
    return items;
  }, [
    basePath,
    canAccessMyPortfolio,
    canAssignTaskToProfile,
    canManagePortfolios,
    canViewAnalytics,
    canViewWorklist,
    isAdmin,
    profile?.email,
    profile?.mobile_e164,
    profile?.phone_e164,
    profile?.whatsapp_e164,
    userId,
  ]);

  const openPortfolio = (item: UserProfilePortfolioDto) => {
    if (canManagePortfolios) {
      const href = buildSellerPortfolioDetailPath(basePath, item.id);
      if (href) navigatePluginPath(href);
      return;
    }
    if (!canAccessMyPortfolio) return;
    setSellerIdFilter(portfolioIds.length > 1 ? item.id : null);
    navigatePluginView("customers", {
      basePath,
      search: buildShellPortfolioCustomersSearch(item.id, portfolioIds),
    });
  };

  const busy = loading || scopeLoading;
  const ready = !busy && Boolean(profile);
  const displayName = profile
    ? directoryUserLabelOrFallback({ name: profile.name })
    : "";
  const heroDescription =
    (profile?.job_title ?? "").trim() ||
    (profile?.email ?? "").trim() ||
    undefined;
  const pathSearch =
    typeof window !== "undefined" ? window.location.search : "";
  const back = resolvePagePathBack(
    pathSearch,
    { href: basePath, label: "Portal Comercial" },
    basePath,
  );

  return (
    <CommercialPortalUserProfilePage
      className="cm-user-profile"
      isSelf={isSelf}
      onEditSelf={
        isSelf === true
          ? () => navigateHostPath(HOST_SELF_PROFILE_PATH)
          : undefined
      }
      contextBadges={
        ready && profile ? (
          <CommercialStatusBadge
            label={formatPortfoliosCount(profile.portfolios.length)}
            variant="info"
          />
        ) : undefined
      }
      pagePath={{
        back: {
          label: back.label,
          href: back.href,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(back.href);
          },
        },
        current: displayName || "Perfil",
      }}
      loading={busy}
      loadingNode={<CommercialLoadingCard title="Carregando perfil…" />}
      error={
        !busy && (error || !profile) ? (
          <CommercialStateBanner variant="error">
            {error || "Não foi possível abrir o perfil."}
          </CommercialStateBanner>
        ) : null
      }
      hero={
        ready && profile
          ? {
              eyebrow: USER_ACCESS_COPY.appBadge,
              title: displayName,
              description: heroDescription,
            }
          : undefined
      }
      identityHint={CM_HELP.users.profile}
      identity={
        ready && profile
          ? {
              name: displayName,
              email: profile.email,
              jobTitle: profile.job_title,
              phone: profile.phone_e164,
              mobile: profile.mobile_e164,
              whatsapp: profile.whatsapp_e164,
              photoUrl: photoObjectUrl,
              colorKey: profile.user_id,
              previewTitle: displayName,
              previewAriaLabel: photoObjectUrl
                ? USER_ACCESS_COPY.enlargePhoto.replace("{name}", displayName)
                : undefined,
            }
          : null
      }
      shortcutsHint={CM_HELP.users.shortcuts}
      shortcuts={ready ? shortcuts : undefined}
      sections={
        ready && profile ? (
          <>
            <CommercialSectionCard
              title={USER_ACCESS_COPY.groupsTitle}
              subtitle={USER_ACCESS_COPY.groupsSubtitle}
              actions={
                canManagePortfolios || isAdmin ? (
                  <CommercialActionButton
                    variant="ghost"
                    title={USER_ACCESS_COPY.groupsManageHint}
                    onClick={() =>
                      navigatePluginView("administration_groups", { basePath })
                    }
                  >
                    <UsersRound size={16} strokeWidth={1.75} aria-hidden="true" />
                    {USER_ACCESS_COPY.groupsManage}
                  </CommercialActionButton>
                ) : null
              }
            >
              {(profile.groups ?? []).length === 0 ? (
                <p className="cm-muted">{USER_ACCESS_COPY.groupsEmpty}</p>
              ) : (
                <div className="cm-user-profile__portfolio-grid">
                  {(profile.groups ?? []).map((group) => (
                    <CommercialDataRecordCard
                      key={group.id}
                      leading={<UsersRound size={18} aria-hidden />}
                      title={group.name}
                      subtitle={group.active ? null : USER_ACCESS_COPY.groupInactive}
                      status={
                        <CommercialStatusBadge
                          label={
                            group.active
                              ? USER_ACCESS_COPY.groupActive
                              : USER_ACCESS_COPY.groupInactive
                          }
                          variant={group.active ? "info" : "neutral"}
                        />
                      }
                    />
                  ))}
                </div>
              )}
            </CommercialSectionCard>

            <CommercialSectionCard
              title={USER_ACCESS_COPY.portfoliosTitle}
              subtitle={USER_ACCESS_COPY.portfoliosSubtitle}
              hint={CM_HELP.users.portfolios}
            >
              {profile.portfolios.length === 0 ? (
                <EmptyState
                  classNames={cmEmptyStateClassNames}
                  defaultTitle="Nenhuma carteira"
                  defaultMessage="Este usuário ainda não é membro de carteiras ativas."
                />
              ) : (
                <div className="cm-user-profile__portfolio-grid">
                  {profile.portfolios.map((item) => {
                    const canOpen = canManagePortfolios || canAccessMyPortfolio;
                    return (
                      <CommercialDataRecordCard
                        key={item.id}
                        leading={<BriefcaseBusiness size={18} aria-hidden />}
                        title={item.name}
                        subtitle={formatPortfolioRoleLabel(item.role)}
                        status={
                          <span className="cm-nav-row">
                            <CommercialStatusBadge
                              label={formatPortfolioRoleLabel(item.role)}
                              variant={item.role === "owner" ? "success" : "info"}
                            />
                            <CommercialStatusBadge
                              label={item.active ? "Ativa" : "Inativa"}
                              variant={item.active ? "success" : "neutral"}
                            />
                          </span>
                        }
                        fields={[
                          {
                            id: "customers",
                            label: USER_ACCESS_COPY.portfolioCustomers,
                            value: formatPortfolioCountValue(item.customer_count),
                          },
                          {
                            id: "members",
                            label: USER_ACCESS_COPY.portfolioMembers,
                            value: formatPortfolioCountValue(item.member_count),
                          },
                        ]}
                        context={
                          canOpen ? (
                            (() => {
                              const href = canManagePortfolios
                                ? buildSellerPortfolioDetailPath(basePath, item.id)
                                : buildPluginPath(
                                    "customers",
                                    basePath,
                                    buildShellPortfolioCustomersSearch(
                                      item.id,
                                      portfolioIds,
                                    ),
                                  );
                              if (!href) return null;
                              return (
                                <CommercialEntityLink
                                  href={href}
                                  title={portfolioLinkTitle(item.name)}
                                  className="cm-link-button"
                                  onNavigate={() => openPortfolio(item)}
                                >
                                  <Users size={16} aria-hidden />
                                  {USER_ACCESS_COPY.portfolioOpen}
                                </CommercialEntityLink>
                              );
                            })()
                          ) : null
                        }
                      />
                    );
                  })}
                </div>
              )}
            </CommercialSectionCard>

            <CommercialSectionCard
              title={USER_ACCESS_COPY.accessTitle}
              subtitle={USER_ACCESS_COPY.accessSubtitle}
              hint={CM_HELP.users.access}
            >
              {isSelf === true ? (
                <div className="cm-user-profile__access">
                  {meIsSuperadmin ? (
                    <div className="cm-user-profile__access-group">
                      <h3 className="cm-user-profile__access-heading">Contexto admin</h3>
                      <div className="cm-nav-row">
                        <CommercialStatusBadge
                          label={USER_ACCESS_COPY.superadmin}
                          variant="warning"
                        />
                      </div>
                    </div>
                  ) : null}
                  {capabilityItems.length > 0 ? (
                    <div className="cm-user-profile__access-group">
                      <h3 className="cm-user-profile__access-heading">
                        Capacidades da sessão
                      </h3>
                      <div className="cm-nav-row">
                        {capabilityItems.map((item) => (
                          <CommercialStatusBadge
                            key={item.key}
                            label={item.label}
                            variant="info"
                          />
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <div className="cm-user-profile__access-group">
                    <h3 className="cm-user-profile__access-heading">Permissões RBAC</h3>
                    {permissionItems.length > 0 ? (
                      <ul className="cm-user-profile__permission-list">
                        {permissionItems.map((item) => (
                          <li key={item.code}>
                            <strong>{item.label}</strong>
                            <code>{item.code}</code>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="cm-muted">{USER_ACCESS_COPY.noPermissions}</p>
                    )}
                  </div>
                </div>
              ) : isOther ? (
                <p className="cm-muted">{USER_ACCESS_COPY.accessSelfOnly}</p>
              ) : (
                <p className="cm-muted">Carregando acessos…</p>
              )}
            </CommercialSectionCard>
          </>
        ) : null
      }
    />
  );
}
