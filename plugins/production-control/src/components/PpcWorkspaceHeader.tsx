import type { ReactNode } from "react";
import { DelpiLogoMark, HelpTooltip } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";

import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { PpcBranch } from "../types";
import { buildPpcHref, navigatePpc, storeBranch } from "../utils/routeParser";

type PpcWorkspaceHeaderProps = {
  title: string;
  subtitle?: string;
  titleHint?: string;
  /** Código em destaque antes do título (ex.: CT selecionado). */
  badge?: string | null;
  /** Chips extras à direita do subtítulo (contagens, etc.). */
  stats?: ReactNode;
  branch: PpcBranch;
  subpluginId: string;
  issueId?: string | null;
  workCenter?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  onRefresh?: () => void;
  refreshBusy?: boolean;
};

export function PpcWorkspaceHeader({
  title,
  subtitle,
  titleHint,
  badge,
  stats,
  branch,
  subpluginId,
  issueId,
  workCenter,
  startDate,
  endDate,
  onRefresh,
  refreshBusy,
}: PpcWorkspaceHeaderProps) {
  const setBranch = (next: PpcBranch) => {
    storeBranch(next);
    navigatePpc(
      buildPpcHref({ subpluginId, branch: next, issueId, workCenter, startDate, endDate }),
    );
  };

  return (
    <header className="ppc-header">
      <div className="ppc-header__inner">
        <div className="ppc-header__identity">
          <span className="ppc-header__logo" aria-hidden="true">
            <DelpiLogoMark className="ppc-header__logo-mark" title="DELPI" />
          </span>
          <div className="ppc-header__identity-text">
            <p className="ppc-header__eyebrow">{copy.productName}</p>
            <div className="ppc-header__title-row">
              {badge ? <span className="ppc-header__badge">{badge}</span> : null}
              <h1 className="ppc-header__title">
                {title}
                <HelpTooltip content={titleHint ?? helpTooltips.problemAnalysis} />
              </h1>
            </div>
            {subtitle ? <p className="ppc-header__subtitle">{subtitle}</p> : null}
            {stats ? <div className="ppc-header__stats">{stats}</div> : null}
          </div>
        </div>

        <div className="ppc-header__actions">
          <div className="ppc-branch" role="group" aria-label={copy.branch.label}>
            <span className="ppc-branch__label">{copy.branch.label}</span>
            <HelpTooltip content={helpTooltips.branch} />
            {(["01", "02"] as const).map((code) => (
              <button
                key={code}
                type="button"
                className={`ppc-branch__btn${branch === code ? " ppc-branch__btn--on" : ""}`}
                aria-pressed={branch === code}
                onClick={() => setBranch(code)}
              >
                {copy.branch[code]}
              </button>
            ))}
          </div>
          {onRefresh ? (
            <button
              type="button"
              className="ppc-icon-btn"
              onClick={onRefresh}
              title={copy.home.refresh}
              disabled={refreshBusy}
            >
              <RefreshCw
                size={16}
                strokeWidth={1.75}
                aria-hidden
                className={refreshBusy ? "ppc-icon-btn__spin" : undefined}
              />
              <span>{copy.home.refresh}</span>
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}
