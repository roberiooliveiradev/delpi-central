import type { AuditBackendPlaceholders, AuditFilters } from "./auditTypes";

import "./AuditFiltersPanel.css";

type AuditFiltersPanelProps = AuditBackendPlaceholders & {
  filters: AuditFilters;
  onChange: (filters: AuditFilters) => void;
};

export function AuditFiltersPanel({
  filters,
  onChange,
  reloadAuditLogs,
  exportAuditLogs,
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
          placeholder="Ação, usuário ou contexto"
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
          placeholder="Ex.: document.deleted"
          onChange={(event) => updateFilter("action", event.target.value)}
        />
      </label>

      <label>
        <span>Usuário</span>
        <input
          value={filters.userId}
          placeholder="ID do usuário"
          onChange={(event) => updateFilter("userId", event.target.value)}
        />
      </label>

      <div className="mdc-audit-filters__actions">
        <button
          type="button"
          disabled={!reloadAuditLogs}
          title={reloadAuditLogs ? "Recarregar auditoria" : "Aguardando endpoint paginado"}
          onClick={() => {
            void reloadAuditLogs?.(filters);
          }}
        >
          Recarregar
        </button>

        <button
          type="button"
          disabled={!exportAuditLogs}
          title={exportAuditLogs ? "Exportar auditoria" : "Aguardando endpoint de exportação"}
          onClick={() => {
            void exportAuditLogs?.(filters);
          }}
        >
          Exportar
        </button>
      </div>
    </section>
  );
}
