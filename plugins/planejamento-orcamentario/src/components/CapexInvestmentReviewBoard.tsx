import { useState } from "react";
import {
  Check,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Paperclip,
  X,
  XCircle,
} from "lucide-react";

import type {
  CapexCategory,
  CapexInvestment,
  CapexInvestmentAttachment,
} from "../types/budgetPlanning";
import { attachmentTypeLabel } from "../utils/capexAttachments";
import {
  classificationLabel,
  excerptText,
  formatMoneyBr,
  investmentAccentTone,
  investmentReviewLabel,
  investmentReviewStatus,
  originLabel,
  priorityLabel,
  priorityTone,
  requiredDateMonthLabel,
  shiftLabel,
} from "../utils/capexInvestments";
import { CapexCategoryVisual } from "./CapexCategoryVisual";
import { SectionCard, StateBox } from "./uiKit";

type Props = {
  investments: CapexInvestment[];
  categoryMap: Map<string, CapexCategory>;
  attachmentsByInv: Record<string, CapexInvestmentAttachment[]>;
  canDecide: boolean;
  decidingId: string | null;
  onApprove: (investment: CapexInvestment) => void;
  onReject: (investment: CapexInvestment, comment: string) => void;
  onDownload: (attachment: CapexInvestmentAttachment) => void;
};

function ReviewStatusIcon({ status }: { status: string }) {
  if (status === "approved") return <CheckCircle2 size={16} aria-hidden="true" />;
  if (status === "rejected") return <XCircle size={16} aria-hidden="true" />;
  return <Clock3 size={16} aria-hidden="true" />;
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="po-inv-detail__field">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function CapexInvestmentReviewBoard({
  investments,
  categoryMap,
  attachmentsByInv,
  canDecide,
  decidingId,
  onApprove,
  onReject,
  onDownload,
}: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(
    investments.length === 1 ? investments[0]?.id ?? null : null,
  );
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectComment, setRejectComment] = useState("");
  const [rejectError, setRejectError] = useState<string | null>(null);

  function toggleExpanded(id: string) {
    setExpandedId((current) => (current === id ? null : id));
  }

  function startReject(id: string) {
    setExpandedId(id);
    setRejectingId(id);
    setRejectComment("");
    setRejectError(null);
  }

  function cancelReject() {
    setRejectingId(null);
    setRejectComment("");
    setRejectError(null);
  }

  function confirmReject(row: CapexInvestment) {
    if (!rejectComment.trim()) {
      setRejectError("Justificativa obrigatória para reprovar.");
      return;
    }
    onReject(row, rejectComment.trim());
    cancelReject();
  }

  return (
    <SectionCard
      title="Investimentos para decisão"
      hint="Aprove ou reprove cada item. Abra os detalhes para ver observações, justificativa e anexos."
    >
      {investments.length === 0 ? (
        <StateBox variant="default" dismissible={false}>
          Nenhum investimento ativo neste planejamento.
        </StateBox>
      ) : (
        <ul className="po-review-inv">
          {investments.map((row) => {
            const cat = row.category_id ? categoryMap.get(row.category_id) : null;
            const accent = investmentAccentTone(row.category_id || row.id);
            const pTone = priorityTone(row.priority);
            const review = investmentReviewStatus(row);
            const attachments = attachmentsByInv[row.id] ?? [];
            const expanded = expandedId === row.id;
            const busy = decidingId === row.id;
            const label = row.description?.trim() || "(Sem descrição)";
            const notePreview =
              excerptText(row.observations) ||
              excerptText(row.justification) ||
              excerptText(row.application);
            const noteKind = row.observations?.trim()
              ? "Observação"
              : row.justification?.trim()
                ? "Justificativa"
                : row.application?.trim()
                  ? "Aplicação"
                  : null;
            const supplier = row.probable_supplier_name?.trim()
              ? `${row.probable_supplier_name.trim()}${
                  row.probable_supplier_code ? ` (${row.probable_supplier_code})` : ""
                }`
              : "—";

            return (
              <li
                key={row.id}
                className={`po-review-inv__card po-review-inv__card--${accent} po-review-inv__card--${review}${
                  expanded ? " is-open" : ""
                }`}
              >
                <div className="po-review-inv__accent" aria-hidden="true" />
                <div className="po-review-inv__main">
                  <div className="po-review-inv__identity">
                    <span className={`po-cockpit-inv__icon po-cockpit-inv__icon--${accent}`} aria-hidden="true">
                      <CapexCategoryVisual
                        categoryId={cat?.id}
                        iconKey={cat?.icon_key}
                        hasCustomIcon={Boolean(cat?.has_custom_icon)}
                        size={18}
                        alt=""
                      />
                    </span>
                    <div className="po-review-inv__titles">
                      <strong className="po-review-inv__title">{label}</strong>
                      <span className="po-review-inv__subtitle">
                        {cat?.name || "Sem categoria"}
                        {row.required_date
                          ? ` · ${requiredDateMonthLabel(row.required_date)}`
                          : ""}
                      </span>
                    </div>
                  </div>

                  <div className="po-review-inv__amount" data-label="Valor">
                    {formatMoneyBr(row.estimated_amount, row.currency)}
                  </div>

                  <div className="po-review-inv__priority" data-label="Prioridade">
                    <span className={`po-cockpit-inv__priority po-cockpit-inv__priority--${pTone}`}>
                      {priorityLabel(row.priority)}
                    </span>
                  </div>

                  <div className="po-review-inv__status" data-label="Decisão">
                    <span className={`po-review-inv__badge po-review-inv__badge--${review}`}>
                      <ReviewStatusIcon status={review} />
                      {investmentReviewLabel(review)}
                    </span>
                  </div>
                </div>

                {notePreview ? (
                  <p className="po-review-inv__excerpt">
                    <span>{noteKind}</span>
                    {notePreview}
                  </p>
                ) : (
                  <p className="po-review-inv__excerpt po-review-inv__excerpt--empty">
                    Sem observações registradas pelo responsável.
                  </p>
                )}

                {row.review_comment?.trim() && review === "rejected" ? (
                  <p className="po-review-inv__excerpt po-review-inv__excerpt--reject">
                    <span>Motivo da reprovação</span>
                    {row.review_comment.trim()}
                  </p>
                ) : null}

                <div className="po-review-inv__toolbar">
                  <button
                    type="button"
                    className="po-btn po-btn--secondary po-btn--sm"
                    aria-expanded={expanded}
                    onClick={() => toggleExpanded(row.id)}
                  >
                    <ChevronDown
                      size={16}
                      aria-hidden="true"
                      className={`po-review-inv__chevron${expanded ? " is-open" : ""}`}
                    />
                    {expanded ? "Ocultar detalhes" : "Ver detalhes"}
                    {attachments.length > 0 ? (
                      <span className="po-review-inv__attach-count">
                        <Paperclip size={14} aria-hidden="true" />
                        {attachments.length}
                      </span>
                    ) : null}
                  </button>

                  {canDecide ? (
                    <div className="po-review-inv__actions">
                      <button
                        type="button"
                        className="po-btn po-btn--primary po-btn--sm"
                        disabled={Boolean(decidingId) || review === "approved"}
                        onClick={() => onApprove(row)}
                      >
                        <Check size={16} aria-hidden="true" />
                        {busy && review !== "rejected" ? "Aprovando…" : "Aprovar"}
                      </button>
                      <button
                        type="button"
                        className="po-btn po-btn--secondary po-btn--sm po-review-inv__reject"
                        disabled={Boolean(decidingId) || review === "rejected"}
                        onClick={() => startReject(row.id)}
                      >
                        <X size={16} aria-hidden="true" />
                        Reprovar
                      </button>
                    </div>
                  ) : null}
                </div>

                {expanded ? (
                  <div className="po-review-inv__details">
                    <dl className="po-inv-detail__grid">
                      <DetailField
                        label="Mês necessário"
                        value={
                          row.required_date
                            ? requiredDateMonthLabel(row.required_date)
                            : "—"
                        }
                      />
                      <DetailField label="Origem" value={originLabel(row.origin)} />
                      <DetailField
                        label="Classificação"
                        value={classificationLabel(row.classification)}
                      />
                      <DetailField label="Turno" value={shiftLabel(row.shift)} />
                      <DetailField label="Fornecedor" value={supplier} />
                      <DetailField
                        label="Decidido por"
                        value={row.reviewed_by_name?.trim() || "—"}
                      />
                    </dl>

                    {row.justification?.trim() ? (
                      <section className="po-inv-detail__block">
                        <h3>Justificativa</h3>
                        <p>{row.justification.trim()}</p>
                      </section>
                    ) : null}

                    {row.application?.trim() ? (
                      <section className="po-inv-detail__block">
                        <h3>Aplicação</h3>
                        <p>{row.application.trim()}</p>
                      </section>
                    ) : null}

                    {row.observations?.trim() ? (
                      <section className="po-inv-detail__block">
                        <h3>Observações</h3>
                        <p>{row.observations.trim()}</p>
                      </section>
                    ) : null}

                    {attachments.length > 0 ? (
                      <section className="po-inv-detail__block">
                        <h3>Anexos</h3>
                        <ul className="po-link-list">
                          {attachments.map((att) => (
                            <li key={att.id}>
                              <button
                                type="button"
                                className="po-btn po-btn--secondary po-btn--sm"
                                onClick={() => onDownload(att)}
                              >
                                {att.display_name} · {attachmentTypeLabel(att.attachment_type)}
                              </button>
                            </li>
                          ))}
                        </ul>
                      </section>
                    ) : (
                      <p className="po-muted">Sem anexos ativos.</p>
                    )}

                    {rejectingId === row.id ? (
                      <div className="po-review-inv__reject-box">
                        <label className="po-field">
                          <span>Justificativa da reprovação</span>
                          <textarea
                            rows={3}
                            value={rejectComment}
                            onChange={(event) => {
                              setRejectComment(event.target.value);
                              setRejectError(null);
                            }}
                            placeholder="Explique o motivo para o responsável"
                            disabled={Boolean(decidingId)}
                          />
                        </label>
                        {rejectError ? (
                          <StateBox variant="error" dismissible={false}>
                            {rejectError}
                          </StateBox>
                        ) : null}
                        <div className="po-form-actions">
                          <button
                            type="button"
                            className="po-btn po-btn--secondary"
                            onClick={cancelReject}
                            disabled={Boolean(decidingId)}
                          >
                            Cancelar
                          </button>
                          <button
                            type="button"
                            className="po-btn po-btn--primary po-review-inv__reject"
                            onClick={() => confirmReject(row)}
                            disabled={Boolean(decidingId)}
                          >
                            {busy ? "Reprovando…" : "Confirmar reprovação"}
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </SectionCard>
  );
}
