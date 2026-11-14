import { createDashboardNativeTextField, formFieldShellBemClasses } from "@delpi/plugin-ui/index";
import { useEffect, useState } from "react";

import {
  CommercialActionButton,
  CommercialHostDialog,
  CommercialStateBanner,
  CommercialTextField,
  UI_PREFIX,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import { validateCampaignForm, type CampaignFormValues } from "./campaignForm";
import { isoToLocalInput } from "./satisfactionDates";

const NativeTextField = createDashboardNativeTextField({
  classNames: formFieldShellBemClasses(UI_PREFIX),
});

type CampaignFormDialogProps = {
  open: boolean;
  mode: "create" | "edit";
  busy: boolean;
  initial?: { name: string; startsAt: string; endsAt: string };
  /** Erro devolvido pela API na última tentativa; o diálogo permanece aberto. */
  submitError?: string | null;
  onClose: () => void;
  onSubmit: (values: CampaignFormValues) => void;
};

export function CampaignFormDialog({
  open,
  mode,
  busy,
  initial,
  submitError,
  onClose,
  onSubmit,
}: CampaignFormDialogProps) {
  const copy = SATISFACTION_CONTENT.campaignForm;
  const [name, setName] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(initial?.name ?? "");
    setStartsAt(isoToLocalInput(initial?.startsAt));
    setEndsAt(isoToLocalInput(initial?.endsAt));
    setValidationError(null);
  }, [open, initial?.name, initial?.startsAt, initial?.endsAt]);

  const submit = () => {
    const result = validateCampaignForm({
      name,
      startsAtLocal: startsAt,
      endsAtLocal: endsAt,
    });
    if (!result.ok) {
      setValidationError(result.message);
      return;
    }
    setValidationError(null);
    onSubmit(result.values);
  };

  const error = validationError ?? submitError ?? null;

  return (
    <CommercialHostDialog
      open={open}
      title={mode === "create" ? copy.createTitle : copy.editTitle}
      onClose={() => {
        if (!busy) onClose();
      }}
      footer={
        <div className="cm-satisfaction-actions">
          <CommercialActionButton variant="ghost" disabled={busy} onClick={onClose}>
            {copy.cancel}
          </CommercialActionButton>
          <CommercialActionButton variant="primary" disabled={busy} onClick={submit}>
            {busy ? copy.saving : mode === "create" ? copy.create : copy.save}
          </CommercialActionButton>
        </div>
      }
    >
      <div className="cm-satisfaction-stack">
        <p>{copy.intro}</p>
        <CommercialTextField
          label={copy.fieldName}
          hint={CM_HELP.satisfactionSurveys.createName}
          value={name}
          onChange={setName}
          disabled={busy}
          required
          fullWidth
        />
        <NativeTextField
          id="satisfaction-campaign-starts-at"
          label={copy.fieldStartsAt}
          hint={CM_HELP.satisfactionSurveys.createStartsAt}
          type="datetime-local"
          value={startsAt}
          onChange={setStartsAt}
          disabled={busy}
          required
        />
        <NativeTextField
          id="satisfaction-campaign-ends-at"
          label={copy.fieldEndsAt}
          hint={CM_HELP.satisfactionSurveys.createEndsAt}
          type="datetime-local"
          value={endsAt}
          onChange={setEndsAt}
          disabled={busy}
          required
        />
        {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
      </div>
    </CommercialHostDialog>
  );
}
