import { Users, ClipboardList, CheckCircle2, AlertTriangle, ListChecks } from "lucide-react";
import { useEffect } from "react";

import { AuditoriaTable } from "../components/AuditoriaTable";
import { EmptyState } from "../components/EmptyState";
import { KpiCard } from "../components/KpiCard";
import { PageShell } from "../components/PageShell";
import { Pagination } from "../components/Pagination";
import {
  AUDITORIA_STATUS_ALL,
  AUDITORIA_STATUS_OPTIONS,
  type AuditoriaInspecaoStatus,
} from "../constants/auditoriaStatus";
import { branchLabel } from "../constants/branch";
import {
  AUDITORIA_SHIFT_ALL,
  AUDITORIA_SHIFT_OPTIONS,
  type AuditoriaShiftFilter,
} from "../constants/factoryShifts";
import { IP_HELP } from "../content/helpTooltips";
import { useInspecoesProcessoAuditoria } from "../hooks/useInspecoesProcessoAuditoria";
import { formatNumber } from "../utils/format";

type AuditoriaPageProps = {
  branch: string;
  active?: boolean;
  refreshToken?: number;
  onLoadingChange?: (loading: boolean) => void;
};

export function AuditoriaPage({
  branch,
  active = true,
  refreshToken = 0,
  onLoadingChange,
}: AuditoriaPageProps) {
  const {
    data,
    setData,
    status,
    setStatus,
    shift,
    setShift,
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions,
    items,
    summary,
    hasNext,
    loading,
    error,
    reload,
  } = useInspecoesProcessoAuditoria(branch, refreshToken);

  const statusLabel =
    AUDITORIA_STATUS_OPTIONS.find((option) => option.value === status)?.label ??
    status;
  const shiftLabel =
    AUDITORIA_SHIFT_OPTIONS.find((option) => option.value === shift)?.label ??
    "Todos";
  const emptyFiltered =
    !loading &&
    !error &&
    items.length === 0 &&
    (status !== AUDITORIA_STATUS_ALL || shift !== AUDITORIA_SHIFT_ALL) &&
    summary.apontamentos_total > 0;

  useEffect(() => {
    if (!active) return;
    onLoadingChange?.(loading);
  }, [active, onLoadingChange, loading]);

  return (
    <PageShell
      title="Auditoria"
      description={`Apontamentos do dia em ${branchLabel(branch)} confrontados com inspeção pelo mesmo operador (OP + operação).`}
    >
      <form
        className="ip-filters"
        aria-label="Filtros da auditoria"
        onSubmit={(event) => {
          event.preventDefault();
          reload();
        }}
      >
        <div className="ip-filters__grid">
          <label className="ip-field">
            <span className="ip-field__label">Data de produção</span>
            <input
              className="ip-input"
              type="date"
              value={data}
              onChange={(event) => setData(event.target.value)}
              required
            />
          </label>
          <label className="ip-field">
            <span className="ip-field__label">Status</span>
            <select
              className="ip-input"
              value={status}
              onChange={(event) =>
                setStatus(event.target.value as AuditoriaInspecaoStatus)
              }
              aria-label="Filtrar por status da inspeção"
            >
              {AUDITORIA_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="ip-field">
            <span
              className="ip-field__label"
              title={IP_HELP.auditoria.shift}
            >
              Turno
            </span>
            <select
              className="ip-input"
              value={shift}
              onChange={(event) =>
                setShift(event.target.value as AuditoriaShiftFilter)
              }
              aria-label="Filtrar por turno de fábrica"
              title={IP_HELP.auditoria.shift}
            >
              {AUDITORIA_SHIFT_OPTIONS.map((option) => (
                <option key={option.value || "all"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="ip-auditoria-hint">
          Cada linha é um apontamento (operador + OP + operação). Status indica se esse
          mesmo operador lançou ensaio no QIP para a mesma OP e operação. Quando a OP
          não tem inspeção amarrada naquela operação (revisão do QPK sem QP7/QP8), o
          status é «Não possui inspeção cadastrada» — não conta como pendência do
          operador.
        </p>
        <div className="ip-filters__actions">
          <button
            type="submit"
            className="ip-button ip-button--primary"
            disabled={loading}
          >
            Atualizar
          </button>
        </div>
      </form>

      <div className="ip-kpi-grid">
        <KpiCard
          title="Apontamentos no dia"
          value={formatNumber(summary.apontamentos_total)}
          subtitle="Operador + OP + operação"
          icon={<ListChecks size={22} strokeWidth={1.75} aria-hidden="true" />}
        />
        <KpiCard
          title="Pendentes"
          value={formatNumber(summary.apontamentos_pendentes)}
          subtitle="Mesmo operador não inspecionou"
          icon={
            <AlertTriangle size={22} strokeWidth={1.75} aria-hidden="true" />
          }
        />
        <KpiCard
          title="Operadores pendentes"
          value={formatNumber(summary.operadores_pendentes)}
          subtitle="Distintos com pendência"
          icon={<Users size={22} strokeWidth={1.75} aria-hidden="true" />}
        />
        <KpiCard
          title="OK (mesmo operador)"
          value={formatNumber(summary.apontamentos_com_inspecao)}
          subtitle="Apontou e inspecionou"
          icon={
            <CheckCircle2 size={22} strokeWidth={1.75} aria-hidden="true" />
          }
        />
      </div>

      {loading ? (
        <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
          <p>Carregando auditoria…</p>
        </div>
      ) : null}

      {error ? (
        <div className="ip-alert ip-alert--error" role="alert">
          <p>{error}</p>
          <button type="button" className="ip-button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title={
            emptyFiltered
              ? status !== AUDITORIA_STATUS_ALL && shift !== AUDITORIA_SHIFT_ALL
                ? `Nenhum apontamento com status «${statusLabel}» no ${shiftLabel}`
                : shift !== AUDITORIA_SHIFT_ALL
                  ? `Nenhum apontamento no ${shiftLabel}`
                  : `Nenhum apontamento com status «${statusLabel}»`
              : "Nenhum apontamento nesta data"
          }
          description={
            emptyFiltered
              ? "Os KPIs acima consideram o dia inteiro. Altere o filtro de status/turno ou escolha «Todos» para ver a lista completa."
              : "Não há apontamentos produtivos (STATUS OK) para a filial e data selecionadas."
          }
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <>
          <AuditoriaTable items={items} />
          <Pagination
            page={page}
            pageSize={pageSize}
            hasNext={hasNext}
            pageSizeOptions={pageSizeOptions}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
            loading={loading}
            ariaLabel="Paginação da auditoria"
          />
        </>
      ) : null}

      {!loading && !error && summary.apontamentos_total > 0 ? (
        <p className="ip-muted-note">
          <ClipboardList size={14} strokeWidth={1.75} aria-hidden="true" />{" "}
          Ordenação: pendências primeiro. Identidade do ensaiador via login
          (matrícula QIP → login) com fallback pelo nome.
        </p>
      ) : null}
    </PageShell>
  );
}
