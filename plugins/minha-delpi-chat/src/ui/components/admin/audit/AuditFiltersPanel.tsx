import type { AuditBackendPlaceholders, AuditFilters } from "./auditTypes";

import "./AuditFiltersPanel.css";

type AuditFiltersPanelProps = AuditBackendPlaceholders & {
  filters: AuditFilters;
  onChange: (filters: AuditFilters) => void;
  canExport?: boolean;
};

export function AuditFiltersPanel({
  filters,
  onChange,
  reloadAuditLogs,
  exportAuditLogs,
  exportAuditLogsCsv,
  canExport = false,
}: AuditFiltersPanelProps) {
  function updateFilter(key: keyof AuditFilters, value: string) {
    onChange({
      ...filters,
      [key]: value,
    });
  }

  return (
    <section className="mdc-audit-filters" aria-label="Filtros de auditoria">
      <label>
        <span>Buscar</span>
        <input
          value={filters.search}
          placeholder="Ação, usuário, contexto ou hash"
          onChange={(event) => updateFilter("search", event.target.value)}
        />
      </label>

      <label>
        <span>Contexto</span>
        <input
          value={filters.context}
          placeholder="Ex.: admin, chat, knowledge"
          onChange={(event) => updateFilter("context", event.target.value)}
        />
      </label>

      <label>
        <span>Ação</span>
        <input
          value={filters.action}
          placeholder="Ex.: chat.message.sent"
          onChange={(event) => updateFilter("action", event.target.value)}
        />
      </label>

      <label>
        <span>Usuário</span>
        <input
          value={filters.userId}
          placeholder="UUID do usuário"
          onChange={(event) => updateFilter("userId", event.target.value)}
        />
      </label>

      <label>
        <span>Trace ID</span>
        <input
          value={filters.traceId}
          placeholder="Correlacionar requisição / fluxo"
          onChange={(event) => updateFilter("traceId", event.target.value)}
        />
      </label>

      <label>
        <span>Data inicial</span>
        <input
          type="date"
          value={filters.dateFrom}
          onChange={(event) => updateFilter("dateFrom", event.target.value)}
        />
      </label>

      <label>
        <span>Data final</span>
        <input
          type="date"
          value={filters.dateTo}
          onChange={(event) => updateFilter("dateTo", event.target.value)}
        />
      </label>

      <div className="mdc-audit-filters__actions">
        <button
          type="button"
          disabled={!reloadAuditLogs}
          onClick={() => {
            void reloadAuditLogs?.(filters);
          }}
        >
          Aplicar filtros
        </button>

        <button
          type="button"
          disabled={!exportAuditLogs || !canExport}
          title={canExport ? "Exportar JSON" : "Sem permissão para exportar"}
          onClick={() => {
            void exportAuditLogs?.(filters);
          }}
        >
          Exportar JSON
        </button>

        <button
          type="button"
          disabled={!exportAuditLogsCsv || !canExport}
          title={canExport ? "Exportar CSV" : "Sem permissão para exportar"}
          onClick={() => {
            void exportAuditLogsCsv?.(filters);
          }}
        >
          Exportar CSV
        </button>
      </div>
    </section>
  );
}
