import { useCallback, useEffect, useMemo, useState } from "react";

import {
  exportAdminAuditLogs,
  exportAdminAuditLogsCsv,
  getAdminAuditLogDetail,
  getAdminAuditTimeline,
  listAuditLogs,
} from "../../../../data/api/adminApi";
import type {
  AdminAuditLog,
  AdminAuditLogDetailResponse,
  AdminAuditLogsResponse,
  AdminAuditTimelineDay,
  AdminRbacSummary,
} from "../../../../data/api/adminTypes";

import { AdminTabHeader } from "../shared/AdminTabHeader";
import { AuditFiltersPanel } from "./AuditFiltersPanel";
import { AuditPagination } from "./AuditPagination";
import { AuditSummaryStrip } from "./AuditSummaryStrip";
import { AuditTablePanel } from "./AuditTablePanel";
import { AuditTimelinePanel } from "./AuditTimelinePanel";
import { DEFAULT_AUDIT_FILTERS, type AuditFilters } from "./auditTypes";

import "./AdminAuditTab.css";

type AdminAuditTabProps = {
  rbac?: AdminRbacSummary | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

const PAGE_SIZE = 25;

function filtersToQuery(filters: AuditFilters, offset: number) {
  return {
    search: filters.search || undefined,
    context: filters.context || undefined,
    action: filters.action || undefined,
    userId: filters.userId || undefined,
    traceId: filters.traceId || undefined,
    dateFrom: filters.dateFrom || undefined,
    dateTo: filters.dateTo || undefined,
    limit: PAGE_SIZE,
    offset,
  };
}

function filtersToTimelineQuery(filters: AuditFilters) {
  return {
    search: filters.search || undefined,
    context: filters.context || undefined,
    action: filters.action || undefined,
    userId: filters.userId || undefined,
    traceId: filters.traceId || undefined,
    dateFrom: filters.dateFrom || undefined,
    dateTo: filters.dateTo || undefined,
    maxDays: 31,
  };
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function formatJson(value: unknown): string {
  if (!value) {
    return "—";
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function AdminAuditTab({ rbac, getAccessToken }: AdminAuditTabProps) {
  const [filters, setFilters] = useState<AuditFilters>(DEFAULT_AUDIT_FILTERS);
  const [response, setResponse] = useState<AdminAuditLogsResponse | null>(null);
  const [timelineDays, setTimelineDays] = useState<AdminAuditTimelineDay[]>([]);
  const [selectedLog, setSelectedLog] = useState<AdminAuditLogDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canView = !rbac || rbac.capabilities.canViewAudit;
  const canExport = Boolean(rbac?.capabilities.canExportAudit);

  const page = useMemo(() => {
    if (!response) {
      return 0;
    }

    return Math.floor(response.pagination.offset / PAGE_SIZE);
  }, [response]);

  const pageCount = useMemo(() => {
    if (!response) {
      return 1;
    }

    return Math.max(1, Math.ceil(response.pagination.total / PAGE_SIZE));
  }, [response]);

  const loadLogs = useCallback(
    async (nextFilters: AuditFilters, offset = 0) => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await listAuditLogs(filtersToQuery(nextFilters, offset), {
          getAccessToken,
        });
        setResponse(result);
        setSelectedLog(null);

        try {
          const timeline = await getAdminAuditTimeline(filtersToTimelineQuery(nextFilters), {
            getAccessToken,
          });
          setTimelineDays(timeline.days);
        } catch {
          setTimelineDays([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar auditoria.");
      } finally {
        setIsLoading(false);
      }
    },
    [getAccessToken],
  );

  useEffect(() => {
    if (!canView) {
      return;
    }

    void loadLogs(DEFAULT_AUDIT_FILTERS, 0);
  }, [canView, loadLogs]);

  async function handleSelectLog(log: AdminAuditLog) {
    setError(null);

    try {
      const detail = await getAdminAuditLogDetail(log.id, { getAccessToken });
      setSelectedLog(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar detalhe do evento.");
    }
  }

  async function handleExport(nextFilters: AuditFilters) {
    setError(null);

    try {
      const exported = await exportAdminAuditLogs(filtersToQuery(nextFilters, 0), {
        getAccessToken,
      });
      downloadJson(
        `minha-delpi-audit-${new Date().toISOString().slice(0, 10)}.json`,
        exported,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar auditoria.");
    }
  }

  async function handleExportCsv(nextFilters: AuditFilters) {
    setError(null);

    try {
      const blob = await exportAdminAuditLogsCsv(filtersToQuery(nextFilters, 0), {
        getAccessToken,
      });
      downloadBlob(`minha-delpi-audit-${new Date().toISOString().slice(0, 10)}.csv`, blob);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar auditoria em CSV.");
    }
  }

  function handleFilterByTrace(traceId: string) {
    const nextFilters = {
      ...filters,
      traceId,
    };
    setFilters(nextFilters);
    void loadLogs(nextFilters, 0);
  }

  if (!canView) {
    return (
      <section className="mdc-admin-audit-tab">
        <article className="mdc-admin-audit-empty">
          <p className="mdc-chat-eyebrow">Auditoria</p>
          <h2>Acesso bloqueado</h2>
          <p>Você não tem permissão para visualizar auditoria.</p>
        </article>
      </section>
    );
  }

  const logs = response?.items ?? [];

  const auditTableFooter = response ? (
    <div className="mdc-admin-data-table__footer">
      <AuditPagination
        page={page}
        pageCount={pageCount}
        onPrevious={() => {
          if (!response.pagination.hasPrevious) {
            return;
          }

          void loadLogs(filters, Math.max(0, response.pagination.offset - PAGE_SIZE));
        }}
        onNext={() => {
          if (!response.pagination.hasNext) {
            return;
          }

          void loadLogs(filters, response.pagination.offset + PAGE_SIZE);
        }}
      />
    </div>
  ) : null;

  return (
    <section className="mdc-admin-audit-tab">
      <AdminTabHeader
        className="mdc-admin-audit-tab__toolbar"
        eyebrow="Governança"
        title="Eventos administrativos"
        description="Consulte, filtre e exporte ações registradas pelo Minha DELPI Chat para rastreabilidade operacional."
        summary={
          <AuditSummaryStrip
            logs={logs}
            total={response?.pagination.total}
            timelineDayCount={timelineDays.length}
            isLoading={isLoading}
          />
        }
        actions={
          <button
            type="button"
            className="mdc-chat-ws-outline-btn"
            disabled={isLoading}
            onClick={() => void loadLogs(filters, response?.pagination.offset ?? 0)}
          >
            {isLoading ? "Atualizando..." : "Atualizar"}
          </button>
        }
      />

      {error ? <p className="mdc-admin-audit-error">{error}</p> : null}

      <AuditFiltersPanel
        filters={filters}
        onChange={setFilters}
        canExport={canExport}
        reloadAuditLogs={(nextFilters) => loadLogs(nextFilters, 0)}
        exportAuditLogs={handleExport}
        exportAuditLogsCsv={handleExportCsv}
      />

      <AuditTimelinePanel
        days={timelineDays}
        onSelectLog={(logId) => {
          const log = logs.find((item) => item.id === logId);

          if (log) {
            void handleSelectLog(log);
          }
        }}
        onFilterByTrace={handleFilterByTrace}
      />

      {isLoading ? <p className="mdc-chat-muted">Carregando eventos...</p> : null}

      <AuditTablePanel
        logs={logs}
        onSelectLog={handleSelectLog}
        footer={auditTableFooter}
      />

      {selectedLog ? (
        <article className="mdc-admin-panel mdc-admin-audit-detail">
          <header>
            <p className="mdc-chat-eyebrow">Detalhe do evento</p>
            <h3>{selectedLog.log.action}</h3>
          </header>

          <dl className="mdc-admin-audit-detail__meta">
            <div>
              <dt>Contexto</dt>
              <dd>{selectedLog.log.context || "—"}</dd>
            </div>
            <div>
              <dt>Usuário</dt>
              <dd>{selectedLog.log.userId || "—"}</dd>
            </div>
            <div>
              <dt>Hash do prompt</dt>
              <dd>{selectedLog.log.promptHash || "—"}</dd>
            </div>
            <div>
              <dt>Trace ID</dt>
              <dd>
                {selectedLog.log.traceId ? (
                  <button type="button" onClick={() => handleFilterByTrace(selectedLog.log.traceId!)}>
                    {selectedLog.log.traceId}
                  </button>
                ) : (
                  "—"
                )}
              </dd>
            </div>
            <div>
              <dt>Data</dt>
              <dd>{new Date(selectedLog.log.createdAt).toLocaleString("pt-BR")}</dd>
            </div>
          </dl>

          <details open>
            <summary>Metadata</summary>
            <pre>{formatJson(selectedLog.log.metadata)}</pre>
          </details>

          {Array.isArray(selectedLog.log.toolCalls) && selectedLog.log.toolCalls.length > 0 ? (
            <details>
              <summary>Tool calls</summary>
              <pre>{formatJson(selectedLog.log.toolCalls)}</pre>
            </details>
          ) : null}

          {(selectedLog.traceRelatedLogs ?? []).length > 0 ? (
            <section className="mdc-admin-audit-detail__related">
              <h4>Eventos correlacionados (mesmo traceId)</h4>
              <ul>
                {(selectedLog.traceRelatedLogs ?? []).map((related) => (
                  <li key={related.id}>
                    <button type="button" onClick={() => void handleSelectLog(related)}>
                      <strong>{related.action}</strong>
                      <span>{new Date(related.createdAt).toLocaleString("pt-BR")}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {selectedLog.relatedLogs.length > 0 ? (
            <section className="mdc-admin-audit-detail__related">
              <h4>Eventos correlacionados (mesmo promptHash)</h4>
              <ul>
                {selectedLog.relatedLogs.map((related) => (
                  <li key={related.id}>
                    <button type="button" onClick={() => void handleSelectLog(related)}>
                      <strong>{related.action}</strong>
                      <span>{new Date(related.createdAt).toLocaleString("pt-BR")}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
