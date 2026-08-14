import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  ContextMenuItem,
} from "@delpi/plugin-ui/index";
import { BriefcaseBusiness, ChevronDown } from "lucide-react";

import { httpGetBlob } from "../api/httpClient";
import {
  getUserProfile,
  userProfilePhotoAbsoluteUrl,
} from "../api/userProfileApi";
import { CommercialAvatar } from "./commercialUi";
import { navigatePluginView, navigateUserProfile } from "./pluginNavigation";
import { currentReturnNav } from "./commercialNavigationReturn";
import { usePortfolioScope } from "./PortfolioScopeContext";
import {
  buildShellPortfolioCustomersSearch,
  resolveShellUserPortfolioNavMode,
  type ShellUserPortfolioOption,
} from "./shellUserPortfolioNav";
import { SHELL_NAV_CONTENT } from "../content/shellNav";

type ShellUserPortfolioMenuProps = {
  basePath: string;
  /** Nome completo para avatar + rótulo (fallback se ausente). */
  displayName: string | null;
};

/**
 * Slot da TopBar: clique no avatar (com ou sem foto) abre o perfil.
 * Zoom da foto fica só na página de perfil. Nome/chevron abre Minha Carteira.
 */
export function ShellUserPortfolioMenu({
  basePath,
  displayName,
}: ShellUserPortfolioMenuProps) {
  const { myPortfolios, setSellerIdFilter, currentUserId } = usePortfolioScope();
  const [open, setOpen] = useState(false);
  const [photoObjectUrl, setPhotoObjectUrl] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
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

  const goToProfile = useCallback(() => {
    if (!userId) return;
    setOpen(false);
    navigateUserProfile(userId, {
      basePath,
      returnNav: currentReturnNav("Portal Comercial"),
    });
  }, [basePath, userId]);

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

  const avatar = (
    <CommercialAvatar
      name={label}
      size="sm"
      alt=""
      src={photoObjectUrl}
      previewable={false}
      portalScopeClassName="dashboard-commercial"
    />
  );

  return (
    <div
      ref={rootRef}
      className={[
        "cm-shell-user",
        portfolioInteractive ? null : "cm-shell-user--disabled",
        open ? "cm-shell-user--open" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {userId ? (
        <button
          type="button"
          className="cm-shell-user__profile"
          aria-label={copy.profileAriaLabel}
          onClick={goToProfile}
        >
          {avatar}
        </button>
      ) : (
        <span className="cm-shell-user__profile cm-shell-user__profile--static">
          {avatar}
        </span>
      )}

      {portfolioInteractive ? (
        <button
          type="button"
          className="cm-shell-user__portfolio"
          aria-label={portfolioAriaLabel}
          aria-haspopup={mode.kind === "menu" ? "menu" : undefined}
          aria-expanded={mode.kind === "menu" ? open : undefined}
          onClick={onPortfolioClick}
        >
          <span className="cm-shell-user__name">{label}</span>
          {mode.kind === "menu" ? (
            <ChevronDown
              className="cm-shell-user__chevron"
              size={16}
              strokeWidth={1.75}
              aria-hidden="true"
            />
          ) : (
            <BriefcaseBusiness
              className="cm-shell-user__portfolio-icon"
              size={16}
              strokeWidth={1.75}
              aria-hidden="true"
            />
          )}
        </button>
      ) : (
        <div className="cm-shell-user__portfolio" aria-label={portfolioAriaLabel}>
          <span className="cm-shell-user__name">{label}</span>
        </div>
      )}

      {mode.kind === "menu" ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          className="delpi-ui-context-menu"
          variant="bare"
          role="menu"
          aria-label={copy.menuAriaLabel}
          preferredPlacement="bottom"
          gap={6}
          portalScopeClassName="dashboard-commercial"
          onDismiss={() => setOpen(false)}
        >
          {mode.portfolios.map((portfolio) => (
            <ContextMenuItem
              key={portfolio.id}
              label={portfolio.displayName}
              icon={BriefcaseBusiness}
              onSelect={() => goToPortfolio(portfolio)}
            />
          ))}
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
