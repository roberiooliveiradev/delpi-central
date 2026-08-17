import { CommercialStatusBadge } from "../../../app/commercialUi";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../../content/portfolioCoverageContent";
import type { CustomerSharedCoverageItem } from "../../../types/portfolio";
import {
  formatAlsoInPortfolios,
  portfolioDisplayNames,
} from "../../../utils/portfolioCoverage";

type CustomerSharedCoverageBadgeProps = {
  coverage?: CustomerSharedCoverageItem | null;
  compact?: boolean;
};

/**
 * Badge «Compartilhado» + «Também em: …» (E6.4).
 */
export function CustomerSharedCoverageBadge({
  coverage,
  compact = false,
}: CustomerSharedCoverageBadgeProps) {
  if (!coverage?.shared) return null;
  const names = portfolioDisplayNames(coverage.also_in_portfolios);
  const alsoIn = formatAlsoInPortfolios(names);
  if (!alsoIn) return null;

  return (
    <span
      className={
        compact
          ? "cm-row-actions cm-customer-shared-coverage cm-customer-shared-coverage--compact"
          : "cm-row-actions cm-customer-shared-coverage"
      }
    >
      <CommercialStatusBadge
        label={PORTFOLIO_COVERAGE_CONTENT.sharedBadge}
        variant="warning"
      />
      <span className="cm-customer-shared-coverage__also-in">{alsoIn}</span>
    </span>
  );
}
