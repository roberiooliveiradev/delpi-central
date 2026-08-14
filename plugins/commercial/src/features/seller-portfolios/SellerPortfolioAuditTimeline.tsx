import { useMemo, useState, type ReactNode } from "react";
import { SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialActivityTimeline,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialStateBanner,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import {
  PORTFOLIO_AUDIT_CONTENT,
  type PortfolioAuditEventFilter,
} from "../../content/portfolioAuditContent";
import type { SellerPortfolioAuditEvent } from "../../types/portfolio";
import {
  filterPortfolioAuditEvents,
  mapPortfolioAuditEventsToTimelineItems,
} from "../../utils/portfolioAuditTimeline";

type SellerPortfolioAuditTimelineProps = {
  loading: boolean;
  error: string | null;
  events: SellerPortfolioAuditEvent[];
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
  onRetry: () => void;
  title?: string;
  subtitle?: string;
  hint?: string;
  /** Conteúdo acima da timeline (ex.: seletor de carteira em Minha Carteira). */
  leading?: ReactNode;
  /** Quando false, só renderiza `leading` (aguardando escolha de carteira). */
  showTimeline?: boolean;
  /** Minha Carteira: seção secundária, colapsável. */
  collapsible?: boolean;
  /** Estado inicial quando `collapsible` (default: aberto). */
  defaultOpen?: boolean;
};

const FILTER_OPTIONS = (
  Object.entries(PORTFOLIO_AUDIT_CONTENT.filters) as Array<
    [PortfolioAuditEventFilter, string]
  >
).map(([value, label]) => ({ value, label }));

export function SellerPortfolioAuditTimeline({
  loading,
  error,
  events,
  directoryLabelFor,
  onRetry,
  title = PORTFOLIO_AUDIT_CONTENT.title,
  subtitle = PORTFOLIO_AUDIT_CONTENT.subtitle,
  hint = CM_HELP.sellerPortfolios.auditTimeline,
  leading = null,
  showTimeline = true,
  collapsible = false,
  defaultOpen = true,
}: SellerPortfolioAuditTimelineProps) {
  const [eventFilter, setEventFilter] =
    useState<PortfolioAuditEventFilter>("all");

  const filteredEvents = useMemo(
    () => filterPortfolioAuditEvents(events, eventFilter),
    [events, eventFilter],
  );

  const items = useMemo(
    () =>
      mapPortfolioAuditEventsToTimelineItems(filteredEvents, directoryLabelFor),
    [directoryLabelFor, filteredEvents],
  );
  const hasSourceData = events.length > 0;
  const hasData = items.length > 0;
  const emptyMessage =
    hasSourceData && !hasData
      ? PORTFOLIO_AUDIT_CONTENT.emptyFiltered
      : PORTFOLIO_AUDIT_CONTENT.empty;

  const filterToolbar = (
    <SegmentToggle
      prefix="cm"
      size="sm"
      ariaLabel={PORTFOLIO_AUDIT_CONTENT.filterAriaLabel}
      idPrefix="cm-portfolio-audit-filter"
      options={FILTER_OPTIONS}
      value={eventFilter}
      onChange={setEventFilter}
    />
  );

  return (
    <CommercialSectionCard
      title={title}
      subtitle={subtitle}
      hint={hint}
      collapsible={collapsible}
      defaultOpen={defaultOpen}
    >
      {leading}

      {showTimeline && loading && !hasSourceData ? (
        <CommercialLoadingCard title={PORTFOLIO_AUDIT_CONTENT.loading} variant="panel" />
      ) : null}

      {showTimeline && error ? (
        <CommercialStateBanner variant="error">
          <p>{error}</p>
          <CommercialActionButton variant="ghost" onClick={onRetry} disabled={loading}>
            {PORTFOLIO_AUDIT_CONTENT.errorRetry}
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {showTimeline && !error && (hasSourceData || !loading) ? (
        <CommercialActivityTimeline
          toolbar={filterToolbar}
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
          emptyMessage={emptyMessage}
          aria-label={PORTFOLIO_AUDIT_CONTENT.ariaLabel}
        />
      ) : null}

      {!showTimeline && leading ? (
        <p className="cm-cell-muted" role="status">
          {PORTFOLIO_AUDIT_CONTENT.selectPortfolioEmpty}
        </p>
      ) : null}
    </CommercialSectionCard>
  );
}
