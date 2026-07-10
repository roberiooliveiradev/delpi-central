import { useMemo, useRef, useState } from "react";
import {
  BarChart3,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Clock3,
  Eye,
  FileSpreadsheet,
  FileText,
  FilterX,
  Lock,
  MoreHorizontal,
  Pencil,
  Plus,
  RotateCcw,
  Search,
  Trash2,
} from "lucide-react";

import type { AuditArea, AuditListItem } from "../api/audit5sApi";
import { getAccessToken } from "../api/httpClient";
import {
  auditStatusLabel,
  auditStatusVariant,
  canAccessNc,
  canReopenEvaluation,
  ncActionLabel,
  shiftLabel,
} from "../constants/audit5s";
import {
  EMPTY_AUDIT_LIST_FILTERS,
  buildAreaNameMap,
  computeAuditListStats,
  filterAuditList,
  formatAuditDate,
  percentOf,
  scorePercentClass,
  type AuditListFilters,
} from "../utils/auditList";
import { formatPersonNamesList } from "../utils/formatPersonName";
import { getDisplayNameFromToken } from "../utils/jwt";
import { AuditRowMenuPortal } from "./AuditRowMenuPortal";
import { ListFilterSelectField } from "./filtersUi";

const PAGE_SIZE = 10;

const STATUS_FILTER_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "draft", label: "Em avaliação" },
  { value: "evaluation_complete", label: "Pendente NC's" },
  { value: "nc_in_progress", label: "NC em andamento" },
  { value: "closed", label: "Encerrada" },
];

type Props = {
  branch: string;
  audits: AuditListItem[];
  areas: AuditArea[];
  loading: boolean;
  onNew: () => void;
  onOpenDashboard: () => void;
  onOpenCatalog: () => void;
  onOpenAudit: (auditId: string) => void;
  onOpenNc: (auditId: string) => void;
  onEditAudit: (auditId: string) => void;
  onReopenAudit: (auditId: string) => Promise<void>;
  onDeleteAudit: (auditId: string, status: string) => Promise<void>;
};

function StatusBadge({ status }: { status: string }) {
  const variant = auditStatusVariant(status);
  const Icon =
    status === "closed" ? Lock : status === "draft" ? Clock3 : CheckCircle2;

  return (
    <span className={`a5s-status-badge a5s-status-badge--${variant} a5s-status-badge--table`}>
      <Icon size={13} aria-hidden />
      {auditStatusLabel(status)}
    </span>
  );
}

function primaryActionLabel(status: string): string {
  if (status === "draft") return "Continuar";
  if (canAccessNc(status)) return ncActionLabel(status);
  return "Ver avaliação";
}

function countRowMenuItems(item: AuditListItem): number {
  let count = 4;
  if (canAccessNc(item.status)) count += 1;
  if (canReopenEvaluation(item.status)) count += 1;
  if (item.status !== "closed") count += 1;
  return count;
}

export function AuditListView({
  branch,
  audits,
  areas,
  loading,
  onNew,
  onOpenDashboard,
  onOpenCatalog,
  onOpenAudit,
  onOpenNc,
  onEditAudit,
  onReopenAudit,
  onDeleteAudit,
}: Props) {
  const [filters, setFilters] = useState<AuditListFilters>(EMPTY_AUDIT_LIST_FILTERS);
  const [page, setPage] = useState(1);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<AuditListItem | null>(null);
  const [pendingReopen, setPendingReopen] = useState<AuditListItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [reopening, setReopening] = useState(false);
  const [exportingAuditId, setExportingAuditId] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const menuTriggerRef = useRef<HTMLButtonElement>(null);

  const userName = getDisplayNameFromToken(getAccessToken()) ?? "Auditor";
  const areaNameById = useMemo(() => buildAreaNameMap(areas), [areas]);

  const filteredAudits = useMemo(
    () => filterAuditList(audits, filters, areaNameById),
    [areaNameById, audits, filters],
  );

  const stats = useMemo(() => computeAuditListStats(audits), [audits]);

  const totalPages = Math.max(1, Math.ceil(filteredAudits.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageStart = filteredAudits.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const pageEnd = Math.min(currentPage * PAGE_SIZE, filteredAudits.length);
  const pageItems = filteredAudits.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const updateFilters = (patch: Partial<AuditListFilters>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
    setPage(1);
    setOpenMenuId(null);
  };

  const clearFilters = () => {
    setFilters(EMPTY_AUDIT_LIST_FILTERS);
    setPage(1);
    setOpenMenuId(null);
  };

  const handlePrimaryAction = (item: AuditListItem) => {
    if (item.status === "draft") {
      onOpenAudit(item.id);
      return;
    }
    if (canAccessNc(item.status)) {
      onOpenNc(item.id);
      return;
    }
    onOpenAudit(item.id);
  };

  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await onDeleteAudit(pendingDelete.id, pendingDelete.status);
      setPendingDelete(null);
      setOpenMenuId(null);
    } catch {
      // Erro exibido pelo Audit5sPage via banner.
    } finally {
      setDeleting(false);
    }
  };

  const handleConfirmReopen = async () => {
    if (!pendingReopen) return;
    setReopening(true);
    try {
      await onReopenAudit(pendingReopen.id);
      setPendingReopen(null);
      setOpenMenuId(null);
    } catch {
      // Erro exibido pelo Audit5sPage via banner.
    } finally {
      setReopening(false);
    }
  };

  const handleExport = async (item: AuditListItem, format: "excel" | "pdf") => {
    if (exportingAuditId) return;
    setExportError(null);
    setExportingAuditId(item.id);
    try {
      const { exportAuditExcel, exportAuditPdf, loadAuditExportData } = await import(
        "../utils/auditExport"
      );
      const data = await loadAuditExportData(item.id);
      if (format === "excel") {
        await exportAuditExcel(data);
      } else {
        await exportAuditPdf(data);
      }
      setOpenMenuId(null);
    } catch (reason) {
      setExportError(
        reason instanceof Error
          ? reason.message
          : format === "excel"
            ? "Não foi possível exportar o Excel."
            : "Não foi possível exportar o PDF.",
      );
    } finally {
      setExportingAuditId(null);
    }
  };

  return (
    <div className="a5s-dashboard">
      <div className="a5s-dashboard__welcome">
        <div>
          <h1 className="a5s-dashboard__title">Olá, {userName}!</h1>
          <p className="a5s-dashboard__subtitle">
            Aqui estão as auditorias 5S da fábrica {branch}.
          </p>
        </div>
        <div className="a5s-dashboard__actions">
          <button type="button" className="a5s-btn a5s-btn--ghost a5s-btn--header" onClick={onOpenCatalog}>
            <ListChecks size={16} aria-hidden />
            Critérios
          </button>
          <button type="button" className="a5s-btn a5s-btn--ghost a5s-btn--header" onClick={onOpenDashboard}>
            <BarChart3 size={16} aria-hidden />
            Dashboard
          </button>
          <button type="button" className="a5s-btn a5s-btn--header" onClick={onNew}>
            <Plus size={16} aria-hidden />
            Nova auditoria
          </button>
        </div>
      </div>

      <div className="a5s-stats-grid">
        <article className="a5s-stat-card a5s-stat-card--total">
          <div className="a5s-stat-card__icon" aria-hidden>
            <ClipboardList size={18} />
          </div>
          <div>
            <span className="a5s-stat-card__label">Total de auditorias</span>
            <strong className="a5s-stat-card__value">{stats.total}</strong>
          </div>
        </article>
        <article className="a5s-stat-card a5s-stat-card--completed">
          <div className="a5s-stat-card__icon" aria-hidden>
            <CheckCircle2 size={18} />
          </div>
          <div>
            <span className="a5s-stat-card__label">Concluídas</span>
            <strong className="a5s-stat-card__value">{stats.completed}</strong>
            <span className="a5s-stat-card__hint">{percentOf(stats.completed, stats.total)}% do total</span>
          </div>
        </article>
        <article className="a5s-stat-card a5s-stat-card--progress">
          <div className="a5s-stat-card__icon" aria-hidden>
            <Clock3 size={18} />
          </div>
          <div>
            <span className="a5s-stat-card__label">Em andamento</span>
            <strong className="a5s-stat-card__value">{stats.inProgress}</strong>
            <span className="a5s-stat-card__hint">{percentOf(stats.inProgress, stats.total)}% do total</span>
          </div>
        </article>
        <article className="a5s-stat-card a5s-stat-card--closed">
          <div className="a5s-stat-card__icon" aria-hidden>
            <Lock size={18} />
          </div>
          <div>
            <span className="a5s-stat-card__label">Encerradas</span>
            <strong className="a5s-stat-card__value">{stats.closed}</strong>
            <span className="a5s-stat-card__hint">{percentOf(stats.closed, stats.total)}% do total</span>
          </div>
        </article>
      </div>

      <section className="a5s-filters-card">
        <div className="a5s-filters-card__search">
          <Search size={16} aria-hidden />
          <input
            type="search"
            placeholder="Buscar auditoria..."
            value={filters.search}
            onChange={(e) => updateFilters({ search: e.target.value })}
          />
        </div>
        <ListFilterSelectField
          id="a5s-list-filter-area"
          label="Área"
          value={filters.areaId}
          onChange={(areaId) => updateFilters({ areaId })}
          options={areas.map((area) => ({ value: area.id, label: area.name }))}
          placeholderOption="Todas"
        />
        <ListFilterSelectField
          id="a5s-list-filter-status"
          label="Status"
          value={filters.status}
          onChange={(status) => updateFilters({ status })}
          options={STATUS_FILTER_OPTIONS}
        />
        <label className="a5s-filters-card__field a5s-filters-card__field--period">
          <span>Período</span>
          <div className="a5s-filters-card__period">
            <input
              type="date"
              value={filters.periodStart}
              onChange={(e) => updateFilters({ periodStart: e.target.value })}
              aria-label="Data inicial"
            />
            <input
              type="date"
              value={filters.periodEnd}
              onChange={(e) => updateFilters({ periodEnd: e.target.value })}
              aria-label="Data final"
            />
          </div>
        </label>
        <button
          type="button"
          className="a5s-btn a5s-btn--ghost a5s-btn--filter a5s-filters-card__clear"
          onClick={clearFilters}
        >
          <FilterX size={16} aria-hidden />
          Limpar filtros
        </button>
      </section>

      {exportError ? (
        <p className="a5s-alert a5s-alert--error" role="alert">
          {exportError}
        </p>
      ) : null}

      <section className="a5s-table-card">
        {loading ? (
          <p className="a5s-table-card__loading">Carregando auditorias...</p>
        ) : (
          <>
            <div className="a5s-table-wrap">
              <table className="a5s-table a5s-table--dashboard">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Data</th>
                    <th>Área</th>
                    <th>Turno</th>
                    <th>Auditores</th>
                    <th>% Geral</th>
                    <th>Status</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((item) => (
                    <tr key={item.id}>
                      <td className="a5s-table__code" data-label="Código">
                        {item.audit_code}
                      </td>
                      <td data-label="Data">{formatAuditDate(item.audit_date)}</td>
                      <td data-label="Área">{item.area_name}</td>
                      <td data-label="Turno">{shiftLabel(item.shift)}</td>
                      <td data-label="Auditores">
                        {formatPersonNamesList(item.auditor_names)}
                      </td>
                      <td data-label="% Geral">
                        <span
                          className={`a5s-score-pill ${scorePercentClass(item.overall_score_pct)}`}
                        >
                          {item.overall_score_pct != null ? `${item.overall_score_pct}%` : "—"}
                        </span>
                      </td>
                      <td data-label="Status">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="a5s-table__actions-cell" data-label="Ações">
                        <div className="a5s-table__actions a5s-table__actions--dashboard">
                          <button
                            type="button"
                            className="a5s-icon-btn a5s-icon-btn--table"
                            aria-label="Ver auditoria"
                            onClick={() => onOpenAudit(item.id)}
                          >
                            <Eye size={18} strokeWidth={2.2} aria-hidden />
                          </button>
                          <button
                            type="button"
                            className="a5s-btn a5s-btn--small a5s-btn--table-action"
                            onClick={() => handlePrimaryAction(item)}
                          >
                            {primaryActionLabel(item.status)}
                          </button>
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
                              itemCount={countRowMenuItems(item)}
                            >
                              <button
                                type="button"
                                role="menuitem"
                                onClick={() => {
                                  setOpenMenuId(null);
                                  onOpenAudit(item.id);
                                }}
                              >
                                Ver avaliação
                              </button>
                              {canAccessNc(item.status) ? (
                                <button
                                  type="button"
                                  role="menuitem"
                                  onClick={() => {
                                    setOpenMenuId(null);
                                    onOpenNc(item.id);
                                  }}
                                >
                                  {ncActionLabel(item.status)}
                                </button>
                              ) : null}
                              {canReopenEvaluation(item.status) ? (
                                <button
                                  type="button"
                                  role="menuitem"
                                  className="a5s-row-menu__item"
                                  onClick={() => {
                                    setOpenMenuId(null);
                                    setPendingReopen(item);
                                  }}
                                >
                                  <RotateCcw size={14} aria-hidden />
                                  Reabrir avaliação
                                </button>
                              ) : null}
                              {item.status !== "closed" ? (
                                <button
                                  type="button"
                                  role="menuitem"
                                  className="a5s-row-menu__item"
                                  onClick={() => {
                                    setOpenMenuId(null);
                                    onEditAudit(item.id);
                                  }}
                                >
                                  <Pencil size={14} aria-hidden />
                                  Editar cabeçalho
                                </button>
                              ) : null}
                              <button
                                type="button"
                                role="menuitem"
                                className="a5s-row-menu__item"
                                disabled={exportingAuditId === item.id}
                                onClick={() => void handleExport(item, "excel")}
                              >
                                <FileSpreadsheet size={14} aria-hidden />
                                {exportingAuditId === item.id ? "Exportando..." : "Exportar Excel"}
                              </button>
                              <button
                                type="button"
                                role="menuitem"
                                className="a5s-row-menu__item"
                                disabled={exportingAuditId === item.id}
                                onClick={() => void handleExport(item, "pdf")}
                              >
                                <FileText size={14} aria-hidden />
                                Exportar PDF
                              </button>
                              <button
                                type="button"
                                role="menuitem"
                                className="a5s-row-menu__danger"
                                onClick={() => {
                                  setOpenMenuId(null);
                                  setPendingDelete(item);
                                }}
                              >
                                <Trash2 size={14} aria-hidden />
                                Excluir auditoria
                              </button>
                            </AuditRowMenuPortal>
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {pageItems.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="a5s-table__empty">
                        Nenhuma auditoria encontrada para os filtros selecionados.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>

            <div className="a5s-pagination">
              <span>
                Mostrando {pageStart} a {pageEnd} de {filteredAudits.length} auditorias
              </span>
              <div className="a5s-pagination__controls">
                <button
                  type="button"
                  className="a5s-icon-btn"
                  aria-label="Página anterior"
                  disabled={currentPage <= 1}
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                >
                  <ChevronLeft size={16} />
                </button>
                <span className="a5s-pagination__page">{currentPage}</span>
                <button
                  type="button"
                  className="a5s-icon-btn"
                  aria-label="Próxima página"
                  disabled={currentPage >= totalPages}
                  onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {pendingReopen ? (
        <div
          className="a5s-confirm-overlay"
          role="presentation"
          onClick={() => !reopening && setPendingReopen(null)}
        >
          <div
            className="a5s-confirm-dialog"
            role="alertdialog"
            aria-labelledby="a5s-reopen-title"
            aria-describedby="a5s-reopen-desc"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="a5s-reopen-title" className="a5s-confirm-dialog__title">
              Reabrir avaliação?
            </h2>
            <p id="a5s-reopen-desc" className="a5s-confirm-dialog__text">
              A auditoria <strong>{pendingReopen.audit_code}</strong> (
              {formatAuditDate(pendingReopen.audit_date)}, {pendingReopen.area_name}) voltará para a
              fase de avaliação dos critérios. As notas já registradas serão mantidas para edição.
              {pendingReopen.status === "nc_in_progress" ? (
                <>
                  {" "}
                  Se já houver não conformidades registradas, a reabertura será bloqueada.
                </>
              ) : null}
            </p>
            <div className="a5s-confirm-dialog__actions">
              <button
                type="button"
                className="a5s-btn a5s-btn--ghost"
                disabled={reopening}
                onClick={() => setPendingReopen(null)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="a5s-btn"
                disabled={reopening}
                onClick={() => void handleConfirmReopen()}
              >
                {reopening ? "Reabrindo..." : "Reabrir avaliação"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {pendingDelete ? (
        <div className="a5s-confirm-overlay" role="presentation" onClick={() => !deleting && setPendingDelete(null)}>
          <div
            className="a5s-confirm-dialog"
            role="alertdialog"
            aria-labelledby="a5s-delete-title"
            aria-describedby="a5s-delete-desc"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="a5s-delete-title" className="a5s-confirm-dialog__title">
              {pendingDelete.status === "draft"
                ? "Excluir auditoria?"
                : "Excluir auditoria definitivamente?"}
            </h2>
            <p id="a5s-delete-desc" className="a5s-confirm-dialog__text">
              A auditoria <strong>{pendingDelete.audit_code}</strong> (
              {formatAuditDate(pendingDelete.audit_date)}, {pendingDelete.area_name}) será removida
              permanentemente junto com respostas, fotos e não conformidades vinculadas.
              {pendingDelete.status !== "draft" ? (
                <>
                  {" "}
                  O status atual é <strong>{auditStatusLabel(pendingDelete.status)}</strong> — esta
                  ação não pode ser desfeita.
                </>
              ) : (
                <> Esta ação não pode ser desfeita.</>
              )}
            </p>
            <div className="a5s-confirm-dialog__actions">
              <button
                type="button"
                className="a5s-btn a5s-btn--ghost"
                disabled={deleting}
                onClick={() => setPendingDelete(null)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="a5s-btn a5s-btn--danger"
                disabled={deleting}
                onClick={() => void handleConfirmDelete()}
              >
                {deleting ? "Excluindo..." : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
