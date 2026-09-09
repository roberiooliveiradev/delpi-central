import { HintAction } from "@delpi/plugin-ui/index";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import type { AuditBackendPlaceholders, AuditFilters } from "./auditTypes";
import { ChatAdminNativeTextField } from "../shared/chatAdminFormFields";

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

  const fields = ADMIN_HELP.fields.audit;

  return (
    <section className="mdc-admin-panel mdc-audit-filters" aria-label="Filtros de auditoria">
      <div className="mdc-admin-filter-bar">
        <ChatAdminNativeTextField
          id="audit-filter-search"
          className="mdc-admin-filter-bar__search"
          label="Buscar"
          hint={fields.search}
          value={filters.search}
          placeholder="Ação, usuário, contexto ou hash"
          onChange={(value) => updateFilter("search", value)}
        />

        <div className="mdc-admin-filter-bar__row">
          <ChatAdminNativeTextField
            id="audit-filter-context"
            label="Contexto"
            hint={fields.context}
            value={filters.context}
            placeholder="Ex.: admin, chat, knowledge"
            onChange={(value) => updateFilter("context", value)}
          />
          <ChatAdminNativeTextField
            id="audit-filter-action"
            label="Ação"
            hint={fields.action}
            value={filters.action}
            placeholder="Ex.: envio de mensagem"
            onChange={(value) => updateFilter("action", value)}
          />
          <ChatAdminNativeTextField
            id="audit-filter-user"
            label="Usuário"
            hint={fields.userId}
            value={filters.userId}
            placeholder="Identificador do usuário"
            onChange={(value) => updateFilter("userId", value)}
          />
          <ChatAdminNativeTextField
            id="audit-filter-trace"
            label="Trace ID"
            hint={fields.traceId}
            value={filters.traceId}
            placeholder="Correlacionar requisição / fluxo"
            onChange={(value) => updateFilter("traceId", value)}
          />
          <ChatAdminNativeTextField
            id="audit-filter-date-from"
            label="Data inicial"
            hint={fields.dateFrom}
            type="date"
            value={filters.dateFrom}
            onChange={(value) => updateFilter("dateFrom", value)}
          />
          <ChatAdminNativeTextField
            id="audit-filter-date-to"
            label="Data final"
            hint={fields.dateTo}
            type="date"
            value={filters.dateTo}
            onChange={(value) => updateFilter("dateTo", value)}
          />
        </div>
      </div>

      <div className="mdc-audit-filters__actions">
        <button
          type="button"
          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
          disabled={!reloadAuditLogs}
          onClick={() => {
            void reloadAuditLogs?.(filters);
          }}
        >
          Aplicar filtros
        </button>

        <HintAction hint={fields.exportJson} ariaLabel="Ajuda: Exportar JSON">
          <button
            type="button"
            className="mdc-chat-ws-outline-btn"
            disabled={!exportAuditLogs || !canExport}
            title={canExport ? "Exportar JSON" : "Sem permissão para exportar"}
            onClick={() => {
              void exportAuditLogs?.(filters);
            }}
          >
            Exportar JSON
          </button>
        </HintAction>

        <HintAction hint={fields.exportCsv} ariaLabel="Ajuda: Exportar CSV">
          <button
            type="button"
            className="mdc-chat-ws-outline-btn"
            disabled={!exportAuditLogsCsv || !canExport}
            title={canExport ? "Exportar CSV" : "Sem permissão para exportar"}
            onClick={() => {
              void exportAuditLogsCsv?.(filters);
            }}
          >
            Exportar CSV
          </button>
        </HintAction>
      </div>
    </section>
  );
}
