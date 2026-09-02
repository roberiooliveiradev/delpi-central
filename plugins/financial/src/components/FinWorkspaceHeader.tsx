import type { ReactNode } from "react";
import { DelpiLogoMark, HelpTooltip } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";

import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { FinancialBranch } from "../types";
import { buildFinancialHref, navigateFinancial, storeBranch } from "../utils/routeParser";
import { FinPeriodFilterButton } from "./FinPeriodFilterButton";

const BRANCH_OPTIONS = ["01", "02", "all"] as const;

type FinWorkspaceHeaderProps = {
  title: string;
  subtitle?: string;
  period?: string | null;
  /** ISO YYYY-MM-DD sugeridos no popover quando não há filtro na URL. */
  periodDefaultStart?: string | null;
  periodDefaultEnd?: string | null;
  /** Quando true, exibe botão sutil que abre o filtro de período. */
  periodEditable?: boolean;
  titleHint?: string;
  stats?: ReactNode;
  actions?: ReactNode;
  branch: FinancialBranch;
  subpluginId: string;
  /** Telas consolidadas na origem (inadimplência) escondem o seletor. */
  showBranchSelector?: boolean;
  startDate?: string | null;
  endDate?: string | null;
  granularity?: string | null;
  /** Mês em foco — preserva o detalhamento ao trocar de filial. */
  month?: string | null;
  onRefresh?: () => void;
  refreshBusy?: boolean;
  onPeriodChange?: (next: { startDate: string; endDate: string } | null) => void;
  /** Telas com filtros próprios na URL assumem a navegação ao trocar de filial. */
  onBranchChange?: (next: FinancialBranch) => void;
};

export function FinWorkspaceHeader({
  title,
  subtitle,
  period,
  periodDefaultStart,
  periodDefaultEnd,
  periodEditable = false,
  titleHint,
  stats,
  actions,
  branch,
  subpluginId,
  showBranchSelector = true,
  startDate,
  endDate,
  granularity = null,
  month = null,
  onRefresh,
  refreshBusy,
  onPeriodChange,
  onBranchChange,
}: FinWorkspaceHeaderProps) {
  const setBranch = (next: FinancialBranch) => {
    storeBranch(next);
    if (onBranchChange) {
      onBranchChange(next);
      return;
    }
    navigateFinancial(
      buildFinancialHref({ subpluginId, branch: next, startDate, endDate, granularity, month }),
    );
  };

  return (
    <header className="fin-header">
      <div className="fin-header__inner">
        <div className="fin-header__identity">
          <span className="fin-header__logo" aria-hidden="true">
            <DelpiLogoMark className="fin-header__logo-mark" title="DELPI" />
          </span>
          <div className="fin-header__identity-text">
            <p className="fin-header__eyebrow">{copy.productName}</p>
            <div className="fin-header__title-row">
              <h1 className="fin-header__title">
                {title}
                <HelpTooltip content={titleHint ?? helpTooltips.home} />
              </h1>
            </div>
            {subtitle ? <p className="fin-header__subtitle">{subtitle}</p> : null}
            {period ? (
              <div className="fin-header__period-row">
                <p className="fin-header__period">{period}</p>
                {periodEditable && onPeriodChange ? (
                  <FinPeriodFilterButton
                    startDate={startDate ?? null}
                    endDate={endDate ?? null}
                    defaultStartDate={periodDefaultStart}
                    defaultEndDate={periodDefaultEnd}
                    onApply={onPeriodChange}
                  />
                ) : null}
              </div>
            ) : null}
            {stats ? <div className="fin-header__stats">{stats}</div> : null}
          </div>
        </div>

        <div className="fin-header__actions">
          {actions}
          {showBranchSelector ? (
            <div className="fin-branch" role="group" aria-label={copy.branch.label}>
              <span className="fin-branch__label">{copy.branch.label}</span>
              <HelpTooltip content={helpTooltips.branch} />
              {BRANCH_OPTIONS.map((code) => (
                <button
                  key={code}
                  type="button"
                  className={`fin-branch__btn${branch === code ? " fin-branch__btn--on" : ""}`}
                  aria-pressed={branch === code}
                  onClick={() => setBranch(code)}
                >
                  {copy.branch[code]}
                </button>
              ))}
            </div>
          ) : null}
          {onRefresh ? (
            <button
              type="button"
              className="fin-icon-btn"
              onClick={onRefresh}
              title={copy.refresh}
              disabled={refreshBusy}
            >
              <RefreshCw
                size={16}
                strokeWidth={1.75}
                aria-hidden
                className={refreshBusy ? "fin-icon-btn__spin" : undefined}
              />
              <span>{copy.refresh}</span>
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}
