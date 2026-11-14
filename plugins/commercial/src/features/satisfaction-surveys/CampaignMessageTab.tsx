import { useEffect, useMemo, useState } from "react";

import { updateSatisfactionCampaign } from "../../api/satisfactionSurveysApi";
import {
  CommercialActionButton,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialTextAreaField,
  CommercialTextField,
} from "../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type { SatisfactionCampaign } from "../../types/satisfactionSurvey";
import { copyToClipboard } from "./clipboard";
import { InvitePreview, type InvitePreviewMode } from "./InvitePreview";
import {
  INVITE_COMPANY_TOKEN,
  INVITE_LINK_TOKEN,
  INVITE_SAMPLE_COMPANY,
  INVITE_SAMPLE_LINK,
  buildInviteHtml,
  buildMessengerText,
  insertTokenAtSelection,
  missingInvitePlaceholders,
  replaceInvitePlaceholders,
  unknownInvitePlaceholders,
} from "./inviteMessage";

const BODY_FIELD_ID = "satisfaction-campaign-invite-body";

type CampaignMessageTabProps = {
  campaign: SatisfactionCampaign;
  onCampaignUpdated: (campaign: SatisfactionCampaign) => void;
  /** Recarrega a campanha do servidor (após conflito de versão). */
  onReloadRequested: () => void;
};

/** UI-02B — aba Mensagem padrão: uma mensagem por campanha com prévia fictícia. */
export function CampaignMessageTab({
  campaign,
  onCampaignUpdated,
  onReloadRequested,
}: CampaignMessageTabProps) {
  const copy = SATISFACTION_CONTENT.message;
  const { notifySuccess } = useCommercialFloatingNotice();
  const [subject, setSubject] = useState(campaign.invite_subject);
  const [body, setBody] = useState(campaign.invite_body);
  const [previewMode, setPreviewMode] = useState<InvitePreviewMode>("email");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Sincroniza com a versão do servidor (recarga/salvamento); edição local só vive entre versões.
  useEffect(() => {
    setSubject(campaign.invite_subject);
    setBody(campaign.invite_body);
    setSaveError(null);
  }, [campaign.id, campaign.version, campaign.invite_subject, campaign.invite_body]);

  const dirty = subject !== campaign.invite_subject || body !== campaign.invite_body;
  const missing = useMemo(() => missingInvitePlaceholders(body), [body]);
  const unknown = useMemo(
    () => [
      ...unknownInvitePlaceholders(subject),
      ...unknownInvitePlaceholders(body),
    ].filter((token, index, all) => all.indexOf(token) === index),
    [subject, body],
  );
  const sampleSubject = useMemo(
    () => replaceInvitePlaceholders(subject, { company: INVITE_SAMPLE_COMPANY, link: INVITE_SAMPLE_LINK }),
    [subject],
  );
  const sampleBody = useMemo(
    () => replaceInvitePlaceholders(body, { company: INVITE_SAMPLE_COMPANY, link: INVITE_SAMPLE_LINK }),
    [body],
  );

  const insertToken = (token: string) => {
    const field = document.getElementById(BODY_FIELD_ID);
    const textarea = field instanceof HTMLTextAreaElement ? field : null;
    const result = insertTokenAtSelection(
      body,
      token,
      textarea?.selectionStart,
      textarea?.selectionEnd,
    );
    setBody(result.text);
    window.requestAnimationFrame(() => {
      if (!textarea) return;
      textarea.focus();
      textarea.setSelectionRange(result.cursor, result.cursor);
    });
  };

  const save = async () => {
    if (saving) return;
    if (!subject.trim()) {
      setSaveError(copy.subjectRequired);
      return;
    }
    if (!body.trim()) {
      setSaveError(copy.bodyRequired);
      return;
    }
    if (unknown.length > 0) {
      setSaveError(copy.unknownTokens(unknown));
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await updateSatisfactionCampaign(campaign.id, {
        version: campaign.version,
        invite_subject: subject.trim(),
        invite_body: body,
      });
      onCampaignUpdated(updated);
      notifySuccess(copy.saveSuccess);
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : copy.conflict);
    } finally {
      setSaving(false);
    }
  };

  const copyPreview = async () => {
    const payload =
      previewMode === "messenger"
        ? { text: buildMessengerText(sampleBody) }
        : {
            text: buildMessengerText(sampleBody),
            html: buildInviteHtml(sampleBody, { linkify: false }),
          };
    const ok = await copyToClipboard(payload);
    if (ok) notifySuccess(copy.copiedPreview);
  };

  return (
    <div className="cm-satisfaction-stack">
      <CommercialSectionCard title={copy.title}>
        <div className="cm-satisfaction-stack">
          <p>{copy.intro}</p>
          <CommercialTextField
            id="satisfaction-campaign-invite-subject"
            label={copy.fieldSubject}
            hint={CM_HELP.satisfactionSurveys.messageSubject}
            value={subject}
            onChange={setSubject}
            disabled={saving}
            fullWidth
          />
          <CommercialTextAreaField
            id={BODY_FIELD_ID}
            label={copy.fieldBody}
            hint={CM_HELP.satisfactionSurveys.messageBody}
            value={body}
            onChange={setBody}
            disabled={saving}
            rows={10}
            fullWidth
          />
          <div className="cm-satisfaction-actions">
            <CommercialActionButton
              variant="default"
              disabled={saving}
              onClick={() => insertToken(INVITE_COMPANY_TOKEN)}
            >
              {copy.insertCompany}
            </CommercialActionButton>
            <CommercialActionButton
              variant="default"
              disabled={saving}
              onClick={() => insertToken(INVITE_LINK_TOKEN)}
            >
              {copy.insertLink}
            </CommercialActionButton>
          </div>
          {unknown.length > 0 ? (
            <CommercialStateBanner variant="error">
              {copy.unknownTokens(unknown)}
            </CommercialStateBanner>
          ) : null}
          {missing.length > 0 ? (
            <CommercialStateBanner variant="default">
              {copy.missingTokens(missing)}
            </CommercialStateBanner>
          ) : null}
        </div>
      </CommercialSectionCard>

      <CommercialSectionCard title={copy.previewTitle} hint={CM_HELP.satisfactionSurveys.messagePreview}>
        <div className="cm-satisfaction-stack">
          <p>{copy.previewSampleNote}</p>
          <InvitePreview
            idPrefix="satisfaction-message"
            mode={previewMode}
            onModeChange={setPreviewMode}
            subject={sampleSubject}
            body={sampleBody}
            linkify={false}
          />
          <div className="cm-satisfaction-actions">
            <CommercialActionButton variant="default" onClick={() => void copyPreview()}>
              {copy.copyPreview}
            </CommercialActionButton>
          </div>
        </div>
      </CommercialSectionCard>

      <div className="cm-satisfaction-actions">
        {dirty ? <span>{copy.dirty}</span> : null}
        {saveError ? (
          <CommercialStateBanner variant="error">
            {saveError}{" "}
            <CommercialActionButton variant="ghost" onClick={onReloadRequested}>
              {copy.reload}
            </CommercialActionButton>
          </CommercialStateBanner>
        ) : null}
        <CommercialActionButton
          variant="ghost"
          disabled={!dirty || saving}
          onClick={() => {
            setSubject(campaign.invite_subject);
            setBody(campaign.invite_body);
            setSaveError(null);
          }}
        >
          {copy.revert}
        </CommercialActionButton>
        <CommercialActionButton
          variant="primary"
          disabled={!dirty || saving || unknown.length > 0}
          onClick={() => void save()}
        >
          {saving ? copy.saving : copy.save}
        </CommercialActionButton>
      </div>
    </div>
  );
}
