import { useEffect, useMemo, useState, type ReactNode } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import {
  BookOpen,
  Home,
  LayoutDashboard,
  ShoppingCart,
} from "lucide-react";

import { getUserProfile, patchUserProfile, type SuppliesUserProfile } from "../../api/userProfileApi";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import {
  buildPluginPath,
  normalizeBasePath,
  SUPPLIES_BASE_PATH,
} from "../../app/pluginRoutes";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import { useMyPersonProfile } from "../../app/useMyPersonProfile";
import {
  SuppliesActionButton,
  SuppliesAvatar,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { USER_PROFILE_CONTENT as C } from "./userProfileContent";

type UserProfilePageProps = {
  basePath: string;
  userId: string;
};

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
  const isSelf = Boolean(session.userId && session.userId === userId);
  const { profile: personProfile, photoUrl } = useMyPersonProfile(isSelf);
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
    if (caps.analytics) {
      items.push({
        id: "overview",
        label: C.shortcutOverview,
        icon: <LayoutDashboard size={16} strokeWidth={1.75} aria-hidden="true" />,
        onSelect: () => navigatePluginView("overview", { basePath }),
      });
    }
    if (caps.purchaseRequests) {
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

  return (
    <div className="sp-page-stack sp-user-profile" aria-label={C.pageAriaLabel}>
      <SuppliesPagePath
        back={{
          label: back.label,
          href: back.href,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(back.href);
          },
        }}
        items={[]}
        current={profile?.name || "Perfil"}
      />

      {loading ? <SuppliesStateBanner>{C.loading}</SuppliesStateBanner> : null}

      {forbidden ? (
        <SuppliesStateBanner variant="error">{C.forbidden}</SuppliesStateBanner>
      ) : null}

      {error ? (
        <div className="sp-user-profile__error">
          <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
          <SuppliesActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
            {C.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      {!loading && profile ? (
        <>
          <SuppliesPageHero
            eyebrow="Portal Suprimentos"
            title={
              <>
                {profile.name}{" "}
                <HelpTooltip content={SP_HELP.userProfile} ariaLabel={C.helpAriaLabel} />
              </>
            }
            description={profile.email || C.hostProfileNote}
            badge={
              <>
                <SuppliesStatusBadge
                  label={profile.isSelf ? C.badgeSelf : C.badgeAdminView}
                  variant={profile.isSelf ? "success" : "info"}
                />
                {units.length > 0 ? (
                  <SuppliesStatusBadge
                    label={`${C.unitsLabel}: ${units.join(", ")}`}
                    variant="info"
                  />
                ) : null}
              </>
            }
          />

          <div className="sp-user-profile__grid">
            <SuppliesSectionCard title={C.identityTitle} subtitle={C.identitySubtitle}>
              <div className="sp-user-profile__identity">
                <SuppliesAvatar
                  name={profile.name}
                  src={isSelf ? photoUrl : null}
                  size="lg"
                />
                <dl>
                  <div>
                    <dt>{C.nameLabel}</dt>
                    <dd>{profile.name}</dd>
                  </div>
                  <div>
                    <dt>{C.emailLabel}</dt>
                    <dd>{profile.email || "—"}</dd>
                  </div>
                  {isSelf ? (
                    <>
                      <div>
                        <dt>{C.jobTitleLabel}</dt>
                        <dd>{personProfile?.job_title?.trim() || "—"}</dd>
                      </div>
                      <div>
                        <dt>{C.phoneLabel}</dt>
                        <dd>{personProfile?.phone_e164?.trim() || "—"}</dd>
                      </div>
                      <div>
                        <dt>{C.mobileLabel}</dt>
                        <dd>{personProfile?.mobile_e164?.trim() || "—"}</dd>
                      </div>
                      <div>
                        <dt>{C.whatsappLabel}</dt>
                        <dd>{personProfile?.whatsapp_e164?.trim() || "—"}</dd>
                      </div>
                    </>
                  ) : null}
                </dl>
              </div>
              <p className="sp-user-profile__note">{C.hostProfileNote}</p>
            </SuppliesSectionCard>

            <SuppliesSectionCard title={C.shortcutsTitle} subtitle={C.shortcutsSubtitle}>
              <ul className="sp-user-profile__shortcuts">
                {shortcuts.map((item) => (
                  <li key={item.id}>
                    <button type="button" className="sp-home__chip" onClick={item.onSelect}>
                      {item.icon}
                      <span>{item.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </SuppliesSectionCard>
          </div>

          <SuppliesSectionCard
            title={C.preferencesTitle}
            subtitle={C.preferencesSubtitle}
            hint={SP_HELP.userProfilePrefs}
          >
            {profile.isSelf ? (
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
            ) : (
              <p className="sp-user-profile__note">{C.preferencesOther}</p>
            )}
          </SuppliesSectionCard>

          <SuppliesSectionCard title={C.accessTitle} subtitle={C.accessSubtitle}>
            {profile.isSelf && profile.capabilities ? (
              <ul className="sp-user-profile__caps">
                {Object.entries(profile.capabilities).map(([key, enabled]) => (
                  <li key={key}>
                    <SuppliesStatusBadge
                      label={`${key}: ${enabled ? "sim" : "não"}`}
                      variant={enabled ? "success" : "neutral"}
                    />
                  </li>
                ))}
                <li>
                  <SuppliesStatusBadge
                    label={`${C.unitsLabel}: ${units.join(", ") || "—"}`}
                    variant="info"
                  />
                </li>
              </ul>
            ) : (
              <p className="sp-user-profile__note">{C.accessOther}</p>
            )}
          </SuppliesSectionCard>
        </>
      ) : null}
    </div>
  );
}

export function buildUserProfilePath(
  userId: string,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const path = `${base}/users/${encodeURIComponent(userId)}`;
  if (!search) return path;
  const normalized = search.startsWith("?") ? search : `?${search}`;
  return `${path}${normalized}`;
}

export function buildSelfProfileSearch(basePath: string): string {
  const returnTo = buildPluginPath("home", basePath);
  const params = new URLSearchParams();
  params.set("returnTo", returnTo);
  params.set("returnLabel", C.backFallback);
  return `?${params.toString()}`;
}
