import { useEffect, useMemo, useState } from "react";

import type { AuditArea, AuditListItem } from "../api/audit5sApi";
import type { NcBoardItem } from "../types/ncManagement";
import { formatRelativeUpdate } from "../utils/auditNc";
import { NcBoardNotesModal } from "../components/NcBoardNotesModal";
import { NcBoardTreatModal } from "../components/NcBoardTreatModal";
import { NcBoardViewModal } from "../components/NcBoardViewModal";
import { NcManagementFilters } from "../components/NcManagementFilters";
import { NcManagementKpis } from "../components/NcManagementKpis";
import { NcManagementTable } from "../components/NcManagementTable";
import { useAudit5sNcBoard } from "../hooks/useAudit5sNcBoard";
import { useAudit5sNcBoardFilters } from "../hooks/useAudit5sNcBoardFilters";

type Props = {
  branch: string;
  areas: AuditArea[];
  audits: AuditListItem[];
};

type NcBoardModalMode = "view" | "edit" | "notes";

type NcBoardModalState = {
  mode: NcBoardModalMode;
  item: NcBoardItem;
} | null;

export function NcManagementPage({ branch, areas, audits }: Props) {
  const [modalState, setModalState] = useState<NcBoardModalState>(null);
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
              onPageChange={filters.setPage}
              onView={(item) => setModalState({ mode: "view", item })}
              onEdit={(item) => setModalState({ mode: "edit", item })}
              onNotes={(item) => setModalState({ mode: "notes", item })}
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
    </div>
  );
}
