import { CalendarDays, CheckCircle2, ChevronDown, UserRound } from "lucide-react";

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
import { AuditNcEvidenceSection } from "./AuditNcEvidenceSection";

type Props = {
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
  const sensoLabel = sensoName(item.sensoOrder, item.sensoName);
  const status = item.nc?.status ?? "open";
  const currentStep = ncWorkflowStep(status);
  const finalized = isNcFinalized(item.nc);
  const planComplete = isNcPlanComplete(form);
  const canFinalize = canFinalizeNcAction(form, item.nc, attachmentsByNcId);
  const ncAttachments = item.nc ? attachmentsByNcId[item.nc.id] : undefined;

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
            <label>
              Descrição da não conformidade
              <textarea
                rows={4}
                value={form.description}
                disabled={disabled || finalized}
                placeholder="Descreva o que foi observado no critério..."
                onChange={(e) => onChange({ description: e.target.value })}
                onBlur={() => onBlurSave()}
              />
            </label>
            <label>
              Causa / porquê
              <textarea
                rows={4}
                value={form.root_cause}
                disabled={disabled || finalized}
                placeholder="Explique por que a não conformidade ocorreu..."
                onChange={(e) => onChange({ root_cause: e.target.value })}
                onBlur={() => onBlurSave()}
              />
            </label>
            <label>
              Ação corretiva
              <textarea
                rows={4}
                value={form.corrective_action}
                disabled={disabled || finalized}
                placeholder="Descreva a ação para eliminar ou mitigar a NC..."
                onChange={(e) => onChange({ corrective_action: e.target.value })}
                onBlur={() => onBlurSave()}
              />
            </label>
          </div>

          <div className="a5s-nc-item__fields a5s-nc-item__fields--triple">
            <label>
              Responsável
              <span className="a5s-nc-input-wrap">
                <UserRound size={16} aria-hidden />
                <input
                  type="text"
                  value={form.responsible_name}
                  disabled={disabled || finalized}
                  placeholder="Nome do responsável"
                  onChange={(e) => onChange({ responsible_name: e.target.value })}
                  onBlur={() => onBlurSave()}
                />
              </span>
            </label>
            <label>
              Prazo para conclusão
              <span className="a5s-nc-input-wrap">
                <CalendarDays size={16} aria-hidden />
                <input
                  type="date"
                  value={form.due_date}
                  disabled={disabled || finalized}
                  onChange={(e) => onChange({ due_date: e.target.value })}
                  onBlur={() => onBlurSave()}
                />
              </span>
            </label>
            <label>
              Prioridade
              <span className="a5s-nc-input-wrap">
                <select
                  value={form.priority}
                  disabled={disabled || finalized}
                  onChange={(e) => {
                    onChange({ priority: e.target.value as NcFormState["priority"] });
                  }}
                  onBlur={() => onBlurSave()}
                >
                  <option value="">Selecione...</option>
                  {NC_PRIORITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </span>
            </label>
          </div>

          <AuditNcEvidenceSection
            ncId={item.nc?.id ?? null}
            before={ncAttachments?.before}
            after={ncAttachments?.after}
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
