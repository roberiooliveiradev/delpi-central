import { Pencil, Trash2 } from "lucide-react";

import type { CapexCategory, CapexInvestment } from "../types/budgetPlanning";
import {
  classificationLabel,
  formatMoneyBr,
  investmentAccentTone,
  investmentSituation,
  investmentStatusLabel,
  missingFieldLabel,
  originLabel,
  priorityLabel,
  priorityTone,
  requiredDateMonthLabel,
  shiftLabel,
} from "../utils/capexInvestments";
import { CapexCategoryVisual } from "./CapexCategoryVisual";
import { HostContainedDialog } from "./uiKit";

type CapexInvestmentDetailModalProps = {
  investment: CapexInvestment | null;
  category: CapexCategory | null;
  planEditable: boolean;
  planStatus?: string | null;
  onClose: () => void;
  onEdit: (id: string) => void;
  onDelete: (row: CapexInvestment) => void;
};

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="po-inv-detail__field">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function CapexInvestmentDetailModal({
  investment,
  category,
  planEditable,
  planStatus = null,
  onClose,
  onEdit,
  onDelete,
}: CapexInvestmentDetailModalProps) {
  const open = Boolean(investment);
  const title = investment?.description?.trim() || "Detalhe do investimento";

  if (!investment) {
    return (
      <HostContainedDialog open={false} title={title} onClose={onClose}>
        {null}
      </HostContainedDialog>
    );
  }

  const accent = investmentAccentTone(investment.category_id || investment.id);
  const pTone = priorityTone(investment.priority);
  const situation = investmentSituation(investment, { planStatus });
  const canDelete = investment.status === "draft" && planEditable;
  const editLabel = investment.status === "archived" || !planEditable ? "Ver cadastro" : "Editar";

  return (
    <HostContainedDialog
      open={open}
      title={title}
      description={category?.name || "Sem categoria"}
      onClose={onClose}
    >
      <article className={`po-inv-detail po-inv-detail--${accent}`}>
        <div className="po-inv-detail__summary">
          <span className={`po-inv-detail__icon po-inv-detail__icon--${accent}`} aria-hidden="true">
            <CapexCategoryVisual
              categoryId={category?.id}
              iconKey={category?.icon_key}
              hasCustomIcon={Boolean(category?.has_custom_icon)}
              size={26}
              alt=""
            />
          </span>
          <div className="po-inv-detail__amount-block">
            <span className="po-inv-detail__amount-label">Valor solicitado</span>
            <strong className="po-inv-detail__amount">
              {formatMoneyBr(investment.estimated_amount, investment.currency)}
            </strong>
          </div>
          <div className="po-inv-detail__badges">
            <span className={`po-cockpit-inv__priority po-cockpit-inv__priority--${pTone}`}>
              {priorityLabel(investment.priority)}
            </span>
            <span className={`po-cockpit-inv__situation po-cockpit-inv__situation--${situation.tone}`}>
              {situation.label}
            </span>
          </div>
        </div>

        <dl className="po-inv-detail__grid">
          <DetailField
            label="Mês necessário"
            value={
              investment.required_date
                ? requiredDateMonthLabel(investment.required_date)
                : "—"
            }
          />
          <DetailField label="Origem" value={originLabel(investment.origin)} />
          <DetailField
            label="Classificação"
            value={classificationLabel(investment.classification)}
          />
          <DetailField label="Turno" value={shiftLabel(investment.shift)} />
          <DetailField
            label="Fornecedor"
            value={investment.probable_supplier_name?.trim() || "—"}
          />
          <DetailField label="Status" value={investmentStatusLabel(investment.status)} />
        </dl>

        {investment.justification?.trim() ? (
          <section className="po-inv-detail__block">
            <h3>Justificativa</h3>
            <p>{investment.justification.trim()}</p>
          </section>
        ) : null}

        {investment.application?.trim() ? (
          <section className="po-inv-detail__block">
            <h3>Aplicação</h3>
            <p>{investment.application.trim()}</p>
          </section>
        ) : null}

        {investment.observations?.trim() ? (
          <section className="po-inv-detail__block">
            <h3>Observações</h3>
            <p>{investment.observations.trim()}</p>
          </section>
        ) : null}

        {!investment.is_complete && investment.missing_fields?.length ? (
          <section className="po-inv-detail__pendencies">
            <h3>Pendências</h3>
            <ul>
              {investment.missing_fields.map((field) => (
                <li key={field}>{missingFieldLabel(field)}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <footer className="po-inv-detail__footer">
          <button type="button" className="po-btn po-btn--secondary" onClick={onClose}>
            Fechar
          </button>
          <div className="po-inv-detail__footer-actions">
            {canDelete ? (
              <button
                type="button"
                className="po-btn po-btn--secondary po-cockpit-inv__danger"
                onClick={() => onDelete(investment)}
              >
                <Trash2 size={16} aria-hidden="true" />
                Excluir
              </button>
            ) : null}
            <button
              type="button"
              className="po-btn po-btn--primary"
              onClick={() => onEdit(investment.id)}
            >
              <Pencil size={16} aria-hidden="true" />
              {editLabel}
            </button>
          </div>
        </footer>
      </article>
    </HostContainedDialog>
  );
}
