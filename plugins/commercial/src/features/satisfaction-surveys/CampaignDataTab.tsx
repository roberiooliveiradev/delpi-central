import { Pencil } from "lucide-react";
import { useState, type ReactNode } from "react";

import { updateSatisfactionCampaign } from "../../api/satisfactionSurveysApi";
import { CommercialActionButton, CommercialSectionCard } from "../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type { SatisfactionCampaign } from "../../types/satisfactionSurvey";
import type { CampaignFormValues } from "./campaignForm";
import { CampaignFormDialog } from "./CampaignFormDialog";
import { formatSurveyDateTime, formatSurveyPeriod } from "./satisfactionDates";
import { SatisfactionStatusBadge } from "./SatisfactionStatusBadge";

type CampaignDataTabProps = {
  campaign: SatisfactionCampaign;
  onCampaignUpdated: (campaign: SatisfactionCampaign) => void;
};

/** UI-02B — aba Dados da campanha: leitura + edição (servidor valida regras de datas). */
export function CampaignDataTab({ campaign, onCampaignUpdated }: CampaignDataTabProps) {
  const copy = SATISFACTION_CONTENT.data;
  const { notifySuccess } = useCommercialFloatingNotice();
  const [editOpen, setEditOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (values: CampaignFormValues) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateSatisfactionCampaign(campaign.id, {
        version: campaign.version,
        name: values.name,
        starts_at: values.startsAtIso,
        ends_at: values.endsAtIso,
      });
      onCampaignUpdated(updated);
      notifySuccess(SATISFACTION_CONTENT.campaignForm.updateSuccess);
      setEditOpen(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : copy.editHint);
    } finally {
      setSaving(false);
    }
  };

  const fields: Array<{ label: string; value: ReactNode }> = [
    { label: copy.fieldName, value: campaign.name },
    { label: copy.fieldPeriod, value: formatSurveyPeriod(campaign.starts_at, campaign.ends_at) },
    { label: copy.fieldStatus, value: <SatisfactionStatusBadge status={campaign.status} /> },
    { label: copy.fieldQuestionnaire, value: copy.fieldQuestionnaireValue },
    { label: copy.fieldVersion, value: campaign.questionnaire_version },
    { label: copy.fieldCreated, value: formatSurveyDateTime(campaign.created_at) },
    { label: copy.fieldUpdated, value: formatSurveyDateTime(campaign.updated_at) },
  ];

  return (
    <CommercialSectionCard
      title={copy.title}
      hint={CM_HELP.satisfactionSurveys.dataName}
      actions={
        <CommercialActionButton
          variant="default"
          onClick={() => {
            setError(null);
            setEditOpen(true);
          }}
        >
          <Pencil size={16} aria-hidden="true" /> {copy.edit}
        </CommercialActionButton>
      }
    >
      <div className="cm-satisfaction-stack">
        <dl className="cm-satisfaction-fields">
          {fields.map((field) => (
            <div key={field.label} className="cm-satisfaction-fields__item">
              <dt>{field.label}</dt>
              <dd>{field.value}</dd>
            </div>
          ))}
        </dl>
        <p>{copy.editHint}</p>
      </div>
      <CampaignFormDialog
        open={editOpen}
        mode="edit"
        busy={saving}
        initial={{
          name: campaign.name,
          startsAt: campaign.starts_at,
          endsAt: campaign.ends_at,
        }}
        submitError={error}
        onClose={() => setEditOpen(false)}
        onSubmit={(values) => void submit(values)}
      />
    </CommercialSectionCard>
  );
}
