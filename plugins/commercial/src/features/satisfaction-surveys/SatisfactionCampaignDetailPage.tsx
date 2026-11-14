import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { getSatisfactionCampaign } from "../../api/satisfactionSurveysApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialSectionHintLabel,
  CommercialStateBanner,
  CommercialUnderlineNav,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type { SatisfactionCampaign } from "../../types/satisfactionSurvey";
import { CampaignDataTab } from "./CampaignDataTab";
import { CampaignMessageTab } from "./CampaignMessageTab";
import { CampaignParticipantsTab } from "./CampaignParticipantsTab";
import { formatSurveyPeriod } from "./satisfactionDates";
import { SatisfactionPagePath } from "./SatisfactionPagePath";
import { SatisfactionStatusBadge } from "./SatisfactionStatusBadge";

type CampaignTab = "participants" | "message" | "data";

type SatisfactionCampaignDetailPageProps = {
  basePath: string;
  campaignId: string;
};

/** UI-02B — detalhe da campanha: Participantes | Mensagem padrão | Dados. */
export function SatisfactionCampaignDetailPage({
  basePath,
  campaignId,
}: SatisfactionCampaignDetailPageProps) {
  const copy = SATISFACTION_CONTENT.detail;
  const listCopy = SATISFACTION_CONTENT.list;
  const { canManageSatisfaction, loading: scopeLoading } = usePortfolioScope();
  const [campaign, setCampaign] = useState<SatisfactionCampaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [tab, setTab] = useState<CampaignTab>("participants");

  useEffect(() => {
    if (!canManageSatisfaction) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getSatisfactionCampaign(campaignId, controller.signal)
      .then((item) => {
        if (!controller.signal.aborted) setCampaign(item);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setCampaign(null);
        setError(err instanceof Error ? err.message : copy.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [campaignId, canManageSatisfaction, copy.loadError, reloadKey]);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  if (!scopeLoading && !canManageSatisfaction) {
    return (
      <section className="cm-page-stack">
        <SatisfactionPagePath
          basePath={basePath}
          ariaLabel={listCopy.title}
          showListLink
          current={copy.backToList}
        />
        <CommercialEmptyState title={listCopy.forbiddenTitle} message={listCopy.forbiddenMessage} />
      </section>
    );
  }

  const pathCurrent = campaign?.name ?? copy.loading;

  return (
    <section className="cm-page-stack cm-satisfaction-campaign">
      <SatisfactionPagePath
        basePath={basePath}
        ariaLabel={campaign?.name ?? listCopy.title}
        showListLink
        current={pathCurrent}
      />

      {loading && !campaign ? <CommercialLoadingCard title={copy.loading} variant="panel" /> : null}

      {error && !campaign ? (
        <CommercialStateBanner variant="error">
          {error}{" "}
          <CommercialActionButton variant="ghost" onClick={reload}>
            {copy.refresh}
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {campaign ? (
        <>
          <CommercialPageHero
            aria-label={campaign.name}
            title={
              <CommercialSectionHintLabel
                label={campaign.name}
                hint={CM_HELP.satisfactionSurveys.detailTabs}
              />
            }
            description={copy.heroDescription(
              formatSurveyPeriod(campaign.starts_at, campaign.ends_at),
            )}
            actions={
              <div className="cm-satisfaction-actions">
                <SatisfactionStatusBadge status={campaign.status} />
                <CommercialActionButton variant="ghost" onClick={reload}>
                  <RefreshCw size={16} aria-hidden="true" /> {copy.refresh}
                </CommercialActionButton>
              </div>
            }
          />
          <CommercialStateBanner>{listCopy.partialScope}</CommercialStateBanner>

          <CommercialUnderlineNav
            mode="tabs"
            activeId={tab}
            aria-label={copy.tabsAriaLabel}
            items={[
              { id: "participants", label: copy.tabParticipants, onSelect: () => setTab("participants") },
              { id: "message", label: copy.tabMessage, onSelect: () => setTab("message") },
              { id: "data", label: copy.tabData, onSelect: () => setTab("data") },
            ]}
          />

          {tab === "participants" ? (
            <CampaignParticipantsTab
              basePath={basePath}
              campaign={campaign}
              onParticipantsChanged={reload}
            />
          ) : null}
          {tab === "message" ? (
            <CampaignMessageTab
              campaign={campaign}
              onCampaignUpdated={setCampaign}
              onReloadRequested={reload}
            />
          ) : null}
          {tab === "data" ? (
            <CampaignDataTab campaign={campaign} onCampaignUpdated={setCampaign} />
          ) : null}
        </>
      ) : null}
    </section>
  );
}
