import { EmptyState } from "@delpi/plugin-ui/index";
import {
  BriefcaseBusiness,
  CalendarCheck,
  Camera,
  Home,
  LayoutDashboard,
  Mail,
  Pencil,
  Shield,
  Trash2,
  UserRound,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";

import { fetchMeProfile } from "../../api/meApi";
import { httpGetBlob } from "../../api/httpClient";
import {
  deleteUserProfilePhoto,
  getUserProfile,
  patchUserProfile,
  uploadUserProfilePhoto,
  userProfilePhotoAbsoluteUrl,
  type UserProfileDto,
  type UserProfilePortfolioDto,
} from "../../api/userProfileApi";
import {
  cmEmptyStateClassNames,
  CommercialActionButton,
  CommercialAvatar,
  CommercialDataRecordCard,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
} from "../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { buildShellPortfolioCustomersSearch } from "../../app/shellUserPortfolioNav";
import { CM_HELP } from "../../content/helpTooltips";
import {
  formatPortfolioCountValue,
  formatPortfolioRoleLabel,
  formatPortfoliosCount,
  listCommercialPermissions,
  listGrantedCapabilities,
  USER_ACCESS_COPY,
} from "../../content/userAccess";
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

export function UserProfilePage({ basePath, userId }: UserProfilePageProps) {
  const {
    currentUserId,
    canManagePortfolios,
    canViewWorklist,
    canManageFollowups,
    canViewAnalytics,
    canViewProposals,
    canExportProposals,
    canUseTeamScope,
    canViewAccountsTeam,
    canViewWorklistTeam,
    canAccessMyPortfolio,
    isAdmin,
    setSellerIdFilter,
  } = usePortfolioScope();
  const { notifyError, notifySuccess } = useCommercialFloatingNotice();
  const fileInputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfileDto | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [photoObjectUrl, setPhotoObjectUrl] = useState<string | null>(null);
  const [mePermissions, setMePermissions] = useState<string[]>([]);
  const [meIsSuperadmin, setMeIsSuperadmin] = useState(false);

  const isSelf = useMemo(() => {
    const me = (currentUserId || "").trim();
    return Boolean(me && me === userId.trim());
  }, [currentUserId, userId]);

  const canEdit = isSelf;

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const data = await getUserProfile(userId, signal);
        if (signal?.aborted) return;
        setProfile(data);
        setJobTitle((data.job_title || "").trim());
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
    setEditing(false);
  }, [userId]);

  useEffect(() => {
    if (!isSelf) {
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
      isSelf
        ? listGrantedCapabilities({
            worklist_view: canViewWorklist,
            followups_manage: canManageFollowups,
            seller_portfolios_manage: canManagePortfolios,
            analytics_view: canViewAnalytics,
            proposals_view: canViewProposals,
            proposals_export: canExportProposals,
            accounts_team_view: canViewAccountsTeam,
            worklist_team_view: canViewWorklistTeam,
            team_scope: canUseTeamScope,
          })
        : [],
    [
      canExportProposals,
      canManageFollowups,
      canManagePortfolios,
      canUseTeamScope,
      canViewAccountsTeam,
      canViewAnalytics,
      canViewProposals,
      canViewWorklist,
      canViewWorklistTeam,
      isSelf,
    ],
  );

  const portfolioIds = useMemo(
    () => profile?.portfolios.map((item) => item.id).filter(Boolean) ?? [],
    [profile?.portfolios],
  );

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
    return items;
  }, [
    basePath,
    canAccessMyPortfolio,
    canManagePortfolios,
    canViewAnalytics,
    canViewWorklist,
    isAdmin,
  ]);

  const startEditing = () => {
    if (!canEdit || !profile) return;
    setJobTitle((profile.job_title || "").trim());
    setEditing(true);
  };

  const cancelEditing = () => {
    if (saving) return;
    setJobTitle((profile?.job_title || "").trim());
    setEditing(false);
  };

  const onSaveProfile = async () => {
    if (!canEdit || !editing) return;
    setSaving(true);
    try {
      const data = await patchUserProfile(userId, { job_title: jobTitle.trim() || null });
      setProfile(data);
      setJobTitle((data.job_title || "").trim());
      setEditing(false);
      notifySuccess("Perfil atualizado.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao salvar perfil.");
    } finally {
      setSaving(false);
    }
  };

  const onUploadPhoto = async (file: File | null | undefined) => {
    if (!canEdit || !editing || !file) return;
    setSaving(true);
    try {
      const data = await uploadUserProfilePhoto(userId, file);
      setProfile(data);
      notifySuccess("Foto atualizada.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao enviar foto.");
    } finally {
      setSaving(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const onRemovePhoto = async () => {
    if (!canEdit || !editing) return;
    setSaving(true);
    try {
      const data = await deleteUserProfilePhoto(userId);
      setProfile(data);
      notifySuccess("Foto removida.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao remover foto.");
    } finally {
      setSaving(false);
    }
  };

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

  if (loading) {
    return <CommercialLoadingCard title="Carregando perfil…" />;
  }

  if (error || !profile) {
    return (
      <CommercialStateBanner variant="error">
        {error || "Não foi possível abrir o perfil."}
      </CommercialStateBanner>
    );
  }

  const displayName = profile.name || profile.user_id;
  const heroDescription = [profile.email, profile.job_title].filter(Boolean).join(" · ");

  return (
    <div className="cm-user-profile cm-page-stack">
      <CommercialPagePath
        back={{
          label: "Portal Comercial",
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(basePath);
          },
        }}
        items={[]}
        current={displayName}
      />

      <CommercialPageHero
        title={displayName}
        description={heroDescription || undefined}
        badge={
          <span className="cm-nav-row">
            <CommercialStatusBadge label="Commercial" variant="success" />
            {meIsSuperadmin && isSelf ? (
              <CommercialStatusBadge label={USER_ACCESS_COPY.superadmin} variant="warning" />
            ) : null}
            <CommercialStatusBadge
              label={formatPortfoliosCount(profile.portfolios.length)}
              variant="info"
            />
            {editing ? (
              <CommercialStatusBadge label={USER_ACCESS_COPY.editingBadge} variant="warning" />
            ) : null}
          </span>
        }
        actions={
          canEdit ? (
            editing ? (
              <div className="cm-nav-row">
                <CommercialActionButton
                  variant="ghost"
                  disabled={saving}
                  onClick={cancelEditing}
                >
                  {USER_ACCESS_COPY.cancelEdit}
                </CommercialActionButton>
                <CommercialActionButton
                  variant="primary"
                  disabled={saving}
                  onClick={() => void onSaveProfile()}
                >
                  {USER_ACCESS_COPY.saveProfile}
                </CommercialActionButton>
              </div>
            ) : (
              <CommercialActionButton
                variant="primary"
                onClick={startEditing}
                aria-label={CM_HELP.users.editMode}
              >
                <Pencil size={16} aria-hidden />
                {USER_ACCESS_COPY.editProfile}
              </CommercialActionButton>
            )
          ) : undefined
        }
      />

      <div className="cm-user-profile__grid">
        <CommercialSectionCard title={USER_ACCESS_COPY.identityTitle} hint={CM_HELP.users.profile}>
          <div className="cm-user-profile__identity">
            <div className="cm-user-profile__avatar-block">
              {editing && canEdit ? (
                <>
                  <button
                    type="button"
                    className="cm-user-profile__avatar-button"
                    aria-label={USER_ACCESS_COPY.changePhoto}
                    disabled={saving}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <CommercialAvatar
                      name={displayName}
                      colorKey={profile.user_id}
                      src={photoObjectUrl}
                      size="lg"
                      previewable={false}
                    />
                    <span className="cm-user-profile__avatar-overlay" aria-hidden>
                      <Camera size={18} />
                      <span>{USER_ACCESS_COPY.changePhoto}</span>
                    </span>
                  </button>
                  <input
                    ref={fileInputRef}
                    id={fileInputId}
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    className="cm-user-profile__file-input"
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      void onUploadPhoto(file);
                    }}
                  />
                  {profile.has_photo ? (
                    <CommercialActionButton
                      variant="ghost"
                      disabled={saving}
                      onClick={() => void onRemovePhoto()}
                    >
                      <Trash2 size={16} aria-hidden />
                      {USER_ACCESS_COPY.removePhoto}
                    </CommercialActionButton>
                  ) : null}
                </>
              ) : (
                <CommercialAvatar
                  name={displayName}
                  colorKey={profile.user_id}
                  src={photoObjectUrl}
                  size="lg"
                  previewTitle={displayName}
                  portalScopeClassName="dashboard-commercial"
                />
              )}
            </div>

            <div className="cm-user-profile__identity-fields">
              <div className="cm-user-profile__meta-row">
                <Mail size={16} aria-hidden />
                <span>{profile.email || "Sem e-mail"}</span>
              </div>
              <div className="cm-user-profile__meta-row">
                <UserRound size={16} aria-hidden />
                <span>
                  {USER_ACCESS_COPY.userIdLabel}: {profile.user_id}
                </span>
              </div>

              {editing && canEdit ? (
                <div className="cm-user-profile__job-form">
                  <CommercialTextField
                    label="Cargo"
                    value={jobTitle}
                    onChange={setJobTitle}
                    hint={CM_HELP.users.jobTitle}
                    fullWidth
                  />
                </div>
              ) : (
                <p className="cm-user-profile__job-readonly">
                  <strong>Cargo:</strong>{" "}
                  {(profile.job_title || "").trim() || USER_ACCESS_COPY.jobTitleEmpty}
                </p>
              )}
            </div>
          </div>
        </CommercialSectionCard>

        <CommercialSectionCard
          title={USER_ACCESS_COPY.shortcutsTitle}
          subtitle={USER_ACCESS_COPY.shortcutsSubtitle}
          hint={CM_HELP.users.shortcuts}
        >
          <div className="cm-user-profile__shortcuts">
            {shortcuts.map((item) => (
              <CommercialActionButton
                key={item.id}
                variant="default"
                onClick={item.onSelect}
              >
                {item.icon}
                {item.label}
              </CommercialActionButton>
            ))}
          </div>
        </CommercialSectionCard>
      </div>

      <CommercialSectionCard
        title={USER_ACCESS_COPY.groupsTitle}
        subtitle={USER_ACCESS_COPY.groupsSubtitle}
      >
        {(profile.groups ?? []).length === 0 ? (
          <p className="cm-muted">{USER_ACCESS_COPY.groupsEmpty}</p>
        ) : (
          <div className="cm-nav-row">
            {(profile.groups ?? []).map((group) => (
              <CommercialStatusBadge
                key={group.id}
                label={group.name}
                variant={group.active ? "info" : "neutral"}
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
                      <CommercialActionButton
                        variant="ghost"
                        onClick={() => openPortfolio(item)}
                      >
                        <Users size={16} aria-hidden />
                        {USER_ACCESS_COPY.portfolioOpen}
                      </CommercialActionButton>
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
        {isSelf ? (
          <div className="cm-user-profile__access">
            {capabilityItems.length > 0 ? (
              <div className="cm-user-profile__access-group">
                <h3 className="cm-user-profile__access-heading">Capacidades da sessão</h3>
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
        ) : (
          <p className="cm-muted">{USER_ACCESS_COPY.accessSelfOnly}</p>
        )}
      </CommercialSectionCard>

      <CommercialSectionCard title={USER_ACCESS_COPY.aboutTitle}>
        <p className="cm-muted">{USER_ACCESS_COPY.aboutBody}</p>
      </CommercialSectionCard>
    </div>
  );
}
