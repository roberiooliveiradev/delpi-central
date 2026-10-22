import { useEffect, useState } from "react";
import { ActionButton, FieldLabel, HintAction } from "@delpi/plugin-ui/index";

import type { ClassificationPatch, TicketDetail } from "../api/helpdeskApi";
import type { HelpdeskAssigneeValue } from "../components/HelpdeskAssigneePicker";
import { helpTooltips } from "../content/helpTooltips";
import { absoluteDateTimeLabel } from "../presentation/ticketView";
import { approvalSummaryCounts } from "../presentation/ticketValidationView";
import { HelpdeskSelect } from "../ui/helpdeskUi";
import { HelpdeskAssignPopover } from "./HelpdeskAssignPopover";

export type ClassificationCatalogs = {
  categories: { id: number; name: string }[];
  urgencies: { id: number; name: string }[];
  impacts: { id: number; name: string }[];
  ticketTypes: { id: number; name: string }[];
  requestTypes: { id: number; name: string }[];
};

type CatalogItem = { id: number; name: string };

const toOptions = (items: CatalogItem[]) =>
  items.map((item) => ({ value: String(item.id), label: item.name }));

export function TicketDetailsSurface({
  ticket,
  assigneePick,
  onAssigneeChange,
  onAssignConfirm,
  assignSaving,
  onOpenApprovals,
  classificationCatalogs,
  classificationEditing = false,
  classificationSaving = false,
  onClassificationEditStart,
  onClassificationEditCancel,
  onClassificationSave,
}: {
  ticket: TicketDetail;
  assigneePick: HelpdeskAssigneeValue | null;
  onAssigneeChange: (user: HelpdeskAssigneeValue | null) => void;
  onAssignConfirm: () => void;
  assignSaving: boolean;
  onOpenApprovals: () => void;
  classificationCatalogs?: ClassificationCatalogs | null;
  classificationEditing?: boolean;
  classificationSaving?: boolean;
  onClassificationEditStart?: () => void;
  onClassificationEditCancel?: () => void;
  onClassificationSave?: (patch: ClassificationPatch) => void;
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

  // Classification edit draft — string ids for the selects; seeded from
  // the authoritative projection every time edit mode opens.
  const canUpdateClassification = ticket.can_update_classification === true;
  const [editCategory, setEditCategory] = useState("");
  const [editUrgency, setEditUrgency] = useState("");
  const [editImpact, setEditImpact] = useState("");
  const [editType, setEditType] = useState("");
  const [editRequestType, setEditRequestType] = useState("");
  useEffect(() => {
    if (!classificationEditing) return;
    setEditCategory(ticket.category_id ? String(ticket.category_id) : "");
    setEditUrgency(ticket.urgency_id ? String(ticket.urgency_id) : "");
    setEditImpact(ticket.impact_id ? String(ticket.impact_id) : "");
    setEditType(ticket.type_id ? String(ticket.type_id) : "");
    setEditRequestType(ticket.request_type_id ? String(ticket.request_type_id) : "");
  }, [
    classificationEditing,
    ticket.category_id,
    ticket.urgency_id,
    ticket.impact_id,
    ticket.type_id,
    ticket.request_type_id,
  ]);

  const draft = {
    category_id: Number(editCategory) || null,
    urgency_id: Number(editUrgency) || null,
    impact_id: Number(editImpact) || null,
    type_id: Number(editType) || null,
    request_type_id: Number(editRequestType) || null,
  };
  const patch: ClassificationPatch = {};
  for (const field of Object.keys(draft) as (keyof typeof draft)[]) {
    const next = draft[field];
    if (next !== null && next !== ticket[field]) patch[field] = next;
  }
  const hasChanges = Object.keys(patch).length > 0;

  const requestTypeName = classificationCatalogs?.requestTypes.find(
    (item) => item.id === ticket.request_type_id,
  )?.name;

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

      <section
        className="helpdesk-ticket-details__section"
        aria-labelledby="helpdesk-details-classification"
      >
        <h2 id="helpdesk-details-classification" className="helpdesk-ticket-details__title">
          Classificação
        </h2>
        {classificationEditing ? (
          <div className="helpdesk-classification-form">
            <HelpdeskSelect
              label="Categoria"
              hint={helpTooltips.detailUi.classificationCategory}
              value={editCategory}
              onChange={setEditCategory}
              required
              searchable
              options={toOptions(classificationCatalogs?.categories ?? [])}
            />
            <HelpdeskSelect
              label="Tipo"
              hint={helpTooltips.detailUi.classificationType}
              value={editType}
              onChange={setEditType}
              required
              options={toOptions(classificationCatalogs?.ticketTypes ?? [])}
            />
            <HelpdeskSelect
              label="Urgência"
              hint={helpTooltips.detailUi.classificationUrgency}
              value={editUrgency}
              onChange={setEditUrgency}
              required
              options={toOptions(classificationCatalogs?.urgencies ?? [])}
            />
            <HelpdeskSelect
              label="Impacto"
              hint={helpTooltips.detailUi.classificationImpact}
              value={editImpact}
              onChange={setEditImpact}
              required
              options={toOptions(classificationCatalogs?.impacts ?? [])}
            />
            <HelpdeskSelect
              label="Origem"
              hint={helpTooltips.detailUi.classificationRequestType}
              value={editRequestType}
              onChange={setEditRequestType}
              required
              options={toOptions(classificationCatalogs?.requestTypes ?? [])}
            />
            <div className="helpdesk-ticket-details__row">
              <dt>
                <FieldLabel
                  label="Prioridade"
                  hint={helpTooltips.detailUi.classificationPriorityDerived}
                />
              </dt>
              <dd>{ticket.priority || "—"}</dd>
            </div>
            <div className="helpdesk-classification-form__actions">
              <HintAction
                hint={helpTooltips.detailUi.classificationCancel}
                ariaLabel="Ajuda: Cancelar edição"
              >
                <ActionButton
                  variant="ghost"
                  type="button"
                  onClick={onClassificationEditCancel}
                  disabled={classificationSaving}
                >
                  Cancelar
                </ActionButton>
              </HintAction>
              <HintAction
                hint={helpTooltips.detailUi.classificationSave}
                ariaLabel="Ajuda: Salvar classificação"
              >
                <ActionButton
                  variant="primary"
                  type="button"
                  onClick={() => onClassificationSave?.(patch)}
                  disabled={classificationSaving || !hasChanges}
                  aria-label={classificationSaving ? "Salvando" : "Salvar classificação"}
                >
                  {classificationSaving ? "Salvando…" : "Salvar"}
                </ActionButton>
              </HintAction>
            </div>
          </div>
        ) : (
          <>
            <dl className="helpdesk-ticket-details__list">
              <div className="helpdesk-ticket-details__row">
                <dt>Categoria</dt>
                <dd>{ticket.category || "—"}</dd>
              </div>
              <div className="helpdesk-ticket-details__row">
                <dt>Tipo</dt>
                <dd>{ticket.type_name || "—"}</dd>
              </div>
              <div className="helpdesk-ticket-details__row">
                <dt>Urgência</dt>
                <dd>{ticket.urgency || "—"}</dd>
              </div>
              <div className="helpdesk-ticket-details__row">
                <dt>Impacto</dt>
                <dd>{ticket.impact || "—"}</dd>
              </div>
              <div className="helpdesk-ticket-details__row">
                <dt>Origem</dt>
                <dd>{requestTypeName || "—"}</dd>
              </div>
              <div className="helpdesk-ticket-details__row">
                <dt>
                  <FieldLabel
                    label="Prioridade"
                    hint={helpTooltips.detailUi.classificationPriorityDerived}
                  />
                </dt>
                <dd>{ticket.priority || "—"}</dd>
              </div>
            </dl>
            {canUpdateClassification && onClassificationEditStart ? (
              <HintAction
                hint={helpTooltips.detailUi.classificationEdit}
                ariaLabel="Ajuda: Editar classificação"
              >
                <ActionButton
                  variant="ghost"
                  type="button"
                  className="helpdesk-ticket-details__link"
                  onClick={onClassificationEditStart}
                >
                  Editar classificação
                </ActionButton>
              </HintAction>
            ) : null}
          </>
        )}
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
