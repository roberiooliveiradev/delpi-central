import { CalendarDays, CheckCircle2, ChevronDown, UserRound } from "lucide-react";
import { useId } from "react";

import type { NcAttachmentMap, NcAttachmentType } from "../api/audit5sApi";
import {
  NC_PRIORITY_OPTIONS,
  ncStatusLabel,
  ncStatusVariant,
  sensoAccentClass,
  sensoName,
} from "../constants/audit5s";
import type { NcFormState, NcTreatmentItem } from "../utils/auditNc";
import {
  canFinalizeNcAction,
  formatNcScore,
  isNcFinalized,
  isNcPlanComplete,
  ncWorkflowStep,
} from "../utils/auditNc";
import {
  AuditNativeSelectField,
  AuditNativeTextAreaField,
  AuditNativeTextField,
} from "./auditFormFields";
import { AuditNcEvidenceSection } from "./AuditNcEvidenceSection";

type Props = {
  auditId: string;
  item: NcTreatmentItem;
  form: NcFormState;
  attachmentsByNcId: NcAttachmentMap;
  disabled: boolean;
  expanded: boolean;
  saving: boolean;
  savedFlash: boolean;
  finalizing: boolean;
  uploadingType: NcAttachmentType | null;
  onToggle: () => void;
  onChange: (patch: Partial<NcFormState>) => void;
  onBlurSave: () => void;
  onUpload: (type: NcAttachmentType, file: File) => Promise<void>;
  onFinalize: () => void;
};

function scoreTone(score: number): string {
  if (score <= 1) return "low";
  if (score <= 3) return "mid";
  return "high";
}

const WORKFLOW_STEPS = [
  { step: 1, label: "Registrar plano" },
  { step: 2, label: "Anexar evidências" },
  { step: 3, label: "Finalizar ação" },
];

export function AuditNcItemCard({
  auditId,
  item,
  form,
  attachmentsByNcId,
  disabled,
  expanded,
  saving,
  savedFlash,
  finalizing,
  uploadingType,
  onToggle,
  onChange,
  onBlurSave,
  onUpload,
  onFinalize,
}: Props) {
  const fieldIdPrefix = useId();
  const sensoLabel = sensoName(item.sensoOrder, item.sensoName);
  const status = item.nc?.status ?? "open";
  const currentStep = ncWorkflowStep(status);
  const finalized = isNcFinalized(item.nc);
  const planComplete = isNcPlanComplete(form);
  const canFinalize = canFinalizeNcAction(form, item.nc, attachmentsByNcId);
  const ncAttachments = item.nc ? attachmentsByNcId[item.nc.id] : undefined;
  const fieldLocked = disabled || finalized;

  return (
    <article className={`a5s-nc-item ${expanded ? "a5s-nc-item--expanded" : ""}`}>
      <button type="button" className="a5s-nc-item__header" onClick={onToggle}>
        <div className="a5s-nc-item__header-main">
          <span className={`a5s-nc-senso ${sensoAccentClass(item.sensoOrder)}`}>
            SENSO {item.sensoOrder} · {sensoLabel}
          </span>
          <strong className="a5s-nc-item__title">{item.criterionDescription}</strong>
        </div>
        <div className="a5s-nc-item__header-side">
          <span className={`a5s-status-badge a5s-status-badge--${ncStatusVariant(status)}`}>
            {ncStatusLabel(status)}
          </span>
          <span className={`a5s-nc-item__score a5s-nc-item__score--${scoreTone(item.score)}`}>
            Nota {formatNcScore(item.score)}
          </span>
          <ChevronDown size={18} className={expanded ? "a5s-nc-item__chevron--open" : undefined} aria-hidden />
        </div>
      </button>

      {expanded ? (
        <div className="a5s-nc-item__body">
          <ol className="a5s-nc-workflow" aria-label="Etapas do tratamento">
            {WORKFLOW_STEPS.map((entry) => (
              <li
                key={entry.step}
                className={`a5s-nc-workflow__step ${
                  currentStep === entry.step
                    ? "a5s-nc-workflow__step--current"
                    : currentStep > entry.step
                      ? "a5s-nc-workflow__step--done"
                      : ""
                }`}
              >
                <span className="a5s-nc-workflow__bullet">{entry.step}</span>
                <span>{entry.label}</span>
              </li>
            ))}
          </ol>

          {item.observation ? (
            <p className="a5s-nc-item__comment">
              <strong>Comentário da avaliação:</strong> {item.observation}
            </p>
          ) : null}

          <div className="a5s-nc-item__fields a5s-nc-item__fields--triple">
            <AuditNativeTextAreaField
              id={`${fieldIdPrefix}-description`}
              label="Descrição da não conformidade"
              span={false}
              rows={4}
              value={form.description}
              disabled={fieldLocked}
              placeholder="Descreva o que foi observado no critério..."
              onChange={(value) => onChange({ description: value })}
              onBlur={onBlurSave}
            />
            <AuditNativeTextAreaField
              id={`${fieldIdPrefix}-root-cause`}
              label="Causa / porquê"
              span={false}
              rows={4}
              value={form.root_cause}
              disabled={fieldLocked}
              placeholder="Explique por que a não conformidade ocorreu..."
              onChange={(value) => onChange({ root_cause: value })}
              onBlur={onBlurSave}
            />
            <AuditNativeTextAreaField
              id={`${fieldIdPrefix}-corrective-action`}
              label="Ação corretiva"
              span={false}
              rows={4}
              value={form.corrective_action}
              disabled={fieldLocked}
              placeholder="Descreva a ação para eliminar ou mitigar a NC..."
              onChange={(value) => onChange({ corrective_action: value })}
              onBlur={onBlurSave}
            />
          </div>

          <div className="a5s-nc-item__fields a5s-nc-item__fields--triple">
            <AuditNativeTextField
              id={`${fieldIdPrefix}-responsible`}
              label="Responsável"
              span={false}
              type="text"
              value={form.responsible_name}
              disabled={fieldLocked}
              placeholder="Nome do responsável"
              beforeControl={<UserRound size={16} aria-hidden />}
              controlWrapperClassName="a5s-nc-input-wrap"
              onChange={(value) => onChange({ responsible_name: value })}
              onBlur={onBlurSave}
            />
            <AuditNativeTextField
              id={`${fieldIdPrefix}-due-date`}
              label="Prazo para conclusão"
              span={false}
              type="date"
              value={form.due_date}
              disabled={fieldLocked}
              beforeControl={<CalendarDays size={16} aria-hidden />}
              controlWrapperClassName="a5s-nc-input-wrap"
              onChange={(value) => onChange({ due_date: value })}
              onBlur={onBlurSave}
            />
            <AuditNativeSelectField
              id={`${fieldIdPrefix}-priority`}
              label="Prioridade"
              span={false}
              value={form.priority}
              disabled={fieldLocked}
              placeholderOption="Selecione..."
              controlWrapperClassName="a5s-nc-input-wrap"
              options={NC_PRIORITY_OPTIONS}
              onChange={(value) =>
                onChange({ priority: value as NcFormState["priority"] })
              }
              onBlur={onBlurSave}
            />
          </div>

          <AuditNcEvidenceSection
            auditId={auditId}
            criterionId={item.criterionId}
            ncId={item.nc?.id ?? null}
            before={ncAttachments?.before}
            after={ncAttachments?.after}
            evaluationBefore={item.evaluationAttachment}
            disabled={disabled || finalized}
            uploadingType={uploadingType}
            onUpload={onUpload}
          />

          <div className="a5s-nc-item__footer">
            <span className="a5s-nc-item__save-hint" aria-live="polite">
              {finalized
                ? "Ação finalizada com evidências."
                : saving
                  ? "Salvando plano..."
                  : savedFlash
                    ? "Plano salvo automaticamente"
                    : "O plano salva ao sair de cada campo"}
            </span>

            {!finalized ? (
              <button
                type="button"
                className="a5s-btn a5s-btn--small"
                disabled={disabled || finalizing || !canFinalize}
                title={
                  !planComplete
                    ? "Preencha o plano de ação completo"
                    : !canFinalize
                      ? "Anexe foto do antes e do depois"
                      : undefined
                }
                onClick={onFinalize}
              >
                <CheckCircle2 size={15} aria-hidden />
                {finalizing ? "Finalizando..." : "Finalizar ação com evidências"}
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </article>
  );
}
