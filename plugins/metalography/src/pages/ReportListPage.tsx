import { useCallback, useEffect, useState } from "react";
import { ActionButton, ConfirmModalPanel, NativeTextField, ScreenLoading, StateBox } from "@delpi/plugin-ui/index";

import { copyReport, deleteReport, exportPdf, listReports, type ReportFilters } from "../api/metallographicReportsApi";
import { HttpRequestError } from "../api/httpClient";
import { METALOGRAPHY_HELP } from "../content/helpTooltips";
import { allows, METALOGRAPHY_PERMISSIONS } from "../domain/permissions";
import { conclusionLabel, type ReportSnapshot } from "../domain/reportForm";
import { clearKey, idempotencyKey } from "../domain/draftSession";
import {
  confirmClassNames,
  fieldClassNames,
  MetalographyDialog,
  MetalographyEmpty,
  MetalographyPageHeader,
  ROOT_CLASS,
} from "../ui/metalographyUi";
import { createPath, editorPath, navigateMetalography } from "../utils/route";

type ReportListPageProps = {
  permissions?: readonly string[];
  isSuperadmin?: boolean;
};

const EMPTY_FILTERS: ReportFilters = { page: 1, pageSize: 20, sort: "created_at_desc" };

export function ReportListPage({ permissions, isSuperadmin }: ReportListPageProps) {
  const [filters, setFilters] = useState<ReportFilters>(EMPTY_FILTERS);
  const [draft, setDraft] = useState<ReportFilters>(EMPTY_FILTERS);
  const [items, setItems] = useState<ReportSnapshot[]>([]);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<ReportSnapshot | null>(null);

  const canView = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.view);
  const canCreate = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.create);
  const canEdit = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.edit);
  const canDelete = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.delete);
  const canExport = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.export);

  const load = useCallback(async (signal?: AbortSignal) => {
    if (!canView) {
      setForbidden(true);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await listReports(filters, signal);
      setItems(result.data.items);
      setTotal(result.data.total);
      setHasNext(result.data.has_next);
      setForbidden(false);
    } catch (cause) {
      if ((cause as Error).name === "AbortError") return;
      if (cause instanceof HttpRequestError && cause.status === 403) {
        setForbidden(true);
      } else {
        setError(cause instanceof Error ? cause.message : "Não foi possível listar os relatórios.");
      }
    } finally {
      setLoading(false);
    }
  }, [canView, filters]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function downloadPdf(report: ReportSnapshot) {
    setBusyId(report.id);
    setError(null);
    try {
      const file = await exportPdf(report.id);
      const url = URL.createObjectURL(file.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${report.report_number}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível exportar o PDF.");
    } finally {
      setBusyId(null);
    }
  }

  async function duplicate(report: ReportSnapshot) {
    setBusyId(report.id);
    setError(null);
    const storageKey = `metalography:copy:${report.id}`;
    try {
      const key = idempotencyKey(sessionStorage, storageKey, () => crypto.randomUUID());
      const created = await copyReport(report.id, key);
      clearKey(sessionStorage, storageKey);
      navigateMetalography(editorPath(created.data.id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível duplicar o relatório.");
    } finally {
      setBusyId(null);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setBusyId(pendingDelete.id);
    try {
      await deleteReport(pendingDelete.id, `"${pendingDelete.version}"`);
      setPendingDelete(null);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível excluir o relatório.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className={`${ROOT_CLASS} dashboard-page`}>
      <div className="mg-page-stack">
        <MetalographyPageHeader
          title="Relatórios Metalográficos"
          subtitle="Metalografia DELPI"
          onRefresh={() => void load()}
          refreshing={loading}
        />
        <p className="mg-help">{METALOGRAPHY_HELP.list}</p>
        {canCreate ? (
          <ActionButton type="button" variant="primary" onClick={() => navigateMetalography(createPath())}>
            Criar relatório
          </ActionButton>
        ) : null}
        <form
          className="mg-filters"
          onSubmit={(event) => {
            event.preventDefault();
            setFilters({ ...draft, page: 1, pageSize: 20, sort: draft.sort ?? "created_at_desc" });
          }}
        >
          <NativeTextField id="mg-filter-number" label="Número" classNames={fieldClassNames} value={draft.reportNumber ?? ""} onChange={(value) => setDraft({ ...draft, reportNumber: value })} />
          <NativeTextField id="mg-filter-sample" label="Amostra" classNames={fieldClassNames} value={draft.sampleIdentification ?? ""} onChange={(value) => setDraft({ ...draft, sampleIdentification: value })} />
          <NativeTextField id="mg-filter-terminal" label="Terminal" classNames={fieldClassNames} value={draft.terminalCode ?? ""} onChange={(value) => setDraft({ ...draft, terminalCode: value })} />
          <NativeTextField id="mg-filter-from" label="Período de" type="date" classNames={fieldClassNames} value={draft.reportDateFrom ?? ""} onChange={(value) => setDraft({ ...draft, reportDateFrom: value })} />
          <NativeTextField id="mg-filter-to" label="Período até" type="date" classNames={fieldClassNames} value={draft.reportDateTo ?? ""} onChange={(value) => setDraft({ ...draft, reportDateTo: value })} />
          <ActionButton type="submit" variant="primary">Pesquisar</ActionButton>
        </form>
        {forbidden ? <StateBox prefix="mg" variant="error">Você não tem permissão para consultar relatórios metalográficos.</StateBox> : null}
        {error ? <StateBox prefix="mg" variant="error">{error}</StateBox> : null}
        {loading ? <ScreenLoading label="Carregando relatórios" variant="embedded" /> : null}
        {!loading && !forbidden && items.length === 0 ? <MetalographyEmpty /> : null}
        {!loading && items.length > 0 ? (
          <div className="mg-table-wrap">
            <table className="mg-table">
              <thead>
                <tr>
                  <th>Número</th>
                  <th>Amostra</th>
                  <th>Resultado</th>
                  <th>Criação</th>
                  <th>Alteração</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((report) => (
                  <tr key={report.id}>
                    <td data-label="Número">{report.report_number}</td>
                    <td data-label="Amostra">{report.sample.sample_identification || "—"}</td>
                    <td data-label="Resultado">{conclusionLabel(report.conclusion.result)}</td>
                    <td data-label="Criação">{report.created_at ?? "—"}</td>
                    <td data-label="Alteração">{report.updated_at ?? "—"}</td>
                    <td data-label="Ações" className="mg-actions">
                      <ActionButton type="button" variant="ghost" onClick={() => navigateMetalography(editorPath(report.id, true))}>Ver</ActionButton>
                      {canEdit ? <ActionButton type="button" variant="ghost" onClick={() => navigateMetalography(editorPath(report.id))}>Editar</ActionButton> : null}
                      {canCreate ? <ActionButton type="button" variant="ghost" disabled={busyId === report.id} onClick={() => void duplicate(report)}>Duplicar</ActionButton> : null}
                      {canExport ? <ActionButton type="button" variant="ghost" disabled={busyId === report.id} onClick={() => void downloadPdf(report)}>Exportar PDF</ActionButton> : null}
                      {canDelete ? <ActionButton type="button" variant="ghost" onClick={() => setPendingDelete(report)}>Excluir</ActionButton> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <p>{total} relatório(s)</p>
        <div className="mg-actions">
          <ActionButton type="button" variant="ghost" disabled={(filters.page ?? 1) <= 1} onClick={() => setFilters({ ...filters, page: (filters.page ?? 1) - 1 })}>Anterior</ActionButton>
          <ActionButton type="button" variant="ghost" disabled={!hasNext} onClick={() => setFilters({ ...filters, page: (filters.page ?? 1) + 1 })}>Próxima</ActionButton>
        </div>
      </div>
      {pendingDelete ? (
        <MetalographyDialog open title="Excluir relatório" onClose={() => setPendingDelete(null)}>
          <ConfirmModalPanel
            classNames={confirmClassNames}
            variant="danger"
            message={`Excluir ${pendingDelete.report_number}? O relatório sai da lista, mas a exclusão é lógica.`}
            confirmLabel="Excluir"
            confirmBusy={busyId === pendingDelete.id}
            onCancel={() => setPendingDelete(null)}
            onConfirm={() => void confirmDelete()}
          />
        </MetalographyDialog>
      ) : null}
    </div>
  );
}
