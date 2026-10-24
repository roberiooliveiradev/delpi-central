import {
  HOST_SELF_PROFILE_PATH,
  createDashboardPortalUserProfilePage,
  navigateHostPath,
  portalUserProfileAccessBemClasses,
} from "@delpi/plugin-ui/index";
import {
  BookOpen,
  Home,
  LayoutDashboard,
  ShoppingCart,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import {
  getUserPhotoBlob,
  getUserProfile,
  getUserRelatedRequests,
  patchUserProfile,
  type SuppliesUserProfile,
  type UserRelatedRequestsResponse,
} from "../../api/userProfileApi";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import {
  buildPluginPath,
  buildPurchaseRequestDetailPath,
  normalizeBasePath,
  SUPPLIES_BASE_PATH,
} from "../../app/pluginRoutes";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import { useMyPersonProfile } from "../../app/useMyPersonProfile";
import {
  SuppliesActionButton,
  SuppliesEntityLink,
  SuppliesLoadingCard,
  SuppliesTitleWithHelp,
  SuppliesSectionCard,
  SuppliesStateBanner,
  SuppliesStatusBadge,
  spSectionCardClassNames,
  spSectionLabels,
  UI_PREFIX,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { USER_PROFILE_CONTENT as C } from "./userProfileContent";
import { PurchaseRequestsListTable } from "../purchase-requests/PurchaseRequestsListTable";
import { createDefaultQuery } from "../purchase-requests/query";
import type { PurchaseRequestsQuery } from "../purchase-requests/types";

type UserProfilePageProps = {
  basePath: string;
  userId: string;
};

/** Visual e comportamento do perfil vêm do kit; Suprimentos entrega dados, copy e seções. */
const SuppliesPortalUserProfilePage = createDashboardPortalUserProfilePage({
  prefix: UI_PREFIX,
  classNames: { section: spSectionCardClassNames },
  labels: {
    section: spSectionLabels,
    pageAriaLabel: C.pageAriaLabel,
    identityTitle: C.identityTitle,
    identitySubtitle: C.identitySubtitle,
    shortcutsTitle: C.shortcutsTitle,
    shortcutsSubtitle: C.shortcutsSubtitle,
    shortcutsAriaLabel: C.shortcutsAriaLabel,
    nameLabel: C.nameLabel,
    emailLabel: C.emailLabel,
    jobTitleLabel: C.jobTitleLabel,
    phoneLabel: C.phoneLabel,
    mobileLabel: C.mobileLabel,
    whatsappLabel: C.whatsappLabel,
  },
});

const ACCESS = portalUserProfileAccessBemClasses(UI_PREFIX);

function readReturnTo(): { href: string; label: string } {
  if (typeof window === "undefined") {
    return { href: SUPPLIES_BASE_PATH, label: C.backFallback };
  }
  const params = new URLSearchParams(window.location.search || "");
  const returnTo = (params.get("returnTo") || "").trim();
  const returnLabel = (params.get("returnLabel") || "").trim() || C.backFallback;
  if (returnTo.startsWith("/apps/supplies")) {
    return { href: returnTo, label: returnLabel };
  }
  return { href: normalizeBasePath(SUPPLIES_BASE_PATH), label: C.backFallback };
}

export function UserProfilePage({ basePath, userId }: UserProfilePageProps) {
  const session = useSuppliesSession();
  const isSelf = useMemo((): boolean | null => {
    if (session.loading) return null;
    const me = (session.userId || "").trim();
    if (!me) return null;
    return me === userId;
  }, [session.loading, session.userId, userId]);
  const { profile: personProfile, photoUrl } = useMyPersonProfile(isSelf === true);
  const [profile, setProfile] = useState<SuppliesUserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [defaultBranch, setDefaultBranch] = useState<string>("");
  const [tableDensity, setTableDensity] = useState<"comfortable" | "compact">(
    "comfortable",
  );
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [targetPhotoUrl, setTargetPhotoUrl] = useState<string | null>(null);
  const [related, setRelated] = useState<{
    loading: boolean;
    error: string | null;
    data: UserRelatedRequestsResponse | null;
  }>({ loading: false, error: null, data: null });
  const [relatedReloadKey, setRelatedReloadKey] = useState(0);
  const [relatedQuery, setRelatedQuery] = useState<PurchaseRequestsQuery>(() => ({
    ...createDefaultQuery(),
    // Compact page for the profile section — the shared table's own
    // pagination exposes 25/50/100 and stays inside the BFF cap (100).
    page_size: 25,
    sort_by: "issue_date",
    sort_dir: "desc",
  }));

  const back = useMemo(() => readReturnTo(), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setForbidden(false);
    setSaveMessage(null);
    setSaveError(null);
    getUserProfile(userId, controller.signal)
      .then((payload) => {
        setProfile(payload);
        setDefaultBranch(payload.preferences.defaultBranch || "");
        setTableDensity(payload.preferences.tableDensity || "comfortable");
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const message = err instanceof Error ? err.message : C.error;
        if (/403|forbidden/i.test(message)) {
          setForbidden(true);
          setError(null);
        } else {
          setError(message);
        }
        setProfile(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [userId, reloadKey]);

  useEffect(() => {
    const controller = new AbortController();
    if (isSelf !== false || !profile?.hasPhoto) {
      void Promise.resolve().then(() => {
        if (!controller.signal.aborted) setTargetPhotoUrl(null);
      });
      return () => controller.abort();
    }
    let objectUrl: string | null = null;
    getUserPhotoBlob(userId, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted) return;
        objectUrl = URL.createObjectURL(blob);
        setTargetPhotoUrl(objectUrl);
      })
      .catch(() => {
        if (!controller.signal.aborted) setTargetPhotoUrl(null);
      });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [isSelf, profile?.hasPhoto, userId]);

  useEffect(() => {
    const controller = new AbortController();
    void Promise.resolve().then(() => {
      if (controller.signal.aborted) return;
      if (!profile) {
        setRelated({ loading: false, error: null, data: null });
        return;
      }
      setRelated((prev) => ({ ...prev, loading: true, error: null }));
      getUserRelatedRequests(
        userId,
        {
          page: relatedQuery.page,
          pageSize: relatedQuery.page_size,
          sortBy: relatedQuery.sort_by,
          sortDir: relatedQuery.sort_dir,
        },
        controller.signal,
      )
        .then((data) => {
          if (controller.signal.aborted) return;
          // Degradation is not an empty universe — surface the error state.
          if (data?.error) {
            setRelated({ loading: false, error: data.error, data });
            return;
          }
          setRelated({ loading: false, error: null, data });
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return;
          const message = err instanceof Error ? err.message : C.relatedError;
          setRelated({ loading: false, error: message, data: null });
        });
    });
    return () => controller.abort();
  }, [userId, profile, relatedQuery, relatedReloadKey]);

  const shortcuts = useMemo(() => {
    const caps = profile?.capabilities ?? session.capabilities;
    const items: Array<{
      id: string;
      label: string;
      icon: ReactNode;
      onSelect: () => void;
    }> = [
      {
        id: "home",
        label: C.shortcutHome,
        icon: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
        onSelect: () => navigatePluginView("home", { basePath }),
      },
    ];
    if (caps.access) {
      items.push({
        id: "overview",
        label: C.shortcutOverview,
        icon: <LayoutDashboard size={16} strokeWidth={1.75} aria-hidden="true" />,
        onSelect: () => navigatePluginView("overview", { basePath }),
      });
    }
    if (caps.access) {
      items.push({
        id: "purchase_requests",
        label: C.shortcutSc,
        icon: <ShoppingCart size={16} strokeWidth={1.75} aria-hidden="true" />,
        onSelect: () => navigatePluginView("purchase_requests", { basePath }),
      });
    }
    items.push({
      id: "help",
      label: C.shortcutHelp,
      icon: <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />,
      onSelect: () => navigatePluginView("help", { basePath }),
    });
    return items;
  }, [basePath, profile?.capabilities, session.capabilities]);

  const onSave = async () => {
    if (!profile?.isSelf) return;
    setSaving(true);
    setSaveMessage(null);
    setSaveError(null);
    try {
      const updated = await patchUserProfile(userId, {
        preferences: {
          defaultBranch: defaultBranch || null,
          tableDensity,
        },
      });
      setProfile(updated);
      setSaveMessage(C.saveOk);
      await session.reload();
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : C.saveError);
    } finally {
      setSaving(false);
    }
  };

  const units = profile?.allowedUnits?.length
    ? profile.allowedUnits
    : session.allowedUnits;

  const busy = loading || session.loading;
  const ready = !busy && Boolean(profile);
  const jobTitle =
    (profile?.jobTitle ?? personProfile?.job_title ?? "") || null;
  const heroDescription =
    (typeof jobTitle === "string" && jobTitle.trim()) ||
    (profile?.email || "").trim() ||
    undefined;

  const permissionItems = useMemo(() => {
    const codes = [...new Set((profile?.permissions ?? []).map((c) => String(c).trim()).filter(Boolean))];
    return codes
      .filter(
        (code) =>
          code === C.permissionAccessCode || code === C.permissionManageCode,
      )
      .sort((a, b) => a.localeCompare(b, "pt-BR"))
      .map((code) => ({
        code,
        label:
          code === C.permissionManageCode ? C.permissionManage : C.permissionAccess,
      }));
  }, [profile?.permissions]);

  return (
    <SuppliesPortalUserProfilePage
      className="sp-user-profile"
      isSelf={isSelf}
      onEditSelf={
        isSelf === true
          ? () => navigateHostPath(HOST_SELF_PROFILE_PATH)
          : undefined
      }
      contextBadges={
        ready && units.length > 0 ? (
          <SuppliesStatusBadge
            label={`${C.unitsLabel}: ${units.join(", ")}`}
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
        current: profile?.name || "Perfil",
      }}
      loading={busy}
      loadingNode={<SuppliesLoadingCard title={C.loading} variant="panel" />}
      error={
        forbidden ? (
          <SuppliesStateBanner variant="error">{C.forbidden}</SuppliesStateBanner>
        ) : error ? (
          <>
            <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
            <SuppliesActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
              {C.retry}
            </SuppliesActionButton>
          </>
        ) : null
      }
      hero={
        ready && profile
          ? {
              eyebrow: C.backFallback,
              title: (
                <SuppliesTitleWithHelp title={profile.name} hint={SP_HELP.userProfile} />
              ),
              description: heroDescription,
            }
          : undefined
      }
      identityHint={SP_HELP.userProfile}
      identity={
        ready && profile
          ? {
              name: profile.name,
              email: profile.email,
              photoUrl: isSelf === true ? photoUrl : targetPhotoUrl,
              colorKey: userId,
              jobTitle: profile.jobTitle ?? personProfile?.job_title ?? null,
              phone: profile.phone ?? personProfile?.phone_e164 ?? null,
              mobile: profile.mobile ?? personProfile?.mobile_e164 ?? null,
              whatsapp: profile.whatsapp ?? personProfile?.whatsapp_e164 ?? null,
            }
          : null
      }
      shortcuts={ready ? shortcuts : undefined}
      sections={
        ready && profile ? (
          <>
            {profile.isSelf ? (
              <SuppliesSectionCard
                title={C.preferencesTitle}
                subtitle={C.preferencesSubtitle}
                hint={SP_HELP.userProfilePrefs}
              >
                <form
                  className="sp-user-profile__prefs"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void onSave();
                  }}
                >
                  <label>
                    <span>{C.defaultBranchLabel}</span>
                    <select
                      value={defaultBranch}
                      onChange={(event) => setDefaultBranch(event.target.value)}
                    >
                      <option value="">{C.defaultBranchEmpty}</option>
                      {session.allowedUnits.map((unit) => (
                        <option key={unit} value={unit}>
                          {unit}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>{C.tableDensityLabel}</span>
                    <select
                      value={tableDensity}
                      onChange={(event) =>
                        setTableDensity(event.target.value as "comfortable" | "compact")
                      }
                    >
                      <option value="comfortable">{C.densityComfortable}</option>
                      <option value="compact">{C.densityCompact}</option>
                    </select>
                  </label>
                  <SuppliesActionButton variant="primary" type="submit" disabled={saving}>
                    {saving ? C.saving : C.save}
                  </SuppliesActionButton>
                  {saveMessage ? (
                    <SuppliesStateBanner variant="success">{saveMessage}</SuppliesStateBanner>
                  ) : null}
                  {saveError ? (
                    <SuppliesStateBanner variant="error">{saveError}</SuppliesStateBanner>
                  ) : null}
                </form>
              </SuppliesSectionCard>
            ) : null}

            <SuppliesSectionCard
              title={C.relatedTitle}
              subtitle={C.relatedSubtitle}
            >
              {related.loading && !related.data ? (
                <p className="sp-user-profile__note">{C.relatedLoading}</p>
              ) : related.error ? (
                <>
                  <SuppliesStateBanner variant="error">
                    {related.error === "identity_lookup_unavailable"
                      ? C.relatedIdentityUnavailable
                      : C.relatedError}
                  </SuppliesStateBanner>
                  <SuppliesActionButton
                    variant="ghost"
                    onClick={() => setRelatedReloadKey((v) => v + 1)}
                  >
                    {C.retry}
                  </SuppliesActionButton>
                </>
              ) : related.data && related.data.items.length > 0 ? (
                <>
                  {/* Mesma tabela da listagem principal — reuso real de componente,
                      contrato, colunas, ordenação e paginação server-side. */}
                  <PurchaseRequestsListTable
                    items={related.data.items}
                    query={relatedQuery}
                    total={related.data.total}
                    loading={related.loading}
                    canExport={false}
                    basePath={basePath}
                    onExport={() => {}}
                    onPatchQuery={(patch) =>
                      setRelatedQuery((q) => ({ ...q, ...patch }))
                    }
                    onSelectRow={(item) =>
                      navigatePluginPath(
                        buildPurchaseRequestDetailPath(
                          item.branch,
                          item.request_number,
                          basePath,
                        ),
                      )
                    }
                  />
                  {(related.data.protheus_user_ids ?? []).length > 0 ? (() => {
                    const params = new URLSearchParams();
                    for (const pid of related.data.protheus_user_ids) {
                      params.append("requester_user_id", pid);
                    }
                    // Same explicit period semantics as the section
                    // (history floor echoed by the BFF).
                    const dateFrom = (related.data.date_from || "").trim();
                    if (dateFrom) params.set("date_from", dateFrom);
                    const search = `?${params.toString()}`;
                    const href = `${buildPluginPath("purchase_requests", basePath)}${search}`;
                    return (
                      <SuppliesEntityLink
                        href={href}
                        title={C.relatedViewAllTitle}
                        className="sp-entity-link"
                        onNavigate={() =>
                          navigatePluginView("purchase_requests", {
                            basePath,
                            search,
                          })
                        }
                      >
                        {C.relatedViewAll(related.data.total)}
                      </SuppliesEntityLink>
                    );
                  })() : null}
                </>
              ) : (
                <p className="sp-user-profile__note">
                  {related.data?.requester_unmapped
                    ? C.relatedUnmapped
                    : C.relatedEmpty}
                </p>
              )}
            </SuppliesSectionCard>

            <SuppliesSectionCard title={C.accessTitle} subtitle={C.accessSubtitle}>
              {profile.isSelf ? (
                <div className={ACCESS.access}>
                  {profile.isSuperadmin ? (
                    <div className={ACCESS.accessGroup}>
                      <h3 className={ACCESS.accessHeading}>
                        {C.accessContextHeading}
                      </h3>
                      <div className={ACCESS.accessBadges}>
                        <SuppliesStatusBadge label={C.superadmin} variant="warning" />
                      </div>
                    </div>
                  ) : null}
                  <div className={ACCESS.accessGroup}>
                    <h3 className={ACCESS.accessHeading}>
                      {C.accessCapabilitiesHeading}
                    </h3>
                    <div className={ACCESS.accessBadges}>
                      {profile.capabilities?.access || profile.isSuperadmin ? (
                        <SuppliesStatusBadge label={C.capabilityAccess} variant="info" />
                      ) : null}
                      {profile.capabilities?.manage || profile.isSuperadmin ? (
                        <SuppliesStatusBadge label={C.capabilityManage} variant="info" />
                      ) : null}
                      {units.length > 0 ? (
                        <SuppliesStatusBadge
                          label={`${C.unitsLabel}: ${units.join(", ")}`}
                          variant="info"
                        />
                      ) : null}
                    </div>
                  </div>
                  <div className={ACCESS.accessGroup}>
                    <h3 className={ACCESS.accessHeading}>
                      {C.accessPermissionsHeading}
                    </h3>
                    {permissionItems.length > 0 ? (
                      <ul className={ACCESS.accessList}>
                        {permissionItems.map((item) => (
                          <li key={item.code}>
                            <strong>{item.label}</strong>
                            <code>{item.code}</code>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="sp-user-profile__note">{C.accessSelfOnly}</p>
                    )}
                  </div>
                </div>
              ) : isSelf === false ? (
                <p className="sp-user-profile__note">{C.accessSelfOnly}</p>
              ) : (
                <p className="sp-user-profile__note">{C.accessLoading}</p>
              )}
            </SuppliesSectionCard>
          </>
        ) : null
      }
    />
  );
}


