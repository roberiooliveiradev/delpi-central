import {
  CommercialActionButton,
  CommercialActivityTimeline,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { PORTFOLIO_AUDIT_CONTENT } from "../../content/portfolioAuditContent";
import type { SellerPortfolioAuditEvent } from "../../types/portfolio";
import { mapPortfolioAuditEventsToTimelineItems } from "../../utils/portfolioAuditTimeline";

type SellerPortfolioAuditTimelineProps = {
  loading: boolean;
  error: string | null;
  events: SellerPortfolioAuditEvent[];
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
  onRetry: () => void;
};

export function SellerPortfolioAuditTimeline({
  loading,
  error,
  events,
  directoryLabelFor,
  onRetry,
}: SellerPortfolioAuditTimelineProps) {
  const items = mapPortfolioAuditEventsToTimelineItems(events);
  const hasData = items.length > 0;

  return (
    <CommercialSectionCard
      title={PORTFOLIO_AUDIT_CONTENT.title}
      subtitle={PORTFOLIO_AUDIT_CONTENT.subtitle}
      hint={CM_HELP.sellerPortfolios.auditTimeline}
    >
      {loading && !hasData ? (
        <CommercialLoadingCard title={PORTFOLIO_AUDIT_CONTENT.loading} variant="panel" />
      ) : null}

      {error ? (
        <CommercialStateBanner variant="error">
          <p>{error}</p>
          <CommercialActionButton variant="ghost" onClick={onRetry} disabled={loading}>
            {PORTFOLIO_AUDIT_CONTENT.errorRetry}
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {!error && (hasData || !loading) ? (
        <CommercialActivityTimeline
          items={items.map((item) => ({
            id: item.id,
            title: item.title,
            occurredAt: item.occurredAt,
            timeLabel: item.timeLabel,
            detail: item.detail,
            meta: item.actorUserId
              ? `${PORTFOLIO_AUDIT_CONTENT.actorPrefix} ${directoryLabelFor(item.actorUserId)}`
              : undefined,
            tone: item.tone,
          }))}
          emptyMessage={PORTFOLIO_AUDIT_CONTENT.empty}
          aria-label={PORTFOLIO_AUDIT_CONTENT.ariaLabel}
        />
      ) : null}
    </CommercialSectionCard>
  );
}
