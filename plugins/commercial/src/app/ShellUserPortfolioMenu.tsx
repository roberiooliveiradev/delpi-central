import { useCallback, useEffect, useMemo, useState } from "react";
import { BriefcaseBusiness, ChevronDown } from "lucide-react";

import { httpGetBlob } from "../api/httpClient";
import {
  getUserProfile,
  userProfilePhotoAbsoluteUrl,
} from "../api/userProfileApi";
import { CommercialTopBarUserIdentity } from "./commercialUi";
import { navigatePluginView } from "./pluginNavigation";
import { profileLinkTitle } from "../content/entityLinkHints";
import { usePortfolioScope } from "./PortfolioScopeContext";
import {
  buildShellPortfolioCustomersSearch,
  resolveShellUserPortfolioNavMode,
  type ShellUserPortfolioOption,
} from "./shellUserPortfolioNav";
import { SHELL_NAV_CONTENT } from "../content/shellNav";

/** Canonical Minha DELPI self-profile (Portal host). Commercial user pages stay for directory/others. */
const HOST_SELF_PROFILE_PATH = "/profile";

type ShellUserPortfolioMenuProps = {
  basePath: string;
  /** Nome completo para avatar + rótulo (fallback se ausente). */
  displayName: string | null;
};

/**
 * Adapter Comercial: chrome shared (TopBarUserIdentity) + domínio de carteira.
 * Avatar → `/profile` (identidade canônica). Nome/chevron → Minha Carteira (0/1/N).
 */
export function ShellUserPortfolioMenu({
  basePath,
  displayName,
}: ShellUserPortfolioMenuProps) {
  const { myPortfolios, setSellerIdFilter, currentUserId } = usePortfolioScope();
  const [open, setOpen] = useState(false);
  const [photoObjectUrl, setPhotoObjectUrl] = useState<string | null>(null);
  const copy = SHELL_NAV_CONTENT.userMenu;

  const mode = useMemo(
    () => resolveShellUserPortfolioNavMode(myPortfolios),
    [myPortfolios],
  );

  const label = (displayName ?? "").trim() || copy.nameFallback;
  const userId = (currentUserId || "").trim();
  const portfolioIds = useMemo(
    () =>
      mode.kind === "menu"
        ? mode.portfolios.map((portfolio) => portfolio.id)
        : mode.kind === "direct"
          ? [mode.portfolio.id]
          : [],
    [mode],
  );

  useEffect(() => {
    let revoked: string | null = null;
    let cancelled = false;
    if (!userId) {
      setPhotoObjectUrl(null);
      return undefined;
    }
    const controller = new AbortController();
    void getUserProfile(userId, controller.signal)
      .then(async (profile) => {
        if (cancelled || !profile.has_photo) {
          if (!cancelled) setPhotoObjectUrl(null);
          return;
        }
        const blob = await httpGetBlob(userProfilePhotoAbsoluteUrl(userId), {
          signal: controller.signal,
        });
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
      controller.abort();
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [userId]);

  const goToHostProfile = useCallback(() => {
    setOpen(false);
    window.location.assign(HOST_SELF_PROFILE_PATH);
  }, []);

  const goToPortfolio = useCallback(
    (portfolio: ShellUserPortfolioOption) => {
      setOpen(false);
      setSellerIdFilter(portfolioIds.length > 1 ? portfolio.id : null);
      navigatePluginView("customers", {
        basePath,
        search: buildShellPortfolioCustomersSearch(portfolio.id, portfolioIds),
      });
    },
    [basePath, portfolioIds, setSellerIdFilter],
  );

  const onPortfolioClick = useCallback(() => {
    if (mode.kind === "disabled") return;
    if (mode.kind === "direct") {
      goToPortfolio(mode.portfolio);
      return;
    }
    setOpen((current) => !current);
  }, [goToPortfolio, mode]);

  const portfolioInteractive = mode.kind !== "disabled";
  const portfolioAriaLabel =
    mode.kind === "disabled"
      ? copy.disabledAriaLabel
      : mode.kind === "direct"
        ? copy.directAriaLabel.replace("{name}", mode.portfolio.displayName)
        : open
          ? copy.menuCloseAriaLabel
          : copy.menuOpenAriaLabel;

  const profileTitle = profileLinkTitle(label);

  const menuItems =
    mode.kind === "menu"
      ? mode.portfolios.map((portfolio) => ({
          id: portfolio.id,
          label: portfolio.displayName,
          icon: BriefcaseBusiness,
          onSelect: () => goToPortfolio(portfolio),
        }))
      : undefined;

  const labelEnd =
    mode.kind === "menu" ? (
      <ChevronDown size={16} strokeWidth={1.75} aria-hidden="true" />
    ) : mode.kind === "direct" ? (
      <BriefcaseBusiness size={16} strokeWidth={1.75} aria-hidden="true" />
    ) : null;

  return (
    <CommercialTopBarUserIdentity
      displayName={displayName}
      fallbackLabel={copy.nameFallback}
      avatarUrl={photoObjectUrl}
      portalScopeClassName="dashboard-commercial"
      avatarHref={HOST_SELF_PROFILE_PATH}
      onAvatarNavigate={goToHostProfile}
      avatarTitle={profileTitle}
      onLabelClick={portfolioInteractive ? onPortfolioClick : undefined}
      labelAriaLabel={portfolioAriaLabel}
      labelHasPopup={mode.kind === "menu" ? "menu" : false}
      labelExpanded={mode.kind === "menu" ? open : undefined}
      labelDisabled={!portfolioInteractive}
      labelEnd={labelEnd}
      menuItems={menuItems}
      menuAriaLabel={copy.menuAriaLabel}
      open={mode.kind === "menu" ? open : false}
      onOpenChange={mode.kind === "menu" ? setOpen : undefined}
    />
  );
}
