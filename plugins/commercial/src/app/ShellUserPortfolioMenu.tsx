import { useCallback, useMemo, useRef, useState } from "react";
import {
  AnchoredPanelPortal,
  ContextMenuItem,
} from "@delpi/plugin-ui/index";
import { BriefcaseBusiness, ChevronDown } from "lucide-react";

import { CommercialAvatar } from "./commercialUi";
import { navigatePluginView } from "./pluginNavigation";
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
 * Slot da TopBar (ex-Escopo): avatar + nome + atalho para Minha Carteira filtrada.
 * 0 carteiras → estático; 1 → navega direto; N → menu de seleção.
 */
export function ShellUserPortfolioMenu({
  basePath,
  displayName,
}: ShellUserPortfolioMenuProps) {
  const { myPortfolios, setSellerIdFilter } = usePortfolioScope();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const copy = SHELL_NAV_CONTENT.userMenu;

  const mode = useMemo(
    () => resolveShellUserPortfolioNavMode(myPortfolios),
    [myPortfolios],
  );

  const label = (displayName ?? "").trim() || copy.nameFallback;
  const portfolioIds = useMemo(
    () =>
      mode.kind === "menu"
        ? mode.portfolios.map((portfolio) => portfolio.id)
        : mode.kind === "direct"
          ? [mode.portfolio.id]
          : [],
    [mode],
  );

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

  const onTriggerClick = useCallback(() => {
    if (mode.kind === "disabled") return;
    if (mode.kind === "direct") {
      goToPortfolio(mode.portfolio);
      return;
    }
    setOpen((current) => !current);
  }, [goToPortfolio, mode]);

  const interactive = mode.kind !== "disabled";
  const ariaLabel =
    mode.kind === "disabled"
      ? copy.disabledAriaLabel
      : mode.kind === "direct"
        ? copy.directAriaLabel.replace("{name}", mode.portfolio.displayName)
        : open
          ? copy.menuCloseAriaLabel
          : copy.menuOpenAriaLabel;

  return (
    <div
      ref={rootRef}
      className={[
        "cm-shell-user",
        interactive ? null : "cm-shell-user--disabled",
        open ? "cm-shell-user--open" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {interactive ? (
        <button
          type="button"
          className="cm-shell-user__trigger"
          aria-label={ariaLabel}
          aria-haspopup={mode.kind === "menu" ? "menu" : undefined}
          aria-expanded={mode.kind === "menu" ? open : undefined}
          onClick={onTriggerClick}
        >
          <CommercialAvatar name={label} size="sm" alt="" />
          <span className="cm-shell-user__name">{label}</span>
          {mode.kind === "menu" ? (
            <ChevronDown
              className="cm-shell-user__chevron"
              size={16}
              strokeWidth={1.75}
              aria-hidden="true"
            />
          ) : null}
        </button>
      ) : (
        <div className="cm-shell-user__trigger" aria-label={ariaLabel}>
          <CommercialAvatar name={label} size="sm" alt="" />
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
