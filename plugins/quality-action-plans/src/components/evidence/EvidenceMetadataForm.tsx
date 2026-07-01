import {
  EVIDENCE_SECTION_OPTIONS,
  EVIDENCE_TYPE_OPTIONS,
} from "../../constants/evidence";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { PlanAction } from "../../types/actionPlan";
import { SelectField } from "../ui/SelectField";
import { TextAreaField } from "../ui/TextAreaField";
import { linkedActionLabel } from "./evidenceAttachmentUtils";

type Props = {
  idPrefix: string;
  evidenceType: string;
  section: string;
  actionId: string;
  description: string;
  actions?: PlanAction[];
  lockActionId?: boolean;
  disabled?: boolean;
  onEvidenceTypeChange: (value: string) => void;
  onSectionChange: (value: string) => void;
  onActionIdChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
};

export function EvidenceMetadataForm({
  idPrefix,
  evidenceType,
  section,
  actionId,
  description,
  actions = [],
  lockActionId = false,
  disabled = false,
  onEvidenceTypeChange,
  onSectionChange,
  onActionIdChange,
  onDescriptionChange,
}: Props) {
  const actionOptions = [
    { value: "", label: "Nenhuma (plano geral)" },
    ...actions.map((action) => ({ value: action.id, label: linkedActionLabel(action) })),
  ];
  const lockedAction = actions.find((action) => action.id === actionId);

  return (
    <div
      className={`pac-form-grid pac-evidence-metadata-form${
        actions.length ? " pac-evidence-metadata-form--with-action" : ""
      }`}
    >
      <SelectField
        id={`${idPrefix}-type`}
        label="Tipo"
        hint={PAC_HELP_TOOLTIPS.evidence.type}
        options={[...EVIDENCE_TYPE_OPTIONS]}
        value={evidenceType}
        onChange={onEvidenceTypeChange}
        searchable={false}
        disabled={disabled}
      />
      <SelectField
        id={`${idPrefix}-section`}
        label="Seção 8D"
        hint={PAC_HELP_TOOLTIPS.evidence.section}
        options={[...EVIDENCE_SECTION_OPTIONS]}
        value={section}
        onChange={onSectionChange}
        searchable={false}
        disabled={disabled}
      />
      {actions.length ? (
        lockActionId ? (
          <div className="pac-field pac-field--action-link">
            <span className="pac-field__label">Vincular à ação</span>
            <p className="pac-evidence-pending-item__locked-action">
              {lockedAction ? linkedActionLabel(lockedAction) : "Ação da fila"}
            </p>
          </div>
        ) : (
          <SelectField
            id={`${idPrefix}-action`}
            className="pac-field--action-link"
            label="Vincular à ação"
            hint={PAC_HELP_TOOLTIPS.evidence.linkedAction}
            options={actionOptions}
            value={actionId}
            onChange={onActionIdChange}
            searchable={actions.length > 4}
            disabled={disabled}
          />
        )
      ) : null}
      <TextAreaField
        id={`${idPrefix}-desc`}
        label="Descrição"
        hint={PAC_HELP_TOOLTIPS.evidence.description}
        value={description}
        onChange={onDescriptionChange}
        rows={3}
        fullWidth
        disabled={disabled}
      />
    </div>
  );
}
