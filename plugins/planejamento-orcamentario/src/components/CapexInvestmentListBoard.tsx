import { useEffect, useId, useRef, useState } from "react";
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  CircleDot,
  Clock3,
  MoreVertical,
  Pencil,
  Trash2,
} from "lucide-react";

import type { CapexCategory, CapexInvestment } from "../types/budgetPlanning";
import {
  formatMoneyBr,
  investmentAccentTone,
  investmentSituation,
  priorityLabel,
  priorityTone,
} from "../utils/capexInvestments";
import { CapexCategoryVisual } from "./CapexCategoryVisual";
import { CapexInvestmentDetailModal } from "./CapexInvestmentDetailModal";

type Props = {
  items: CapexInvestment[];
  categoryMap: Map<string, CapexCategory>;
  planEditable: boolean;
  /** Status do plano do centro — atualiza a coluna Situação após envio/aprovação. */
  planStatus?: string | null;
  onEdit: (id: string) => void;
  onDelete: (row: CapexInvestment) => void;
};

function SituationIcon({ tone }: { tone: string }) {
  if (tone === "ok") return <CheckCircle2 size={16} aria-hidden="true" />;
  if (tone === "warn") return <AlertTriangle size={16} aria-hidden="true" />;
  if (tone === "muted") return <Archive size={16} aria-hidden="true" />;
  if (tone === "info") return <Clock3 size={16} aria-hidden="true" />;
  return <CircleDot size={16} aria-hidden="true" />;
}

function RowActionsMenu({
  row,
  planEditable,
  onEdit,
  onDelete,
}: {
  row: CapexInvestment;
  planEditable: boolean;
  onEdit: (id: string) => void;
  onDelete: (row: CapexInvestment) => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const canDelete = row.status === "draft" && planEditable;
  const editLabel = row.status === "archived" || !planEditable ? "Ver" : "Editar";

  useEffect(() => {
    if (!open) return;
    const onDoc = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div
      className="po-cockpit-inv__menu"
      ref={rootRef}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      <button
        type="button"
        className="po-cockpit-inv__menu-trigger"
        aria-label="Ações do investimento"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((v) => !v)}
      >
        <MoreVertical size={18} aria-hidden="true" />
      </button>
      {open ? (
        <div id={menuId} className="po-cockpit-inv__menu-panel" role="menu">
          <button
            type="button"
            role="menuitem"
            className="po-cockpit-inv__menu-item"
            onClick={() => {
              setOpen(false);
              onEdit(row.id);
            }}
          >
            <Pencil size={14} aria-hidden="true" />
            {editLabel}
          </button>
          {canDelete ? (
            <button
              type="button"
              role="menuitem"
              className="po-cockpit-inv__menu-item po-cockpit-inv__menu-item--danger"
              onClick={() => {
                setOpen(false);
                onDelete(row);
              }}
            >
              <Trash2 size={14} aria-hidden="true" />
              Excluir
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function CapexInvestmentListBoard({
  items,
  categoryMap,
  planEditable,
  planStatus = null,
  onEdit,
  onDelete,
}: Props) {
  const [detailId, setDetailId] = useState<string | null>(null);
  const detail = detailId ? items.find((row) => row.id === detailId) ?? null : null;
  const detailCategory =
    detail?.category_id != null ? categoryMap.get(detail.category_id) ?? null : null;

  const openDetail = (id: string) => setDetailId(id);
  const closeDetail = () => setDetailId(null);

  const handleEditFromDetail = (id: string) => {
    closeDetail();
    onEdit(id);
  };

  const handleDeleteFromDetail = (row: CapexInvestment) => {
    closeDetail();
    onDelete(row);
  };

  return (
    <div className="po-cockpit-inv-board">
      <div className="po-cockpit-inv-board__head" aria-hidden="true">
        <span>Investimento</span>
        <span>Valor solicitado</span>
        <span>Prioridade</span>
        <span>Situação</span>
        <span>Ações</span>
      </div>
      <ul className="po-cockpit-inv">
        {items.map((row) => {
          const cat = row.category_id ? categoryMap.get(row.category_id) : null;
          const accent = investmentAccentTone(row.category_id || row.id);
          const pTone = priorityTone(row.priority);
          const situation = investmentSituation(row, { planStatus });
          const incomplete = !row.is_complete && planEditable;
          const label = row.description?.trim() || "(Sem descrição)";

          return (
            <li
              key={row.id}
              className={`po-cockpit-inv__row po-cockpit-inv__row--clickable po-cockpit-inv__row--${accent}${
                incomplete ? " is-incomplete" : " is-complete"
              }`}
            >
              <button
                type="button"
                className="po-cockpit-inv__hit"
                aria-label={`Ver detalhes de ${label}`}
                onClick={() => openDetail(row.id)}
              />
              <div className="po-cockpit-inv__accent" aria-hidden="true" />

              <div className="po-cockpit-inv__col po-cockpit-inv__col--invest">
                <span className={`po-cockpit-inv__icon po-cockpit-inv__icon--${accent}`} aria-hidden="true">
                  <CapexCategoryVisual
                    categoryId={cat?.id}
                    iconKey={cat?.icon_key}
                    hasCustomIcon={Boolean(cat?.has_custom_icon)}
                    size={18}
                    alt=""
                  />
                </span>
                <div className="po-cockpit-inv__identity">
                  <strong className="po-cockpit-inv__title">{label}</strong>
                  <span className="po-cockpit-inv__subtitle">
                    {cat?.name || "Sem categoria"}
                  </span>
                </div>
              </div>

              <div className="po-cockpit-inv__col po-cockpit-inv__col--amount" data-label="Valor solicitado">
                <span className="po-cockpit-inv__amount">
                  {formatMoneyBr(row.estimated_amount, row.currency)}
                </span>
              </div>

              <div className="po-cockpit-inv__col po-cockpit-inv__col--priority" data-label="Prioridade">
                <span className={`po-cockpit-inv__priority po-cockpit-inv__priority--${pTone}`}>
                  {priorityLabel(row.priority)}
                </span>
              </div>

              <div className="po-cockpit-inv__col po-cockpit-inv__col--situation" data-label="Situação">
                <span className={`po-cockpit-inv__situation po-cockpit-inv__situation--${situation.tone}`}>
                  <SituationIcon tone={situation.tone} />
                  {situation.label}
                </span>
              </div>

              <div className="po-cockpit-inv__col po-cockpit-inv__col--actions">
                <RowActionsMenu
                  row={row}
                  planEditable={planEditable}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              </div>
            </li>
          );
        })}
      </ul>

      <CapexInvestmentDetailModal
        investment={detail}
        category={detailCategory}
        planEditable={planEditable}
        planStatus={planStatus}
        onClose={closeDetail}
        onEdit={handleEditFromDetail}
        onDelete={handleDeleteFromDetail}
      />
    </div>
  );
}
