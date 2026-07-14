import { useRef, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  MessageSquarePlus,
  MoreHorizontal,
  Pencil,
  RotateCcw,
} from "lucide-react";

import type { NcBoardItem, NcBoardPagination } from "../types/ncManagement";
import {
  sensoName,
  shiftLabel,
} from "../constants/audit5s";
import { formatDisplayDate } from "../utils/dates";
import { resolveNcBoardRowStatus } from "../utils/ncDueSla";
import { AuditRowMenuPortal } from "./AuditRowMenuPortal";
import { NcWorkflowPill } from "./NcWorkflowPill";

type Props = {
  items: NcBoardItem[];
  pagination: NcBoardPagination;
  canAdmin?: boolean;
  onPageChange: (page: number) => void;
  onView: (item: NcBoardItem) => void;
  onEdit: (item: NcBoardItem) => void;
  onNotes: (item: NcBoardItem) => void;
  onReopen?: (item: NcBoardItem) => void;
};

function truncateText(value: string | null | undefined, max = 72): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1)}…`;
}

export function NcManagementTable({
  items,
  pagination,
  canAdmin = false,
  onPageChange,
  onView,
  onEdit,
  onNotes,
  onReopen,
}: Props) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const menuTriggerRef = useRef<HTMLButtonElement>(null);
  const totalPages = pagination.total_pages || 1;
  const canPrev = pagination.page > 1;
  const canNext = pagination.page < totalPages;

  function canReopenAction(item: NcBoardItem): boolean {
    return (
      canAdmin &&
      Boolean(onReopen) &&
      item.is_registered !== false &&
      item.status === "closed"
    );
  }

  return (
    <section className="a5s-nc-board-table-section">
      <header className="a5s-nc-board-table-section__head">
        <h2>Não conformidades</h2>
        <span>
          {pagination.total} registro{pagination.total === 1 ? "" : "s"}
        </span>
      </header>

      <div className="a5s-table-wrap a5s-nc-board-table-wrap">
        <table className="a5s-table a5s-nc-board-table">
          <thead>
            <tr>
              <th>Auditoria</th>
              <th>Área / turno</th>
              <th>O que foi encontrado</th>
              <th>Progresso</th>
              <th>Ação corretiva</th>
              <th>Responsável</th>
              <th>Prazo</th>
              <th>Status</th>
              <th aria-label="Ações" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={9} className="a5s-table__empty a5s-nc-board-table__empty">
                  Nenhuma não conformidade encontrada com os filtros atuais.
                </td>
              </tr>
            ) : (
              items.map((item) => {
                const rowStatus = resolveNcBoardRowStatus(item);
                const showReopen = canReopenAction(item);
                const menuItemCount = 3 + (showReopen ? 1 : 0);
                return (
                <tr
                  key={item.id}
                  className={
                    rowStatus.tone === "overdue"
                      ? "a5s-nc-board-table__row--overdue"
                      : undefined
                  }
                >
                  <td data-label="Auditoria">
                    <div className="a5s-nc-board-audit">
                      <strong>{item.audit_code}</strong>
                      <span>{formatDisplayDate(item.audit_date)}</span>
                    </div>
                  </td>
                  <td data-label="Área / turno">
                    <div className="a5s-nc-board-area">
                      <strong>{item.area_name}</strong>
                      <span>
                        {shiftLabel(item.shift)} · {sensoName(item.senso_order, item.senso_name)}
                      </span>
                    </div>
                  </td>
                  <td data-label="O que foi encontrado">
                    <span
                      className="a5s-nc-board-finding"
                      title={item.description?.trim() || undefined}
                    >
                      {truncateText(item.description, 120)}
                    </span>
                  </td>
                  <td data-label="Progresso">
                    <NcWorkflowPill
                      planStarted={item.plan_started}
                      workflowStep={item.workflow_step}
                      status={item.status}
                    />
                  </td>
                  <td data-label="Ação corretiva">
                    <span className="a5s-nc-board-action" title={item.corrective_action ?? undefined}>
                      {truncateText(item.corrective_action)}
                    </span>
                  </td>
                  <td data-label="Responsável">
                    <span className="a5s-nc-board-responsible">
                      {item.responsible_name?.trim() || "—"}
                    </span>
                  </td>
                  <td data-label="Prazo">
                    <span>{item.due_date ? formatDisplayDate(item.due_date) : "—"}</span>
                  </td>
                  <td data-label="Status">
                    <span
                      className={`a5s-nc-board-row-status a5s-nc-board-row-status--${rowStatus.tone}`}
                      title={rowStatus.hint}
                    >
                      {rowStatus.label}
                    </span>
                  </td>
                  <td className="a5s-nc-board-table__actions-cell" data-label="Ações">
                    <div className="a5s-table__actions a5s-table__actions--dashboard">
                      <div className="a5s-row-menu">
                        <button
                          ref={openMenuId === item.id ? menuTriggerRef : undefined}
                          type="button"
                          className="a5s-icon-btn a5s-icon-btn--table"
                          aria-label="Mais ações"
                          aria-expanded={openMenuId === item.id}
                          aria-haspopup="menu"
                          onClick={() =>
                            setOpenMenuId((current) => (current === item.id ? null : item.id))
                          }
                        >
                          <MoreHorizontal size={18} strokeWidth={2.2} aria-hidden />
                        </button>
                        <AuditRowMenuPortal
                          open={openMenuId === item.id}
                          onClose={() => setOpenMenuId(null)}
                          triggerRef={menuTriggerRef}
                          itemCount={menuItemCount}
                        >
                          <button
                            type="button"
                            role="menuitem"
                            className="a5s-row-menu__item"
                            onClick={() => {
                              setOpenMenuId(null);
                              onView(item);
                            }}
                          >
                            <Eye size={14} aria-hidden />
                            Ver
                          </button>
                          <button
                            type="button"
                            role="menuitem"
                            className="a5s-row-menu__item"
                            onClick={() => {
                              setOpenMenuId(null);
                              onEdit(item);
                            }}
                          >
                            <Pencil size={14} aria-hidden />
                            Atualizar
                          </button>
                          <button
                            type="button"
                            role="menuitem"
                            className="a5s-row-menu__item"
                            disabled={!item.is_registered}
                            title={
                              item.is_registered
                                ? undefined
                                : "Registre o plano de ação antes de incluir notas."
                            }
                            onClick={() => {
                              setOpenMenuId(null);
                              onNotes(item);
                            }}
                          >
                            <MessageSquarePlus size={14} aria-hidden />
                            Notas
                          </button>
                          {showReopen ? (
                            <button
                              type="button"
                              role="menuitem"
                              className="a5s-row-menu__item"
                              onClick={() => {
                                setOpenMenuId(null);
                                onReopen?.(item);
                              }}
                            >
                              <RotateCcw size={14} aria-hidden />
                              Reabrir ação
                            </button>
                          ) : null}
                        </AuditRowMenuPortal>
                      </div>
                    </div>
                  </td>
                </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {pagination.total > pagination.page_size ? (
        <div className="a5s-table-pagination">
          <button
            type="button"
            className="a5s-btn a5s-btn--ghost a5s-btn--small"
            disabled={!canPrev}
            onClick={() => onPageChange(pagination.page - 1)}
          >
            <ChevronLeft size={16} aria-hidden />
            Anterior
          </button>
          <span>
            Página {pagination.page} de {totalPages}
          </span>
          <button
            type="button"
            className="a5s-btn a5s-btn--ghost a5s-btn--small"
            disabled={!canNext}
            onClick={() => onPageChange(pagination.page + 1)}
          >
            Próxima
            <ChevronRight size={16} aria-hidden />
          </button>
        </div>
      ) : null}
    </section>
  );
}
