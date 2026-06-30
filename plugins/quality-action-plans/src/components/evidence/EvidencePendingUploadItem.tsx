import { Trash2 } from "lucide-react";

import {
  EVIDENCE_SECTION_OPTIONS,
  EVIDENCE_TYPE_OPTIONS,
} from "../../constants/evidence";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { PlanAction } from "../../types/actionPlan";
import { SelectField } from "../ui/SelectField";
import { TextField } from "../ui/TextField";
import { formatEvidenceFileSize, linkedActionLabel } from "./evidenceAttachmentUtils";

export type EvidencePendingUpload = {
  id: string;
  file: File;
  evidenceType: string;
  section: string;
  actionId: string;
  description: string;
};

type Props = {
  item: EvidencePendingUpload;
  actions: PlanAction[];
  lockActionId?: boolean;
  disabled?: boolean;
  onChange: (id: string, patch: Partial<EvidencePendingUpload>) => void;
  onRemove: (id: string) => void;
};

export function EvidencePendingUploadItem({
  item,
  actions,
  lockActionId = false,
  disabled = false,
  onChange,
  onRemove,
}: Props) {
  const actionOptions = [
    { value: "", label: "Nenhuma (plano geral)" },
    ...actions.map((action) => ({ value: action.id, label: linkedActionLabel(action) })),
  ];
  const lockedAction = actions.find((action) => action.id === item.actionId);

  return (
    <article className="pac-evidence-pending-item">
      <header className="pac-evidence-pending-item__header">
        <div className="pac-evidence-pending-item__file">
          <strong>{item.file.name}</strong>
          <span className="pac-muted">{formatEvidenceFileSize(item.file.size)}</span>
        </div>
        <button
          type="button"
          className="pac-ghost-btn pac-ghost-btn--icon"
          aria-label={`Remover ${item.file.name} da fila`}
          title="Remover da fila"
          disabled={disabled}
          onClick={() => onRemove(item.id)}
        >
          <Trash2 size={16} />
        </button>
      </header>
      <div
        className={`pac-form-grid pac-evidence-pending-item__fields${
          actions.length ? " pac-evidence-pending-item__fields--with-action" : ""
        }`}
      >
        <SelectField
          id={`pac-pending-type-${item.id}`}
          label="Tipo"
          hint={PAC_HELP_TOOLTIPS.evidence.type}
          options={[...EVIDENCE_TYPE_OPTIONS]}
          value={item.evidenceType}
          onChange={(value) => onChange(item.id, { evidenceType: value })}
          searchable={false}
          disabled={disabled}
        />
        <SelectField
          id={`pac-pending-section-${item.id}`}
          label="Seção 8D"
          hint={PAC_HELP_TOOLTIPS.evidence.section}
          options={[...EVIDENCE_SECTION_OPTIONS]}
          value={item.section}
          onChange={(value) => onChange(item.id, { section: value })}
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
              id={`pac-pending-action-${item.id}`}
              className="pac-field--action-link"
              label="Vincular à ação"
              hint={PAC_HELP_TOOLTIPS.evidence.linkedAction}
              options={actionOptions}
              value={item.actionId}
              onChange={(value) => onChange(item.id, { actionId: value })}
              searchable={actions.length > 4}
              disabled={disabled}
            />
          )
        ) : null}
        <TextField
          id={`pac-pending-desc-${item.id}`}
          label="Descrição"
          hint={PAC_HELP_TOOLTIPS.evidence.description}
          value={item.description}
          onChange={(value) => onChange(item.id, { description: value })}
          fullWidth
          disabled={disabled}
        />
      </div>
    </article>
  );
}
