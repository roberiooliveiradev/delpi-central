import { useMemo, useState } from "react";
import {
  ArrowLeft,
  Boxes,
  CircleGauge,
  Clock3,
  ExternalLink,
  Factory,
  UserRound,
} from "lucide-react";

import { AppointmentTimeFindings } from "../components/AppointmentTimeFindings";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { ExportActions } from "../components/ExportActions";
import {
  DetailDateTimeValue,
  DetailDateValue,
  DetailFormulaValue,
  DetailHoursValue,
  DetailIntegerValue,
  DetailNumericValue,
  DetailPercentValue,
  DetailQuantityValue,
} from "../components/DetailValue";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { OeeStatusBadge } from "../components/OeeStatusBadge";
import { ProductStructureTree } from "../components/ProductStructureTree";
import { ProductTypeBadge } from "../components/ProductTypeBadge";
import { ProductionPageHeader } from "../components/ProductionPageHeader";
import { PRODUCTION_ROUTES } from "../constants/routes";
import { useProductionOeeAppointmentDetail } from "../hooks/useProductionOeeAppointmentDetail";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type {
  ProductionOeeRoutingOperation,
  ProductionOrderProductType,
} from "../types/production";
import { formatHours, formatInteger, formatPercent } from "../utils/format";
import { appendFiltersToPath, readProductionFilters } from "../utils/filterUrl";
import {
  exportAppointmentDetailExcel,
  exportAppointmentDetailPdf,
} from "../utils/appointmentDetailExport";
import { navigateProduction, navigateProductionBack } from "../utils/navigation";
import { buildOtdOrderPath } from "../utils/routeParser";

type OeeAppointmentDetailPageProps = {
  appointmentId: string;
  branch?: string;
  pathname?: string;
};

function resolveProductType(
  productType?: string | null
): ProductionOrderProductType | undefined {
  const normalized = productType?.trim().toUpperCase();
  if (normalized === "PA" || normalized === "PI") {
    return normalized;
  }
  return undefined;
}

function formatRealHoursSource(source?: string | null): string {
  if (source === "interval") return "Início/fim do apontamento";
  if (source === "h6_tempo") return "H6_TEMPO (fallback)";
  return "—";
}

export function OeeAppointmentDetailPage({
  appointmentId,
  branch,
  pathname,
}: OeeAppointmentDetailPageProps) {
  const filterState = readProductionFilters();
  const detail = useProductionOeeAppointmentDetail(appointmentId, { branch });
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const appointment = detail.appointment;
  const timeAnalysis = detail.timeAnalysis;

  const initialFetchProgress = useTrackedSingleFetchProgress(detail.loading);
  const initialLoadingProgress = useLoadingProgress(
    detail.loading,
    initialFetchProgress
  );

  const backPath = appendFiltersToPath(PRODUCTION_ROUTES.oee, filterState);

  const handleBack = () => {
    navigateProductionBack(backPath, filterState);
  };

  const handleOpenProductionOrder = () => {
    if (!appointment?.production_order) return;

    navigateProduction(
      buildOtdOrderPath(
        appointment.production_order,
        appointment.branch,
        filterState,
        resolveProductType(appointment.product_type)
      ),
      filterState
    );
  };

  const handleExportExcel = async () => {
    if (!detail.data || exporting) return;
    setExportError(null);
    setExporting(true);
    try {
      await exportAppointmentDetailExcel(detail.data);
    } catch (reason) {
      setExportError(
        reason instanceof Error ? reason.message : "Não foi possível exportar o Excel."
      );
    } finally {
      setExporting(false);
    }
  };

  const handleExportPdf = async () => {
    if (!detail.data || exporting) return;
    setExportError(null);
    setExporting(true);
    try {
      await exportAppointmentDetailPdf(detail.data);
    } catch (reason) {
      setExportError(
        reason instanceof Error ? reason.message : "Não foi possível exportar o PDF."
      );
    } finally {
      setExporting(false);
    }
  };

  const appointmentFields = useMemo(
    () =>
      appointment
        ? [
            {
              label: "Status OEE",
              value: <OeeStatusBadge status={appointment.status} oeePct={appointment.oee_pct} />,
            },
            {
              label: "Tipo produto",
              value: <ProductTypeBadge productType={appointment.product_type} />,
            },
            { label: "Filial", value: appointment.branch },
            { label: "Apontamento", value: <DetailIntegerValue value={appointment.appointment_id} /> },
            { label: "OP", value: appointment.production_order || "—" },
            { label: "Nº OP", value: appointment.order_number || "—" },
            { label: "Item", value: appointment.order_item || "—" },
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
            { label: "Recurso", value: appointment.resource_name || appointment.resource_code || "—" },
            { label: "Operador", value: appointment.operator_code || "—" },
            { label: "Roteiro", value: appointment.route_code || "—" },
            {
              label: "Data produção",
              value: <DetailDateValue value={appointment.production_date} />,
            },
            {
              label: "Data apontamento",
              value: <DetailDateValue value={appointment.appointment_date} />,
            },
            {
              label: "Início",
              value: (
                <DetailDateTimeValue
                  date={appointment.start_date}
                  time={appointment.start_time}
                />
              ),
            },
            {
              label: "Fim",
              value: (
                <DetailDateTimeValue date={appointment.end_date} time={appointment.end_time} />
              ),
            },
            {
              label: "Qtd. apontada",
              value: (
                <DetailQuantityValue
                  value={appointment.produced_qty}
                  unit={appointment.unit}
                />
              ),
            },
            {
              label: "Qtd. perdida",
              value: (
                <DetailQuantityValue value={appointment.lost_qty} unit={appointment.unit} />
              ),
            },
            {
              label: "Qtd. OP",
              value: (
                <DetailQuantityValue
                  value={appointment.order_planned_qty}
                  unit={appointment.unit}
                />
              ),
            },
            {
              label: "Produzido OP",
              value: (
                <DetailQuantityValue
                  value={appointment.order_produced_qty}
                  unit={appointment.unit}
                />
              ),
            },
            {
              label: "Tipo apontamento",
              value: appointment.appointment_type || "—",
            },
            {
              label: "Ponto produção",
              value: appointment.production_point_type || "—",
            },
          ]
        : [],
    [appointment]
  );

  const timeFields = useMemo(
    () =>
      timeAnalysis
        ? [
            { label: "Setup (h)", value: <DetailHoursValue value={timeAnalysis.setup_hours} /> },
            {
              label: "Fator padrão",
              value: <DetailNumericValue value={timeAnalysis.standard_time_factor} fractionDigits={6} />,
            },
            {
              label: "Qtd. OP",
              value: (
                <DetailQuantityValue
                  value={timeAnalysis.order_planned_qty}
                  unit={appointment?.unit}
                />
              ),
            },
            {
              label: "Qtd. apontada",
              value: (
                <DetailQuantityValue
                  value={timeAnalysis.produced_qty}
                  unit={appointment?.unit}
                />
              ),
            },
            {
              label: "Tempo previsto",
              value: <DetailHoursValue value={timeAnalysis.planned_hours} />,
            },
            {
              label: "Tempo real",
              value: <DetailHoursValue value={timeAnalysis.real_hours} />,
            },
            {
              label: "Fonte tempo real",
              value: formatRealHoursSource(timeAnalysis.real_hours_source),
            },
            {
              label: "Variação (real − previsto)",
              value: <DetailHoursValue value={timeAnalysis.time_variance_hours} />,
            },
            {
              label: "Ganho/perda de tempo",
              value: <DetailHoursValue value={timeAnalysis.time_gained_lost_hours} />,
            },
            {
              label: "Eficiência (tempos)",
              value: <DetailPercentValue value={timeAnalysis.efficiency_from_times_pct} />,
            },
            {
              label: "OEE registrado",
              value: <DetailPercentValue value={timeAnalysis.oee_pct} />,
            },
            {
              label: "Fórmula previsto",
              value: <DetailFormulaValue value={timeAnalysis.formula_planned} />,
              wide: true,
            },
            {
              label: "Fórmula real",
              value: <DetailFormulaValue value={timeAnalysis.formula_real} />,
              wide: true,
            },
            {
              label: "Fórmula eficiência",
              value: <DetailFormulaValue value={timeAnalysis.formula_efficiency} />,
              wide: true,
            },
          ]
        : [],
    [timeAnalysis, appointment?.unit]
  );

  const routingColumns = useMemo<DataTableColumn<ProductionOeeRoutingOperation>[]>(
    () => [
      {
        key: "operation_code",
        header: "Operação",
        render: (row) => row.operation_code ?? "—",
      },
      {
        key: "operation_description",
        header: "Descrição",
        className: "dp-table__col--wide",
        render: (row) => row.operation_description ?? "—",
      },
      {
        key: "work_center",
        header: "CT",
        render: (row) => row.work_center ?? "—",
      },
      {
        key: "resource_code",
        header: "Recurso",
        render: (row) => row.resource_code ?? "—",
      },
      {
        key: "setup_hours",
        header: "Setup (h)",
        className: "dp-table__col--numeric",
        render: (row) => formatHours(row.setup_hours as number | null),
      },
      {
        key: "standard_time_hours_piece",
        header: "Tempo padrão (h/peça)",
        className: "dp-table__col--numeric",
        render: (row) => formatHours(row.standard_time_hours_piece as number | null, 4),
      },
      {
        key: "bom_level",
        header: "Nível BOM",
        className: "dp-table__col--numeric",
        render: (row) => formatInteger(row.bom_level as number | null),
      },
      {
        key: "highlight",
        header: "Apontamento",
        render: (row) =>
          row.is_appointment_operation ? (
            <span className="dp-kpi-badge dp-kpi-badge--success">Operação atual</span>
          ) : (
            "—"
          ),
      },
    ],
    []
  );

  const pageTitle = appointment
    ? `Apontamento ${appointment.appointment_id}`
    : `Apontamento ${appointmentId}`;

  const pageSubtitle = appointment
    ? `OP ${appointment.production_order} · ${appointment.product_code} · CT ${appointment.work_center}`
    : branch
      ? `Filial ${branch}`
      : "Detalhe do apontamento de produção";

  return (
    <div className="dashboard-production dashboard-page">
      <ProductionPageHeader
        title={pageTitle}
        subtitle={pageSubtitle}
        currentPath={pathname ?? PRODUCTION_ROUTES.oee}
        filterState={filterState}
        onRefresh={detail.reload}
        refreshing={detail.loading && Boolean(appointment)}
        actions={
          <>
            {appointment ? (
              <ExportActions
                exporting={exporting}
                onExportExcel={handleExportExcel}
                onExportPdf={handleExportPdf}
              />
            ) : null}
            {appointment?.production_order ? (
              <button
                type="button"
                className="dp-ghost-btn"
                onClick={handleOpenProductionOrder}
              >
                <ExternalLink size={16} aria-hidden="true" />
                Ver OP
              </button>
            ) : null}
            <button type="button" className="dp-ghost-btn" onClick={handleBack}>
              <ArrowLeft size={16} aria-hidden="true" />
              Voltar
            </button>
          </>
        }
      />

      <DataSourceBanner />

      {exportError ? (
        <div className="dp-state dp-state--warning" role="status">
          <p>{exportError}</p>
        </div>
      ) : null}

      {detail.error ? (
        <div className="dp-state dp-state--error" role="alert">
          <p>{detail.error}</p>
          <button className="dp-primary-btn" type="button" onClick={detail.reload}>
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
          <section className="dp-kpi-grid" aria-busy={detail.loading}>
            <KpiCard
              title="Eficiência"
              value={formatPercent(appointment.oee_pct)}
              subtitle={timeAnalysis?.formula_efficiency ?? "Tempo previsto ÷ tempo real"}
              icon={<CircleGauge size={22} />}
              loading={detail.loading}
            />
            <KpiCard
              title="Tempo previsto"
              value={formatHours(timeAnalysis?.planned_hours)}
              subtitle={`Real: ${formatHours(timeAnalysis?.real_hours)}`}
              icon={<Clock3 size={22} />}
              loading={detail.loading}
            />
            <KpiCard
              title="Variação"
              value={formatHours(timeAnalysis?.time_variance_hours)}
              subtitle={`Ganho/perda: ${formatHours(timeAnalysis?.time_gained_lost_hours)}`}
              icon={<UserRound size={22} />}
              loading={detail.loading}
            />
          </section>

          <section className="dp-detail-layout">
            <DetailCard
              title="Apontamento"
              hint="SH6010 — operador, recurso e quantidades"
              icon={<Factory size={20} />}
            >
              <DetailFieldGrid fields={appointmentFields} />
            </DetailCard>

            <DetailCard
              title="Análise de tempos"
              hint="Previsto (SHY010/SG2) × realizado (início/fim ou H6_TEMPO)"
              icon={<Clock3 size={20} />}
            >
              <AppointmentTimeFindings findings={timeAnalysis?.findings ?? []} />
              <DetailFieldGrid fields={timeFields} />
            </DetailCard>
          </section>

          <DataTableSection
            title="Roteiro de produção"
            hint="SG2010 — operação do apontamento destacada"
            columns={routingColumns}
            rows={detail.routingOperations}
            rowKey={(row) =>
              `${String(row.product_code ?? "product")}-${String(row.operation_code ?? "op")}-${String(row.bom_level ?? 0)}`
            }
            hideSearch
            emptyMessage="Roteiro não encontrado para o produto."
            loading={detail.loading && detail.routingOperations.length === 0}
            refreshing={detail.loading && detail.routingOperations.length > 0}
          />

          <DetailCard
            title="Estrutura do produto"
            hint="BOM / estrutura analítica com níveis aninhados"
            icon={<Boxes size={20} />}
            className="dp-detail-card--full"
          >
            <ProductStructureTree structure={detail.structure} />
          </DetailCard>
        </>
      ) : null}
    </div>
  );
}
