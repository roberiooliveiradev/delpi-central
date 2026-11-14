import { useEffect, useState } from "react";

import {
  CommercialActionButton,
  CommercialHostDialog,
  CommercialStateBanner,
  CommercialTextField,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";

export type RecipientContactValues = {
  contactName: string | null;
  contactEmail: string | null;
};

type RecipientContactDialogProps = {
  open: boolean;
  busy: boolean;
  companyLabel: string;
  initial: { contactName: string | null; contactEmail: string | null };
  submitError?: string | null;
  onClose: () => void;
  onSubmit: (values: RecipientContactValues) => void;
};

/** Contato opcional e específico do convite — não altera cadastro da empresa nem o link. */
export function RecipientContactDialog({
  open,
  busy,
  companyLabel,
  initial,
  submitError,
  onClose,
  onSubmit,
}: RecipientContactDialogProps) {
  const copy = SATISFACTION_CONTENT.recipient;
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");

  useEffect(() => {
    if (!open) return;
    setContactName(initial.contactName ?? "");
    setContactEmail(initial.contactEmail ?? "");
  }, [open, initial.contactName, initial.contactEmail]);

  return (
    <CommercialHostDialog
      open={open}
      title={copy.contactDialogTitle}
      onClose={() => {
        if (!busy) onClose();
      }}
      footer={
        <div className="cm-satisfaction-actions">
          <CommercialActionButton variant="ghost" disabled={busy} onClick={onClose}>
            {copy.contactCancel}
          </CommercialActionButton>
          <CommercialActionButton
            variant="primary"
            disabled={busy}
            onClick={() =>
              onSubmit({
                contactName: contactName.trim() || null,
                contactEmail: contactEmail.trim() || null,
              })
            }
          >
            {busy ? copy.contactSaving : copy.contactSave}
          </CommercialActionButton>
        </div>
      }
    >
      <div className="cm-satisfaction-stack">
        <p>{copy.contactDialogIntro}</p>
        <p>
          <strong>{copy.contactCompany}:</strong> {companyLabel}
        </p>
        <CommercialTextField
          label={copy.contactName}
          hint={CM_HELP.satisfactionSurveys.recipientContactName}
          value={contactName}
          onChange={setContactName}
          disabled={busy}
          fullWidth
        />
        <CommercialTextField
          label={copy.contactEmail}
          hint={CM_HELP.satisfactionSurveys.recipientContactEmail}
          value={contactEmail}
          onChange={setContactEmail}
          disabled={busy}
          fullWidth
        />
        {submitError ? <CommercialStateBanner variant="error">{submitError}</CommercialStateBanner> : null}
      </div>
    </CommercialHostDialog>
  );
}
