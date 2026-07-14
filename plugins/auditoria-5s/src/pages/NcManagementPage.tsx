import { useEffect, useMemo, useState } from "react";

import { reopenNcAction, type AuditArea, type AuditListItem } from "../api/audit5sApi";
import type { NcBoardItem } from "../types/ncManagement";
import { formatRelativeUpdate } from "../utils/auditNc";
import { NcBoardNotesModal } from "../components/NcBoardNotesModal";
import { NcBoardTreatModal } from "../components/NcBoardTreatModal";
import { NcBoardViewModal } from "../components/NcBoardViewModal";
import { NcManagementFilters } from "../components/NcManagementFilters";
import { NcManagementKpis } from "../components/NcManagementKpis";
import { NcManagementTable } from "../components/NcManagementTable";
import { useAudit5sAdminPermission } from "../hooks/useAudit5sAdminPermission";
import { useAudit5sNcBoard } from "../hooks/useAudit5sNcBoard";
import { useAudit5sNcBoardFilters } from "../hooks/useAudit5sNcBoardFilters";

type Props = {
  branch: string;
  pathname?: string;
  areas: AuditArea[];
  audits: AuditListItem[];
};

type NcBoardModalMode = "view" | "edit" | "notes";

type NcBoardModalState = {
  mode: NcBoardModalMode;
  item: NcBoardItem;
} | null;

export function NcManagementPage({ branch, pathname, areas, audits }: Props) {
  const [modalState, setModalState] = useState<NcBoardModalState>(null);
  const [pendingReopen, setPendingReopen] = useState<NcBoardItem | null>(null);
  const [reopening, setReopening] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const { canAdmin } = useAudit5sAdminPermission(branch, pathname);
  const filters = useAudit5sNcBoardFilters(branch, audits);
  const { data, loading, error, reload, lastUpdatedAt, isRefreshing } = useAudit5sNcBoard(
    filters.apiParams,
  );

  const [knownResponsibles, setKnownResponsibles] = useState<string[]>([]);

  useEffect(() => {
    if (!data?.items.length) return;
    setKnownResponsibles((current) => {
      const names = new Set(current);
      for (const item of data.items) {
        const name = item.responsible_name?.trim();
        if (name) names.add(name);
      }
      return Array.from(names).sort((a, b) => a.localeCompare(b, "pt-BR"));
    });
  }, [data]);

  const responsibleOptions = useMemo(() => {
    const names = new Set(knownResponsibles);
    const selected = filters.filters.responsible.trim();
    if (selected) names.add(selected);
    return Array.from(names).sort((a, b) => a.localeCompare(b, "pt-BR"));
  }, [knownResponsibles, filters.filters.responsible]);

  async function handleConfirmReopen() {
    if (!pendingReopen || reopening) return;
    setReopening(true);
    setActionError(null);
    try {
      await reopenNcAction(pendingReopen.id);
      setPendingReopen(null);
      await reload();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Não foi possível reabrir a ação corretiva.",
      );
    } finally {
      setReopening(false);
    }
  }

  return (
    <div className="a5s-nc-board">
      <NcManagementFilters
        areas={areas}
        dateStart={filters.filters.dateStart}
        dateEnd={filters.filters.dateEnd}
        areaId={filters.filters.areaId}
        status={filters.filters.status}
        responsible={filters.filters.responsible}
        responsibleOptions={responsibleOptions}
        overdueOnly={filters.filters.overdueOnly}
        loading={loading}
        lastUpdatedLabel={formatRelativeUpdate(lastUpdatedAt)}
        onDateStartChange={filters.setDateStart}
        onDateEndChange={filters.setDateEnd}
        onAreaIdChange={filters.setAreaId}
        onStatusChange={filters.setStatus}
        onResponsibleChange={filters.setResponsible}
        onOverdueOnlyChange={filters.setOverdueOnly}
        onReload={reload}
      />

      {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}
      {actionError ? <div className="a5s-alert a5s-alert--error">{actionError}</div> : null}

      {loading && !data ? (
        <p className="a5s-nc-board-loading">Carregando não conformidades…</p>
      ) : null}

      {data ? (
        <div
          className={
            isRefreshing
              ? "a5s-nc-board__content a5s-nc-board__content--refresh"
              : "a5s-nc-board__content"
          }
        >
          <NcManagementKpis summary={data.summary} />

          {data.summary.nc_total === 0 ? (
            <div className="a5s-alert a5s-alert--success">
              Nenhuma não conformidade encontrada no período com os filtros selecionados.
            </div>
          ) : (
            <NcManagementTable
              items={data.items}
              pagination={data.pagination}
              canAdmin={canAdmin}
              onPageChange={filters.setPage}
              onView={(item) => setModalState({ mode: "view", item })}
              onEdit={(item) => setModalState({ mode: "edit", item })}
              onNotes={(item) => setModalState({ mode: "notes", item })}
              onReopen={(item) => {
                setActionError(null);
                setPendingReopen(item);
              }}
            />
          )}
        </div>
      ) : null}

      <NcBoardViewModal
        item={modalState?.mode === "view" ? modalState.item : null}
        open={modalState?.mode === "view"}
        onClose={() => setModalState(null)}
      />

      <NcBoardTreatModal
        item={modalState?.mode === "edit" ? modalState.item : null}
        open={modalState?.mode === "edit"}
        onClose={() => setModalState(null)}
        onSaved={reload}
      />

      <NcBoardNotesModal
        item={modalState?.mode === "notes" ? modalState.item : null}
        open={modalState?.mode === "notes"}
        onClose={() => setModalState(null)}
        onSaved={reload}
      />

      {pendingReopen ? (
        <div
          className="a5s-confirm-overlay"
          role="presentation"
          onClick={() => !reopening && setPendingReopen(null)}
        >
          <div
            className="a5s-confirm-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="a5s-reopen-nc-title"
            aria-describedby="a5s-reopen-nc-desc"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="a5s-reopen-nc-title" className="a5s-confirm-dialog__title">
              Reabrir ação corretiva?
            </h2>
            <p id="a5s-reopen-nc-desc" className="a5s-confirm-dialog__text">
              A NC da auditoria <strong>{pendingReopen.audit_code}</strong> voltará para
              tratamento. Se a auditoria estiver encerrada, ela será reaberta para
              acompanhamento das ações.
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
                className="a5s-btn a5s-btn--primary"
                disabled={reopening}
                onClick={() => void handleConfirmReopen()}
              >
                {reopening ? "Reabrindo…" : "Reabrir ação"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
