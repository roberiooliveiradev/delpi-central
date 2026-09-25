import { FieldLabel } from "@delpi/plugin-ui/index";

import type { TicketDetail } from "../api/helpdeskApi";
import type { HelpdeskAssigneeValue } from "../components/HelpdeskAssigneePicker";
import { helpTooltips } from "../content/helpTooltips";
import { absoluteDateTimeLabel } from "../presentation/ticketView";
import { approvalSummaryCounts } from "../presentation/ticketValidationView";
import { HelpdeskAssignPopover } from "./HelpdeskAssignPopover";

export function TicketDetailsSurface({
  ticket,
  assigneePick,
  onAssigneeChange,
  onAssignConfirm,
  assignSaving,
  onOpenApprovals,
}: {
  ticket: TicketDetail;
  assigneePick: HelpdeskAssigneeValue | null;
  onAssigneeChange: (user: HelpdeskAssigneeValue | null) => void;
  onAssignConfirm: () => void;
  assignSaving: boolean;
  onOpenApprovals: () => void;
}) {
  const opened = absoluteDateTimeLabel(ticket.created_at);
  const updated = absoluteDateTimeLabel(ticket.updated_at);
  const solved = absoluteDateTimeLabel(ticket.solved_at ?? "");
  const closed = absoluteDateTimeLabel(ticket.closed_at ?? "");
  const tto = (ticket.sla_tto || "").trim();
  const ttr = (ticket.sla_ttr || "").trim();
  const requester = (ticket.requester_display_name || "").trim() || "—";
  const observers = (ticket.observers_display_name || "").trim();
  const { total: approvalTotal, pending: approvalPending } = approvalSummaryCounts(ticket.validations);

  return (
    <div className="helpdesk-ticket-details" aria-label="Detalhes do chamado">
      <section
        className="helpdesk-ticket-details__section"
        aria-labelledby="helpdesk-details-actors"
      >
        <h2 id="helpdesk-details-actors" className="helpdesk-ticket-details__title">
          Pessoas e atores
        </h2>
        <dl className="helpdesk-ticket-details__list">
          <div className="helpdesk-ticket-details__row">
            <dt>Requerente</dt>
            <dd>{requester}</dd>
          </div>
          <div className="helpdesk-ticket-details__row">
            <dt>
              <FieldLabel label="Observadores" hint={helpTooltips.detailUi.observersRead} />
            </dt>
            <dd>{observers || "Nenhum observador."}</dd>
          </div>
        </dl>
        <HelpdeskAssignPopover
          variant="inline"
          assignedDisplayName={ticket.assigned_display_name}
          assignedUserId={ticket.assigned_user_id}
          value={assigneePick}
          onChange={onAssigneeChange}
          onConfirm={onAssignConfirm}
          saving={assignSaving}
          canAssign={ticket.can_assign === true}
        />
      </section>

      {tto || ttr ? (
        <section
          className="helpdesk-ticket-details__section"
          aria-labelledby="helpdesk-details-sla"
        >
          <h2 id="helpdesk-details-sla" className="helpdesk-ticket-details__title">
            Níveis de serviço
          </h2>
          <dl className="helpdesk-ticket-details__list">
            {tto ? (
              <div className="helpdesk-ticket-details__row">
                <dt>
                  <FieldLabel
                    label="Nível de serviço para atendimento"
                    hint={helpTooltips.detailUi.slaLevelName}
                  />
                </dt>
                <dd>{tto}</dd>
              </div>
            ) : null}
            {ttr ? (
              <div className="helpdesk-ticket-details__row">
                <dt>
                  <FieldLabel
                    label="Nível de serviço para solução"
                    hint={helpTooltips.detailUi.slaLevelName}
                  />
                </dt>
                <dd>{ttr}</dd>
              </div>
            ) : null}
          </dl>
        </section>
      ) : null}

      {opened || updated || solved || closed ? (
        <section
          className="helpdesk-ticket-details__section"
          aria-labelledby="helpdesk-details-dates"
        >
          <h2 id="helpdesk-details-dates" className="helpdesk-ticket-details__title">
            Datas
          </h2>
          <dl className="helpdesk-ticket-details__list">
            {opened ? (
              <div className="helpdesk-ticket-details__row">
                <dt>Aberto</dt>
                <dd>{opened}</dd>
              </div>
            ) : null}
            {updated ? (
              <div className="helpdesk-ticket-details__row">
                <dt>Atualizado</dt>
                <dd>{updated}</dd>
              </div>
            ) : null}
            {solved ? (
              <div className="helpdesk-ticket-details__row">
                <dt>Resolvido</dt>
                <dd>{solved}</dd>
              </div>
            ) : null}
            {closed ? (
              <div className="helpdesk-ticket-details__row">
                <dt>Fechado</dt>
                <dd>{closed}</dd>
              </div>
            ) : null}
          </dl>
        </section>
      ) : null}

      <section
        className="helpdesk-ticket-details__section"
        aria-labelledby="helpdesk-details-approvals"
      >
        <h2 id="helpdesk-details-approvals" className="helpdesk-ticket-details__title">
          Aprovações
        </h2>
        <p className="helpdesk-ticket-details__summary">
          {approvalTotal === 0
            ? "Nenhuma solicitação de aprovação neste chamado."
            : `${approvalTotal} ${approvalTotal === 1 ? "solicitação" : "solicitações"}${
                approvalPending > 0
                  ? ` · ${approvalPending} ${approvalPending === 1 ? "pendente" : "pendentes"}`
                  : ""
              }`}
        </p>
        <button
          type="button"
          className="helpdesk-ticket-details__link"
          onClick={onOpenApprovals}
        >
          Ver aprovações
        </button>
      </section>
    </div>
  );
}
