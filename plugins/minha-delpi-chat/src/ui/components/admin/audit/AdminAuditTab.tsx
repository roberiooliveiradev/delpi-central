import { useMemo, useState } from "react";

import type { AdminAuditLog } from "../../../../data/api/adminTypes";
import { AuditFiltersPanel } from "./AuditFiltersPanel";
import { AuditPagination } from "./AuditPagination";
import { AuditSummaryPanel } from "./AuditSummaryPanel";
import { AuditTablePanel } from "./AuditTablePanel";
import type { AuditBackendPlaceholders, AuditFilters } from "./auditTypes";

import "./AdminAuditTab.css";

type AdminAuditTabProps = AuditBackendPlaceholders & {
  auditLogs: AdminAuditLog[];
};

const PAGE_SIZE = 10;

const EMPTY_FILTERS: AuditFilters = {
  search: "",
  context: "",
  action: "",
  userId: "",
};

function includesNormalized(value: string | null | undefined, search: string) {
  return String(value ?? "").toLowerCase().includes(search.toLowerCase());
}

export function AdminAuditTab({
  auditLogs,
  reloadAuditLogs,
  exportAuditLogs,
}: AdminAuditTabProps) {
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<AuditFilters>(EMPTY_FILTERS);

  const filteredLogs = useMemo(() => {
    return auditLogs.filter((log) => {
      const search = filters.search.trim();

      if (
        search &&
        !includesNormalized(log.action, search) &&
        !includesNormalized(log.context, search) &&
        !includesNormalized(log.userId, search)
      ) {
        return false;
      }

      if (filters.context.trim() && !includesNormalized(log.context, filters.context.trim())) {
        return false;
      }

      if (filters.action.trim() && !includesNormalized(log.action, filters.action.trim())) {
        return false;
      }

      if (filters.userId.trim() && !includesNormalized(log.userId, filters.userId.trim())) {
        return false;
      }

      return true;
    });
  }, [auditLogs, filters]);

  const pageCount = Math.max(1, Math.ceil(filteredLogs.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);

  const visibleLogs = useMemo(() => {
    const start = safePage * PAGE_SIZE;
    return filteredLogs.slice(start, start + PAGE_SIZE);
  }, [filteredLogs, safePage]);

  function handleFilterChange(nextFilters: AuditFilters) {
    setFilters(nextFilters);
    setPage(0);
  }

  return (
    <article className="mdc-admin-audit">
      <div className="mdc-admin-audit__header">
        <div>
          <p className="mdc-chat-eyebrow">Auditoria</p>
          <h2>Auditoria recente</h2>
          <p className="mdc-chat-muted">
            Eventos operacionais, ingestões, exclusões, mensagens e uso administrativo.
          </p>
        </div>

        <span>{filteredLogs.length} evento(s)</span>
      </div>

      <AuditSummaryPanel auditLogs={filteredLogs} />

      <AuditFiltersPanel
        filters={filters}
        onChange={handleFilterChange}
        reloadAuditLogs={reloadAuditLogs}
        exportAuditLogs={exportAuditLogs}
      />

      <AuditTablePanel logs={visibleLogs} />

      <AuditPagination
        page={safePage}
        pageCount={pageCount}
        onPrevious={() => setPage((current) => Math.max(0, current - 1))}
        onNext={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
      />
    </article>
  );
}
