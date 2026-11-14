import { Copy, Pencil, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import {
  getSatisfactionCampaign,
  getSatisfactionRecipient,
  updateSatisfactionRecipientContact,
} from "../../api/satisfactionSurveysApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
} from "../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type {
  SatisfactionCampaign,
  SatisfactionRecipient,
} from "../../types/satisfactionSurvey";
import { CustomerAvatar } from "../customers/components/CustomerAvatar";
import { copyToClipboard } from "./clipboard";
import { InvitePreview, type InvitePreviewMode } from "./InvitePreview";
import { buildInviteHtml, buildMessengerText } from "./inviteMessage";
import { absolutizeInvite } from "./inviteLink";
import { RecipientContactDialog, type RecipientContactValues } from "./RecipientContactDialog";
import { recipientCompanyLabel } from "./satisfactionFilters";
import { SatisfactionPagePath } from "./SatisfactionPagePath";

type SatisfactionRecipientDetailPageProps = {
  basePath: string;
  campaignId: string;
  recipientId: string;
};

type CopyKind = "message" | "subject" | "link";

/** UI-02C — participante: contato do convite e convite personalizado para copiar. */
export function SatisfactionRecipientDetailPage({
  basePath,
  campaignId,
  recipientId,
}: SatisfactionRecipientDetailPageProps) {
  const copy = SATISFACTION_CONTENT.recipient;
  const listCopy = SATISFACTION_CONTENT.list;
  const { canManageSatisfaction, loading: scopeLoading } = usePortfolioScope();
  const { notifySuccess, notifyWarning } = useCommercialFloatingNotice();

  const [recipient, setRecipient] = useState<SatisfactionRecipient | null>(null);
  const [campaign, setCampaign] = useState<SatisfactionCampaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [previewMode, setPreviewMode] = useState<InvitePreviewMode>("email");
  const [contactOpen, setContactOpen] = useState(false);
  const [savingContact, setSavingContact] = useState(false);
  const [contactError, setContactError] = useState<string | null>(null);
  const [manualCopy, setManualCopy] = useState<{ kind: CopyKind; text: string } | null>(null);

  useEffect(() => {
    if (!canManageSatisfaction) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    Promise.all([
      getSatisfactionRecipient(campaignId, recipientId, controller.signal),
      getSatisfactionCampaign(campaignId, controller.signal),
    ])
      .then(([recipientData, campaignData]) => {
        if (controller.signal.aborted) return;
        setRecipient(recipientData);
        setCampaign(campaignData);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setRecipient(null);
        setError(err instanceof Error ? err.message : copy.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [campaignId, recipientId, canManageSatisfaction, copy.loadError, reloadKey]);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  const origin = typeof window === "undefined" ? "" : window.location.origin;
  const invite = recipient?.invite ? absolutizeInvite(recipient.invite, origin) : null;

  const runCopy = async (kind: CopyKind) => {
    if (!invite) return;
    const payload =
      kind === "subject"
        ? { text: invite.subject }
        : kind === "link"
          ? { text: invite.link_url }
          : previewMode === "messenger"
            ? { text: buildMessengerText(invite.body) }
            : {
                text: buildMessengerText(invite.body),
                html: buildInviteHtml(invite.body, { linkify: true }),
              };
    const ok = await copyToClipboard(payload);
    if (ok) {
      setManualCopy(null);
      notifySuccess(
        kind === "subject"
          ? copy.copiedSubject
          : kind === "link"
            ? copy.copiedLink
            : copy.copiedMessage,
      );
      return;
    }
    // Não confirma sucesso: oferece o texto para cópia manual.
    setManualCopy({ kind, text: payload.text });
    notifyWarning(copy.copyFailed);
  };

  const submitContact = async (values: RecipientContactValues) => {
    if (!recipient) return;
    setSavingContact(true);
    setContactError(null);
    try {
      await updateSatisfactionRecipientContact(campaignId, recipientId, {
        version: recipient.version,
        contact_name: values.contactName,
        contact_email: values.contactEmail,
      });
      notifySuccess(copy.contactSaved);
      setContactOpen(false);
      reload();
    } catch (err: unknown) {
      setContactError(err instanceof Error ? err.message : copy.loadError);
    } finally {
      setSavingContact(false);
    }
  };

  if (!scopeLoading && !canManageSatisfaction) {
    return (
      <section className="cm-page-stack">
        <SatisfactionPagePath
          basePath={basePath}
          ariaLabel={listCopy.title}
          showListLink
          current={SATISFACTION_CONTENT.detail.backToList}
        />
        <CommercialEmptyState title={listCopy.forbiddenTitle} message={listCopy.forbiddenMessage} />
      </section>
    );
  }

  const companyLabel = recipient ? recipientCompanyLabel(recipient) : copy.loading;

  return (
    <section className="cm-page-stack cm-satisfaction-recipient">
      <SatisfactionPagePath
        basePath={basePath}
        ariaLabel={companyLabel}
        showListLink
        campaign={{ id: campaignId, name: campaign?.name ?? SATISFACTION_CONTENT.detail.loading }}
        current={companyLabel}
      />

      {loading && !recipient ? <CommercialLoadingCard title={copy.loading} variant="panel" /> : null}

      {error && !recipient ? (
        <CommercialStateBanner variant="error">
          {error}{" "}
          <CommercialActionButton variant="ghost" onClick={reload}>
            {copy.refresh}
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {recipient ? (
        <>
          <CommercialPageHero
            aria-label={companyLabel}
            title={
              <span className="cm-row-actions">
                <CustomerAvatar
                  code={recipient.customer_code}
                  store={recipient.customer_store}
                  name={(recipient.customer_name ?? "").trim() || recipient.customer_code}
                  size="md"
                  previewable={false}
                />
                <span>{(recipient.customer_name ?? "").trim() || recipient.customer_code}</span>
              </span>
            }
            description={copy.heroDescription(
              `${recipient.customer_code}/${recipient.customer_store}`,
            )}
            actions={
              <div className="cm-satisfaction-actions">
                {recipient.status === "responded" ? (
                  <CommercialStatusBadge
                    label={SATISFACTION_CONTENT.participants.statusResponded}
                    variant="success"
                  />
                ) : (
                  <CommercialStatusBadge
                    label={SATISFACTION_CONTENT.participants.statusPending}
                    variant="warning"
                  />
                )}
                <CommercialActionButton variant="ghost" onClick={reload}>
                  <RefreshCw size={16} aria-hidden="true" /> {copy.refresh}
                </CommercialActionButton>
              </div>
            }
          />

          {recipient.status === "responded" ? (
            <CommercialStateBanner>{copy.responded}</CommercialStateBanner>
          ) : null}

          <CommercialSectionCard
            title={copy.contactTitle}
            actions={
              <CommercialActionButton
                variant="default"
                onClick={() => {
                  setContactError(null);
                  setContactOpen(true);
                }}
              >
                <Pencil size={16} aria-hidden="true" /> {copy.editContact}
              </CommercialActionButton>
            }
          >
            <dl className="cm-satisfaction-fields">
              <div className="cm-satisfaction-fields__item">
                <dt>{copy.contactName}</dt>
                <dd>{recipient.contact_name?.trim() || copy.contactEmpty}</dd>
              </div>
              <div className="cm-satisfaction-fields__item">
                <dt>{copy.contactEmail}</dt>
                <dd>{recipient.contact_email?.trim() || copy.contactEmpty}</dd>
              </div>
            </dl>
          </CommercialSectionCard>

          <CommercialSectionCard title={copy.inviteTitle} hint={CM_HELP.satisfactionSurveys.recipientInvite}>
            <div className="cm-satisfaction-stack">
              <p>{copy.inviteIntro}</p>
              {invite ? (
                <>
                  <InvitePreview
                    idPrefix="satisfaction-recipient"
                    mode={previewMode}
                    onModeChange={setPreviewMode}
                    subject={invite.subject}
                    body={invite.body}
                  />
                  <p>
                    <strong>{copy.linkLabel}:</strong> {invite.link_url}
                  </p>
                  <div className="cm-satisfaction-actions">
                    <CommercialActionButton variant="primary" onClick={() => void runCopy("message")}>
                      <Copy size={16} aria-hidden="true" /> {copy.copyMessage}
                    </CommercialActionButton>
                    <CommercialActionButton variant="default" onClick={() => void runCopy("subject")}>
                      {copy.copySubject}
                    </CommercialActionButton>
                    <CommercialActionButton variant="default" onClick={() => void runCopy("link")}>
                      {copy.copyLink}
                    </CommercialActionButton>
                  </div>
                  {manualCopy ? (
                    <div className="cm-satisfaction-stack">
                      <CommercialStateBanner variant="default">{copy.copyFailed}</CommercialStateBanner>
                      <textarea
                        className="cm-satisfaction-manual-copy"
                        readOnly
                        aria-label={copy.manualCopyLabel}
                        value={manualCopy.text}
                        onFocus={(event) => event.currentTarget.select()}
                      />
                    </div>
                  ) : null}
                </>
              ) : (
                <CommercialStateBanner variant="default">{copy.inviteMissing}</CommercialStateBanner>
              )}
            </div>
          </CommercialSectionCard>

          <RecipientContactDialog
            open={contactOpen}
            busy={savingContact}
            companyLabel={companyLabel}
            initial={{
              contactName: recipient.contact_name,
              contactEmail: recipient.contact_email,
            }}
            submitError={contactError}
            onClose={() => setContactOpen(false)}
            onSubmit={(values) => void submitContact(values)}
          />
        </>
      ) : null}
    </section>
  );
}
