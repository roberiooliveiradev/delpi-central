import { useMemo } from "react";
import {
  ArrowLeft,
  BarChart3,
  Building2,
  CircleGauge,
  Clock3,
  FileText,
  RefreshCw,
  UserRound,
  Wrench,
} from "lucide-react";

import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import type { DataTableColumn } from "../components/DataTable";
import { DataTable } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { LMPS_ROUTES } from "../constants/routes";
import { useLmpDetail } from "../hooks/useLmpDetail";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type { LmpProduct } from "../types/lmp";
import { formatPeriodLabel } from "../utils/dates";
import { readLmpsFilters } from "../utils/filterUrl";
import { navigateLmpsBack } from "../utils/navigation";

type LmpDetailPageProps = {
  saleNumber: string;
  branch?: string;
};

function formatDate(value?: string | null): string {
  if (!value || value.length !== 8) return "—";

  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);

  return `${day}/${month}/${year}`;
}

function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "—";
}

function formatMinutes(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR")} min`;
}

function renderStatusBadge(status?: string | null) {
  const normalized = status?.trim();
  if (!normalized) return "—";

  const className =
    normalized === "Atrasado"
      ? "lmps-status-badge lmps-status-badge--danger"
      : normalized === "Pontual"
        ? "lmps-status-badge lmps-status-badge--success"
        : normalized === "Retornada"
          ? "lmps-status-badge lmps-status-badge--warning"
          : "lmps-status-badge";

  return <span className={className}>{normalized}</span>;
}

const productColumns: DataTableColumn<LmpProduct>[] = [
  { key: "code", header: "Código", render: (row) => row.code || "—" },
  {
    key: "description",
    header: "Descrição",
    className: "lmps-table__col--wide",
    render: (row) => row.description || "—",
  },
  { key: "group", header: "Grupo", render: (row) => row.group_code || "—" },
  { key: "type", header: "Tipo", render: (row) => row.type || "—" },
  {
    key: "qtd_pi",
    header: "Qtd PI",
    render: (row) => String(row.qtd_pi ?? 0),
  },
];

export function LmpDetailPage({ saleNumber, branch }: LmpDetailPageProps) {
  const filters = readLmpsFilters();
  const detail = useLmpDetail(saleNumber, filters, { branch });
  const item = detail.item;
  const initialFetchProgress = useTrackedSingleFetchProgress(detail.loading);
  const initialLoadingProgress = useLoadingProgress(detail.loading, initialFetchProgress);

  const periodLabel = formatPeriodLabel(filters.dateStart, filters.dateEnd);

  const proposalFields = useMemo(
    () =>
      item
        ? [
            { label: "Filial", value: item.branch ?? "—" },
            { label: "Tipo", value: formatListingKind(item.listing_kind) },
            { label: "Nº Proposta", value: item.sale_number },
            {
              label: "Descrição",
              value: item.sale_description || "—",
              wide: true,
            },
            { label: "Data início", value: formatDate(item.start_date) },
            { label: "Data fim", value: formatDate(item.end_date) },
            { label: "Status classificação", value: renderStatusBadge(item.status) },
            { label: "Nível", value: item.nivel },
            { label: "Dias úteis (SLA)", value: String(item.dias_uteis_sla) },
            { label: "Data limite", value: formatDate(item.data_limite) },
            {
              label: "Lead time útil",
              value:
                item.lead_time_util == null ? "—" : String(item.lead_time_util),
            },
            { label: "Qtd PI", value: String(item.qtd_pi ?? 0) },
          ]
        : [],
    [item]
  );

  const engineeringFields = useMemo(
    () =>
      item
        ? [
            { label: "Status engenharia", value: item.engineering_status ?? "—" },
            {
              label: "Entradas engenharia",
              value: String(item.qtd_engineering_entries ?? 0),
            },
            {
              label: "Encerramentos",
              value: String(item.qtd_engineering_closed ?? 0),
            },
            {
              label: "Avanços",
              value: String(item.qtd_advanced_from_engineering ?? 0),
            },
            {
              label: "Retornos",
              value: String(item.qtd_returned_from_engineering ?? 0),
            },
            {
              label: "Tempo total",
              value: formatMinutes(item.engineering_total_minutes),
            },
            {
              label: "SLA (minutos)",
              value: formatMinutes(item.sla_minutos),
            },
          ]
        : [],
    [item]
  );

  const customerFields = useMemo(
    () =>
      item
        ? [
            { label: "Cliente", value: item.costumer_name ?? "—" },
            { label: "Código cliente", value: item.costumer_code ?? "—" },
            { label: "Loja", value: item.costumer_store ?? "—" },
            { label: "Vendedor", value: item.seller_name ?? "—" },
            { label: "Código vendedor", value: item.seller_code ?? "—" },
          ]
        : [],
    [item]
  );

  const pageTitle = item
    ? `Proposta ${item.sale_number}`
    : `Proposta ${saleNumber}`;

  const pageSubtitle = item
    ? `${formatListingKind(item.listing_kind)} · ${item.sale_description}`
    : `${periodLabel} · detalhe da OV`;

  return (
    <main className="dashboard-lmps dashboard-page">
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • LMPs</p>
          <h1>{pageTitle}</h1>
          <span className="lmps-page-subtitle">{pageSubtitle}</span>
        </div>

        <div className="lmps-header-actions">
          <button
            type="button"
            className="lmps-ghost-btn"
            onClick={detail.reload}
            disabled={detail.loading}
          >
            <RefreshCw size={16} aria-hidden />
            Atualizar
          </button>
          <button
            type="button"
            className="lmps-ghost-btn"
            onClick={() => navigateLmpsBack(LMPS_ROUTES.home, filters)}
          >
            <ArrowLeft size={16} aria-hidden />
            Voltar
          </button>
        </div>
      </header>

      {detail.error ? (
        <div className="lmps-state-box lmps-state-box-error" role="alert">
          <p>{detail.error}</p>
          <button type="button" className="lmps-primary-btn" onClick={detail.reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {detail.loading && !item ? (
        <LoadingActivityCard
          title="Carregando detalhe da OV"
          description="Consultando proposta, engenharia e produtos no TOTVS."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      {item ? (
        <>
          <section className="lmps-kpi-grid" aria-busy={detail.loading}>
            <KpiCard
              title="Status"
              value={item.status}
              subtitle={item.engineering_status ?? "Engenharia"}
              icon={<CircleGauge size={22} />}
            />
            <KpiCard
              title="Lead time útil"
              value={item.lead_time_util == null ? "—" : String(item.lead_time_util)}
              subtitle={`${item.nivel} · ${item.dias_uteis_sla} dias úteis`}
              icon={<Clock3 size={22} />}
            />
            <KpiCard
              title="Tempo engenharia"
              value={formatMinutes(item.engineering_total_minutes)}
              subtitle={`${item.qtd_pi ?? 0} PI · ${periodLabel}`}
              icon={<BarChart3 size={22} />}
            />
          </section>

          <section className="lmps-detail-layout">
            <DetailCard
              title="Proposta"
              hint="Dados da OV e classificação de prazo"
              icon={<FileText size={20} aria-hidden />}
            >
              <DetailFieldGrid fields={proposalFields} />
            </DetailCard>

            <DetailCard
              title="Engenharia"
              hint="Resumo de entradas, encerramentos e tempo"
              icon={<Wrench size={20} aria-hidden />}
            >
              <DetailFieldGrid fields={engineeringFields} />
            </DetailCard>

            <DetailCard
              title="Cliente e vendedor"
              hint="Identificação comercial da proposta"
              icon={<UserRound size={20} aria-hidden />}
            >
              <DetailFieldGrid fields={customerFields} />
            </DetailCard>

            <DetailCard
              title="Produtos"
              hint={`${item.list_products?.length ?? 0} item(ns) vinculado(s)`}
              icon={<Building2 size={20} aria-hidden />}
              className="lmps-detail-card--full"
            >
              <DataTable
                columns={productColumns}
                rows={item.list_products ?? []}
                rowKey={(row) => row.code || row.description}
                emptyMessage="Nenhum produto vinculado."
              />
            </DetailCard>
          </section>
        </>
      ) : null}
    </main>
  );
}
