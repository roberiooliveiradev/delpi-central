import { ActionButton, FieldLabel, HintAction } from "@delpi/plugin-ui/index";

import type { TicketDetail, TicketValidation } from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import { validationStatusLabel } from "../presentation/ticketValidationView";

function ValidationRow({
  item,
  cycleNote,
  onCycleNoteChange,
  cycleSaving,
  onAccept,
  onReject,
}: {
  item: TicketValidation;
  cycleNote: string;
  onCycleNoteChange: (value: string) => void;
  cycleSaving: boolean;
  onAccept: (validationId: number) => void;
  onReject: (validationId: number) => void;
}) {
  const canDecide = item.mine_to_decide === true;
  const submission = (item.submission_comment || "").trim();
  const approval = (item.approval_comment || "").trim();
  const approverId = item.requested_approver_id;
  const approverType = (item.requested_approver_type || "").trim();

  return (
    <li className="helpdesk-ticket-approvals__item" data-validation-id={item.id}>
      <div className="helpdesk-ticket-approvals__item-head">
        <span className="helpdesk-ticket-approvals__item-id">#{item.id}</span>
        <span className="helpdesk-ticket-approvals__item-status">
          {validationStatusLabel(item.status)}
        </span>
      </div>
      {submission ? (
        <p className="helpdesk-ticket-approvals__comment">
          <span className="helpdesk-ticket-approvals__comment-label">Solicitação:</span> {submission}
        </p>
      ) : null}
      {approval ? (
        <p className="helpdesk-ticket-approvals__comment">
          <span className="helpdesk-ticket-approvals__comment-label">Decisão:</span> {approval}
        </p>
      ) : null}
      {approverId != null || approverType ? (
        <p className="helpdesk-ticket-approvals__meta">
          {[approverType || null, approverId != null ? `ID ${approverId}` : null]
            .filter(Boolean)
            .join(" · ")}
        </p>
      ) : null}
      {canDecide ? (
        <div className="helpdesk-ticket-approvals__decide">
          <label className="helpdesk-lifecycle-note">
            <span>Comentário (opcional)</span>
            <input
              type="text"
              value={cycleNote}
              onChange={(event) => onCycleNoteChange(event.target.value)}
              disabled={cycleSaving}
              maxLength={2000}
            />
          </label>
          <div className="helpdesk-lifecycle-actions__buttons">
            <HintAction hint={helpTooltips.detailUi.acceptValidation} ariaLabel="Ajuda: Aceitar aprovação">
              <ActionButton
                variant="primary"
                type="button"
                disabled={cycleSaving}
                onClick={() => onAccept(item.id)}
              >
                {cycleSaving ? "Salvando…" : "Aceitar aprovação"}
              </ActionButton>
            </HintAction>
            <HintAction hint={helpTooltips.detailUi.rejectValidation} ariaLabel="Ajuda: Recusar aprovação">
              <ActionButton
                variant="default"
                type="button"
                disabled={cycleSaving}
                onClick={() => onReject(item.id)}
              >
                Recusar aprovação
              </ActionButton>
            </HintAction>
          </div>
        </div>
      ) : null}
    </li>
  );
}

export function TicketApprovalsSurface({
  ticket,
  cycleNote,
  onCycleNoteChange,
  cycleSaving,
  onAccept,
  onReject,
  onRequestApproval,
}: {
  ticket: TicketDetail;
  cycleNote: string;
  onCycleNoteChange: (value: string) => void;
  cycleSaving: boolean;
  onAccept: (validationId: number) => void;
  onReject: (validationId: number) => void;
  onRequestApproval: () => void;
}) {
  const validations = ticket.validations ?? [];
  const canRequest = ticket.can_request_approval === true;

  return (
    <div className="helpdesk-ticket-approvals" aria-label="Aprovações do chamado">
      <header className="helpdesk-ticket-approvals__header">
        <h2 className="helpdesk-ticket-approvals__title">Aprovações</h2>
        <p className="helpdesk-ticket-approvals__lead">
          <FieldLabel
            label="Solicitações deste chamado"
            hint={helpTooltips.detailUi.approvalsSurface}
          />
        </p>
        {canRequest ? (
          <HintAction hint={helpTooltips.detailUi.requestApproval} ariaLabel="Ajuda: Pedir aprovação">
            <ActionButton type="button" variant="primary" onClick={onRequestApproval}>
              Pedir aprovação
            </ActionButton>
          </HintAction>
        ) : null}
      </header>

      {validations.length === 0 ? (
        <p className="helpdesk-ticket-approvals__empty" role="status">
          Nenhuma solicitação de aprovação neste chamado.
        </p>
      ) : (
        <ul className="helpdesk-ticket-approvals__list">
          {validations.map((item) => (
            <ValidationRow
              key={item.id}
              item={item}
              cycleNote={cycleNote}
              onCycleNoteChange={onCycleNoteChange}
              cycleSaving={cycleSaving}
              onAccept={onAccept}
              onReject={onReject}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
