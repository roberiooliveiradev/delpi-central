import type { TicketDetail } from "../api/helpdeskApi";
import type { HelpdeskAssigneeValue } from "../components/HelpdeskAssigneePicker";
import { absoluteDateTimeLabel } from "../presentation/ticketView";
import { HelpdeskAssignPopover } from "./HelpdeskAssignPopover";

export function TicketContextPanel({
  ticket,
  assigneePick,
  onAssigneeChange,
  onAssignConfirm,
  assignSaving,
}: {
  ticket: TicketDetail;
  assigneePick: HelpdeskAssigneeValue | null;
  onAssigneeChange: (user: HelpdeskAssigneeValue | null) => void;
  onAssignConfirm: () => void;
  assignSaving: boolean;
}) {
  const opened = absoluteDateTimeLabel(ticket.created_at);
  const updated = absoluteDateTimeLabel(ticket.updated_at);
  const tto = (ticket.sla_tto || "").trim();
  const ttr = (ticket.sla_ttr || "").trim();
  const requester = (ticket.requester_display_name || "").trim() || "—";
  const observers = (ticket.observers_display_name || "").trim();

  return (
    <aside className="helpdesk-ticket-context" aria-label="Contexto do chamado">
      <section className="helpdesk-ticket-context__section" aria-labelledby="helpdesk-context-actors">
        <h2 id="helpdesk-context-actors" className="helpdesk-ticket-context__title">
          Atores
        </h2>
        <dl className="helpdesk-ticket-context__list">
          <div className="helpdesk-ticket-context__row">
            <dt>Requerente</dt>
            <dd>{requester}</dd>
          </div>
          {observers ? (
            <div className="helpdesk-ticket-context__row">
              <dt>Observador</dt>
              <dd>{observers}</dd>
            </div>
          ) : null}
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
        <section className="helpdesk-ticket-context__section" aria-labelledby="helpdesk-context-sla">
          <h2 id="helpdesk-context-sla" className="helpdesk-ticket-context__title">
            Níveis de serviço
          </h2>
          <dl className="helpdesk-ticket-context__list">
            {tto ? (
              <div className="helpdesk-ticket-context__row">
                <dt>TTO</dt>
                <dd>{tto}</dd>
              </div>
            ) : null}
            {ttr ? (
              <div className="helpdesk-ticket-context__row">
                <dt>TTR</dt>
                <dd>{ttr}</dd>
              </div>
            ) : null}
          </dl>
        </section>
      ) : null}

      {opened || updated ? (
        <section className="helpdesk-ticket-context__section" aria-labelledby="helpdesk-context-dates">
          <h2 id="helpdesk-context-dates" className="helpdesk-ticket-context__title">
            Datas
          </h2>
          <dl className="helpdesk-ticket-context__list">
            {opened ? (
              <div className="helpdesk-ticket-context__row">
                <dt>Aberto</dt>
                <dd>{opened}</dd>
              </div>
            ) : null}
            {updated ? (
              <div className="helpdesk-ticket-context__row">
                <dt>Atualizado</dt>
                <dd>{updated}</dd>
              </div>
            ) : null}
          </dl>
        </section>
      ) : null}
    </aside>
  );
}
