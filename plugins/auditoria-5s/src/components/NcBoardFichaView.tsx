import type { ReactNode } from "react";

import type { NcAction, NcAttachmentMap } from "../api/audit5sApi";
import {
  ncBoardStatusVariant,
  ncPriorityLabel,
  ncStatusLabel,
  sensoAccentClass,
  sensoName,
  shiftLabel,
} from "../constants/audit5s";
import type { NcBoardItem } from "../types/ncManagement";
import { formatNcScore } from "../utils/auditNc";
import type { NcTreatmentItem } from "../utils/auditNc";
import { formatDisplayDate } from "../utils/dates";
import { resolveNcBoardRowStatus } from "../utils/ncDueSla";
import { formatPersonName } from "../utils/formatPersonName";
import { NcAttachmentPreview } from "./NcAttachmentPreview";
import { NcWorkflowPill } from "./NcWorkflowPill";
import { ResponseAttachmentPreview } from "./ResponseAttachmentPreview";

type Props = {
  item: NcBoardItem;
  treatmentItem: NcTreatmentItem | null;
  attachmentsByNcId: NcAttachmentMap;
  actions: NcAction[];
};

function formatActionTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function displayValue(value: string | null | undefined): string {
  const text = value?.trim();
  return text || "—";
}

function FichaField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="a5s-nc-ficha__field">
      <span className="a5s-nc-ficha__field-label">{label}</span>
      <div className="a5s-nc-ficha__field-value">{value}</div>
    </div>
  );
}

export function NcBoardFichaView({ item, treatmentItem, attachmentsByNcId, actions }: Props) {
  const rowStatus = resolveNcBoardRowStatus(item);
  const ncStatus = item.is_registered ? item.status : "pending";
  const attachments = item.is_registered ? attachmentsByNcId[item.id] : undefined;
  const score = treatmentItem?.score ?? item.score ?? 0;

  return (
    <div className="a5s-nc-ficha">
      <section className="a5s-nc-ficha__summary">
        <div className="a5s-nc-ficha__badges">
          <span className={`a5s-nc-senso ${sensoAccentClass(item.senso_order)}`}>
            SENSO {item.senso_order} · {sensoName(item.senso_order, item.senso_name)}
          </span>
          <span
            className={`a5s-status-badge a5s-status-badge--${ncBoardStatusVariant(ncStatus, item.is_registered)}`}
          >
            {item.is_registered ? ncStatusLabel(ncStatus) : "Aguardando registro"}
          </span>
          <span className={`a5s-nc-board-row-status a5s-nc-board-row-status--${rowStatus.tone}`}>
            {rowStatus.label}
          </span>
        </div>

        <p className="a5s-nc-ficha__criterion">{item.criterion_description}</p>

        <div className="a5s-nc-ficha__meta-grid">
          <FichaField label="Auditoria" value={`${item.audit_code} · ${formatDisplayDate(item.audit_date)}`} />
          <FichaField label="Área / turno" value={`${item.area_name} · ${shiftLabel(item.shift)}`} />
          <FichaField label="Nota do critério" value={formatNcScore(score)} />
          <FichaField
            label="Progresso"
            value={
              <NcWorkflowPill
                planStarted={item.plan_started}
                workflowStep={item.workflow_step}
                status={item.status}
              />
            }
          />
        </div>
      </section>

      {treatmentItem?.observation ? (
        <section className="a5s-nc-ficha__section">
          <h3>Comentário da avaliação</h3>
          <p className="a5s-nc-ficha__text">{treatmentItem.observation}</p>
        </section>
      ) : null}

      <section className="a5s-nc-ficha__section">
        <h3>Plano de ação</h3>
        <div className="a5s-nc-ficha__grid">
          <FichaField label="Descrição da NC" value={displayValue(item.description)} />
          <FichaField label="Causa / porquê" value={displayValue(item.root_cause)} />
          <FichaField label="Ação corretiva" value={displayValue(item.corrective_action)} />
          <FichaField
            label="Responsável"
            value={formatPersonName(item.responsible_name) || displayValue(item.responsible_name)}
          />
          <FichaField
            label="Prazo"
            value={item.due_date ? formatDisplayDate(item.due_date) : "—"}
          />
          <FichaField label="Prioridade" value={ncPriorityLabel(item.priority)} />
        </div>
      </section>

      {item.is_registered ? (
        <section className="a5s-nc-ficha__section">
          <h3>Evidências</h3>
          <div className="a5s-nc-ficha__evidence-grid">
            <article className="a5s-nc-ficha__evidence">
              <strong>Antes</strong>
              {attachments?.before ? (
                <NcAttachmentPreview ncId={item.id} attachment={attachments.before} label="Antes" />
              ) : treatmentItem?.evaluationAttachment ? (
                <ResponseAttachmentPreview
                  auditId={item.audit_id}
                  criterionId={treatmentItem.criterionId}
                  attachment={treatmentItem.evaluationAttachment}
                  label="Antes"
                />
              ) : (
                <p className="a5s-nc-ficha__empty">Nenhuma evidência anexada.</p>
              )}
            </article>
            <article className="a5s-nc-ficha__evidence">
              <strong>Depois</strong>
              {attachments?.after ? (
                <NcAttachmentPreview ncId={item.id} attachment={attachments.after} label="Depois" />
              ) : (
                <p className="a5s-nc-ficha__empty">Nenhuma evidência anexada.</p>
              )}
            </article>
          </div>
        </section>
      ) : (
        <section className="a5s-nc-ficha__section">
          <p className="a5s-nc-ficha__notice">
            O plano de ação ainda não foi registrado. Use <strong>Atualizar</strong> para iniciar o
            tratamento.
          </p>
        </section>
      )}

      <section className="a5s-nc-ficha__section">
        <h3>Histórico de notas</h3>
        {actions.length === 0 ? (
          <p className="a5s-nc-ficha__empty">Nenhuma observação registrada ainda.</p>
        ) : (
          <ol className="a5s-nc-ficha__history">
            {actions.map((action) => (
              <li key={action.id} className="a5s-nc-ficha__history-item">
                <div className="a5s-nc-ficha__history-head">
                  <strong>{formatPersonName(action.actor_display_name) || action.actor_display_name}</strong>
                  <time dateTime={action.created_at}>{formatActionTimestamp(action.created_at)}</time>
                </div>
                <p>{action.description}</p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
