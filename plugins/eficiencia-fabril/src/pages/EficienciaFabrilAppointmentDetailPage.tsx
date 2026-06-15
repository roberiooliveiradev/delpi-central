import { useMemo } from "react";
import { ArrowLeft, Boxes, CircleGauge, Clock3, Factory, RefreshCw } from "lucide-react";

import { ProductStructureTree } from "../components/ProductStructureTree";
import { AppointmentTimeFindings } from "../components/AppointmentTimeFindings";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS } from "../constants/branches";
import { isProductionEfficiencyLow, isProductionEfficiencyOutlier } from "../constants/businessRules";
import { buildEficienciaFabrilDashboardPath } from "../constants/routes";
import { useProductionOeeAppointmentDetail } from "../hooks/useProductionOeeAppointmentDetail";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import { formatDisplayDate } from "../utils/dates";
import { formatDecimal, formatHours, formatInteger, formatPercent, formatProductionQuantity } from "../utils/format";
import { navigateEficienciaFabrilBack } from "../utils/navigation";

type EficienciaFabrilAppointmentDetailPageProps = {
  appointmentId: string;
  branchRoute: BranchRouteCode;
  branch?: string;
};

function formatDateTime(date?: string | null, time?: string | null): string {
  const dateLabel = formatDisplayDate(date);
  const timeLabel = time?.trim();
  if (dateLabel === "—" && !timeLabel) return "—";
  if (!timeLabel) return dateLabel;
  return `${dateLabel} ${timeLabel}`;
}

function formatRealHoursSource(source?: string | null): string {
  if (source === "interval") return "Início/fim do apontamento";
  if (source === "h6_tempo") return "H6_TEMPO (fallback)";
  return "—";
}

export function EficienciaFabrilAppointmentDetailPage({
  appointmentId,
  branchRoute,
  branch,
}: EficienciaFabrilAppointmentDetailPageProps) {
  const detail = useProductionOeeAppointmentDetail(appointmentId, { branch });
  const appointment = detail.appointment;
  const timeAnalysis = detail.timeAnalysis;
  const backPath = buildEficienciaFabrilDashboardPath(branchRoute);
  const initialFetchProgress = useTrackedSingleFetchProgress(detail.loading);
  const initialLoadingProgress = useLoadingProgress(detail.loading, initialFetchProgress);

  const appointmentFields = useMemo(
    () =>
      appointment
        ? [
            {
              label: "Status",
              value: isProductionEfficiencyOutlier(appointment.oee_pct) ? (
                <span className="ef-badge ef-badge--danger">Verificar</span>
              ) : isProductionEfficiencyLow(appointment.oee_pct) ? (
                <span className="ef-badge ef-badge--warning">Eficiência baixa</span>
              ) : (
                <span className="ef-badge">OK</span>
              ),
            },
            { label: "Filial", value: appointment.branch || "—" },
            { label: "Apontamento", value: formatInteger(appointment.appointment_id) },
            { label: "OP", value: appointment.production_order || "—" },
            { label: "Produto", value: appointment.product_code || "—" },
            {
              label: "Descrição",
              value: appointment.product_description || "—",
              wide: true,
            },
            { label: "Unidade", value: appointment.unit || "—" },
            { label: "CT", value: appointment.work_center || "—" },
            { label: "Operação", value: appointment.operation || "—" },
            {
              label: "Descrição operação",
              value: appointment.operation_description || "—",
              wide: true,
            },
            {
              label: "Recurso",
              value: appointment.resource_name || appointment.resource_code || "—",
            },
            { label: "Operador", value: appointment.operator_code || "—" },
            {
              label: "Data produção",
              value: formatDisplayDate(appointment.production_date),
            },
            {
              label: "Início",
              value: formatDateTime(appointment.start_date, appointment.start_time),
            },
            {
              label: "Fim",
              value: formatDateTime(appointment.end_date, appointment.end_time),
            },
            {
              label: "Qtd. apontada",
              value: formatProductionQuantity(appointment.produced_qty, appointment.unit),
            },
            {
              label: "Eficiência (view)",
              value: formatPercent(appointment.oee_pct),
            },
          ]
        : [],
    [appointment]
  );

  const timeFields = useMemo(
    () =>
      timeAnalysis
        ? [
            { label: "Setup (h)", value: formatHours(timeAnalysis.setup_hours) },
            {
              label: "Fator padrão",
              value: formatDecimal(timeAnalysis.standard_time_factor, 6),
            },
            {
              label: "Qtd. OP",
              value: formatProductionQuantity(
                timeAnalysis.order_planned_qty,
                appointment?.unit
              ),
            },
            {
              label: "Qtd. apontada",
              value: formatProductionQuantity(timeAnalysis.produced_qty, appointment?.unit),
            },
            {
              label: "Tempo previsto",
              value: formatHours(timeAnalysis.planned_hours),
            },
            {
              label: "Tempo real",
              value: formatHours(timeAnalysis.real_hours),
            },
            {
              label: "Fonte tempo real",
              value: formatRealHoursSource(timeAnalysis.real_hours_source),
            },
            {
              label: "Variação (real − previsto)",
              value: formatHours(timeAnalysis.time_variance_hours),
            },
            {
              label: "Ganho/perda de tempo",
              value: formatHours(timeAnalysis.time_gained_lost_hours),
            },
            {
              label: "Eficiência (tempos)",
              value: formatPercent(timeAnalysis.efficiency_from_times_pct),
            },
            {
              label: "OEE registrado (SH6010)",
              value: formatPercent(timeAnalysis.oee_pct),
            },
            {
              label: "Fórmula previsto",
              value: timeAnalysis.formula_planned,
              wide: true,
            },
            {
              label: "Fórmula real",
              value: timeAnalysis.formula_real,
              wide: true,
            },
            {
              label: "Fórmula eficiência",
              value: timeAnalysis.formula_efficiency,
              wide: true,
            },
          ]
        : [],
    [timeAnalysis, appointment?.unit]
  );

  const pageTitle = appointment
    ? `Apontamento ${appointment.appointment_id}`
    : `Apontamento ${appointmentId}`;

  const pageSubtitle = appointment
    ? `OP ${appointment.production_order} · ${appointment.product_code} · CT ${appointment.work_center}`
    : `${BRANCH_ROUTE_LABELS[branchRoute]} · detalhe do apontamento`;

  return (
    <div className="dashboard-eficiencia-fabril dashboard-page">
      <div className="ef-app-shell">
        <header className="ef-page-header">
          <div>
            <h1>{pageTitle}</h1>
            <p>{pageSubtitle}</p>
          </div>
          <div className="ef-page-header__actions">
            <button
              type="button"
              className="ef-btn ef-btn--ghost"
              onClick={detail.reload}
              disabled={detail.loading}
            >
              <RefreshCw size={16} aria-hidden />
              Atualizar
            </button>
            <button
              type="button"
              className="ef-btn ef-btn--ghost"
              onClick={() => navigateEficienciaFabrilBack(backPath)}
            >
              <ArrowLeft size={16} aria-hidden />
              Voltar
            </button>
          </div>
        </header>

        {detail.error ? (
          <div className="ef-alert ef-alert--error" role="alert">
            <p>{detail.error}</p>
            <button type="button" className="ef-btn ef-btn--primary" onClick={detail.reload}>
              Tentar novamente
            </button>
          </div>
        ) : null}

        {detail.loading && !appointment ? (
          <LoadingActivityCard
            title="Carregando apontamento"
            description="Consultando apontamento, roteiro, estrutura e análise de tempos."
            progressPercent={initialLoadingProgress}
          />
        ) : null}

        {appointment ? (
          <>
            <section className="ef-kpi-grid" aria-busy={detail.loading}>
              <KpiCard
                label="Eficiência (view)"
                value={formatPercent(appointment.oee_pct)}
                hint="EFICIENCIA_PERCENTUAL"
                icon={<CircleGauge size={22} aria-hidden />}
              />
              <KpiCard
                label="Eficiência (tempos)"
                value={formatPercent(timeAnalysis?.efficiency_from_times_pct)}
                hint={timeAnalysis?.formula_efficiency ?? "Previsto ÷ real"}
                icon={<Factory size={22} aria-hidden />}
              />
              <KpiCard
                label="Tempo previsto"
                value={formatHours(timeAnalysis?.planned_hours)}
                hint={`Real: ${formatHours(timeAnalysis?.real_hours)}`}
                icon={<Clock3 size={22} aria-hidden />}
              />
              <KpiCard
                label="Variação"
                value={formatHours(timeAnalysis?.time_variance_hours)}
                hint={`Ganho/perda: ${formatHours(timeAnalysis?.time_gained_lost_hours)}`}
                icon={<Clock3 size={22} aria-hidden />}
              />
            </section>

            <section className="ef-detail-layout">
              <article className="ef-detail-card">
                <header>
                  <Factory size={20} aria-hidden />
                  <div>
                    <h2>Apontamento</h2>
                    <p>SH6010 — operador, recurso e quantidades</p>
                  </div>
                </header>
                <DetailFieldGrid fields={appointmentFields} />
              </article>

              <article className="ef-detail-card">
                <header>
                  <Clock3 size={20} aria-hidden />
                  <div>
                    <h2>Análise de tempos</h2>
                    <p>Previsto (SHY010/SG2) × realizado (início/fim ou H6_TEMPO)</p>
                  </div>
                </header>
                <AppointmentTimeFindings findings={timeAnalysis?.findings ?? []} />
                <DetailFieldGrid fields={timeFields} />
              </article>
            </section>

            <section className="ef-table-card" aria-label="Roteiro de produção">
              <header className="ef-table-card__header">
                <div>
                  <h2>Roteiro de produção</h2>
                  <p>SG2010 — operação do apontamento destacada</p>
                </div>
              </header>
              <div className="ef-table-wrap">
                <table className="ef-table ef-table--routing">
                  <thead>
                    <tr>
                      <th className="ef-table__col--compact">Operação</th>
                      <th className="ef-table__col--wide">Descrição</th>
                      <th className="ef-table__col--compact">CT</th>
                      <th className="ef-table__col--compact">Recurso</th>
                      <th className="ef-table__col--numeric">Setup (h)</th>
                      <th className="ef-table__col--numeric">Tempo padrão (h/peça)</th>
                      <th className="ef-table__col--badge">Apontamento</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.routingOperations.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="ef-table__empty">
                          Roteiro não encontrado para o produto.
                        </td>
                      </tr>
                    ) : (
                      detail.routingOperations.map((row, index) => (
                        <tr key={`${row.operation_code ?? "op"}-${index}`} className="ef-row">
                          <td className="ef-table__col--compact" data-label="Operação">
                            {row.operation_code ?? "—"}
                          </td>
                          <td className="ef-table__col--wide" data-label="Descrição">
                            {row.operation_description ?? "—"}
                          </td>
                          <td className="ef-table__col--compact" data-label="CT">
                            {row.work_center ?? "—"}
                          </td>
                          <td className="ef-table__col--compact" data-label="Recurso">
                            {row.resource_code ?? "—"}
                          </td>
                          <td className="ef-table__col--numeric" data-label="Setup (h)">
                            {formatHours(row.setup_hours ?? null)}
                          </td>
                          <td className="ef-table__col--numeric" data-label="Tempo padrão (h/peça)">
                            {formatHours(row.standard_time_hours_piece ?? null, 4)}
                          </td>
                          <td className="ef-table__col--badge" data-label="Apontamento">
                            {row.is_appointment_operation ? (
                              <span className="ef-badge ef-badge--success">Operação atual</span>
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <article className="ef-detail-card ef-detail-card--full">
              <header>
                <Boxes size={20} aria-hidden />
                <div>
                  <h2>Estrutura do produto</h2>
                  <p>BOM / estrutura analítica com níveis aninhados</p>
                </div>
              </header>
              <ProductStructureTree structure={detail.structure} />
            </article>
          </>
        ) : null}
      </div>
    </div>
  );
}
