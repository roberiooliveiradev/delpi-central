import { Eye } from "lucide-react";

import type { PreviousCriterionNonconformity } from "../api/audit5sApi";
import { ncStatusLabel, shiftLabel } from "../constants/audit5s";
import { formatDisplayDate } from "../utils/dates";
import { NcBoardModalShell } from "./NcBoardModalShell";

type Props = {
  nc: PreviousCriterionNonconformity | null;
  open: boolean;
  onClose: () => void;
};

function display(value: string | null | undefined): string {
  const text = value?.trim();
  return text || "—";
}

export function PreviousCriterionNcModal({ nc, open, onClose }: Props) {
  if (!nc) return null;

  const meta = [
    nc.audit_code,
    nc.audit_date ? formatDisplayDate(nc.audit_date) : null,
    nc.shift ? shiftLabel(nc.shift) : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <NcBoardModalShell
      open={open}
      title="Não conformidade da auditoria anterior"
      titleId="a5s-previous-nc-modal-title"
      meta={meta || undefined}
      icon={<Eye size={20} aria-hidden />}
      onClose={onClose}
      dialogClassName="a5s-nc-board-treat-dialog--view"
      footer={
        <button type="button" className="a5s-btn a5s-btn--ghost" onClick={onClose}>
          Voltar à avaliação
        </button>
      }
    >
      <div className="a5s-nc-board-treat-dialog__body a5s-previous-nc-modal">
        <dl className="a5s-previous-nc-modal__fields">
          <div>
            <dt>Critério</dt>
            <dd>
              <strong>{display(nc.criterion_code)}</strong>
              {nc.criterion_description?.trim()
                ? ` — ${nc.criterion_description.trim()}`
                : ""}
            </dd>
          </div>
          <div>
            <dt>Situação</dt>
            <dd>{ncStatusLabel(nc.status)}</dd>
          </div>
          <div>
            <dt>Data da auditoria anterior</dt>
            <dd>{nc.audit_date ? formatDisplayDate(nc.audit_date) : "—"}</dd>
          </div>
          <div>
            <dt>Descrição da NC</dt>
            <dd>{display(nc.description)}</dd>
          </div>
          <div>
            <dt>Observações da avaliação</dt>
            <dd>{display(nc.response_observation)}</dd>
          </div>
          <div>
            <dt>Causa raiz</dt>
            <dd>{display(nc.root_cause)}</dd>
          </div>
          <div>
            <dt>Ação corretiva</dt>
            <dd>{display(nc.corrective_action)}</dd>
          </div>
          <div>
            <dt>Responsável</dt>
            <dd>{display(nc.responsible_name)}</dd>
          </div>
          <div>
            <dt>Prazo</dt>
            <dd>{nc.due_date ? formatDisplayDate(nc.due_date) : "—"}</dd>
          </div>
        </dl>
      </div>
    </NcBoardModalShell>
  );
}
