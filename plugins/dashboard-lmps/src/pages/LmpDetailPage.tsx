import { GHOST_BTN } from "../ui/ghostChrome";
import { useMemo } from "react";
import {
  ArrowLeft,
  BarChart3,
  Building2,
  CircleGauge,
  Clock3,
  FileText,
  History,
  RefreshCw,
  UserRound,
  Wrench,
} from "lucide-react";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { LmpHistorySection } from "../components/LmpHistorySection";
import { LmpProductStructuresSection } from "../components/LmpProductStructuresSection";
import type { DataTableColumn } from "../components/DataTable";
import { DataTable } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { LMPS_ROUTES } from "../constants/routes";
import { useLmpDetail } from "../hooks/useLmpDetail";
import { useLmpDetailRequestScope } from "../hooks/useLmpDetailRequestScope";
import { useLmpProductStructures } from "../hooks/useLmpProductStructures";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type { LmpProduct } from "../types/lmp";
import { formatPeriodLabel } from "../utils/dates";
import { readLmpsFilters, type LmpsFilterUrlState } from "../utils/filterUrl";
import { navigateLmpsBack } from "../utils/navigation";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";
import { STATE_BOX_ERROR } from "../ui/stateChrome";

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

function formatMinutes(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR")} min`;
}

function formatListingKind(kind?: string | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "—";
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

const PRODUCT_TYPE_LABELS: Record<string, string> = {
  PA: "Acabado",
  PI: "Intermediário",
  MP: "Matéria-prima",
  ME: "Mercadoria",
  BN: "Beneficiamento",
  AI: "Ativo imobilizado",
};

function parseProductDescription(description?: string | null): {
  title: string;
  reference?: string;
} {
  const trimmed = description?.trim() ?? "";
  if (!trimmed) return { title: "—" };

  const match = trimmed.match(/^(.*)\s+\(([^)]+)\)\s*$/);
  if (!match) return { title: trimmed };

  const title = match[1].trim();
  const reference = match[2].trim();
  if (!title) return { title: trimmed };

  return { title, reference: reference || undefined };
}

function renderProductType(type?: string | null) {
  const normalized = type?.trim().toUpperCase();
  if (!normalized) return "—";

  const label = PRODUCT_TYPE_LABELS[normalized] ?? normalized;
  const badgeClass =
    normalized === "PI"
      ? "lmps-product-type-badge lmps-product-type-badge--pi"
      : normalized === "PA"
        ? "lmps-product-type-badge lmps-product-type-badge--pa"
        : "lmps-product-type-badge";

  return (
    <span className={badgeClass} title={`Tipo ${normalized}`}>
      {label}
    </span>
  );
}

function renderProductDescription(description?: string | null) {
  const { title, reference } = parseProductDescription(description);

  return (
    <div className="lmps-product-description">
      <span className="lmps-product-description__title">{title}</span>
      {reference ? (
        <span className="lmps-product-description__ref">Referência {reference}</span>
      ) : null}
    </div>
  );
}

function renderProductQuantity(value?: number | null) {
  const quantity = value ?? 0;
  const className =
    quantity > 0
      ? "lmps-product-qtd lmps-product-qtd--active"
      : "lmps-product-qtd";

  return <span className={className}>{quantity.toLocaleString("pt-BR")}</span>;
}

const productColumns: DataTableColumn<LmpProduct>[] = [
  {
    key: "code",
    header: "Código",
    headerHint: LMPS_HELP_TOOLTIPS.detail.productCode,
    render: (row) => row.code || "—",
  },
  {
    key: "description",
    header: "Descrição",
    headerHint: LMPS_HELP_TOOLTIPS.detail.productDescription,
    className: "lmps-table__col--wide",
    render: (row) => renderProductDescription(row.description),
  },
  {
    key: "group",
    header: "Grupo",
    headerHint: LMPS_HELP_TOOLTIPS.detail.productGroup,
    render: (row) => row.group_code || "—",
  },
  {
    key: "type",
    header: "Tipo",
    headerHint: LMPS_HELP_TOOLTIPS.detail.productType,
    render: (row) => renderProductType(row.type),
  },
  {
    key: "qtd_pi",
    header: "Qtd PI",
    headerHint: LMPS_HELP_TOOLTIPS.detail.productQtdPi,
    render: (row) => renderProductQuantity(row.qtd_pi),
  },
];

export function LmpDetailPage({ saleNumber, branch }: LmpDetailPageProps) {
  const requestScope = useLmpDetailRequestScope(saleNumber, branch);
  const detail = useLmpDetail(saleNumber, requestScope);
  const item = detail.item;
  const productStructures = useLmpProductStructures(item?.list_products);
  const initialFetchProgress = useTrackedSingleFetchProgress(detail.loading);
  const initialLoadingProgress = useLoadingProgress(detail.loading, initialFetchProgress);

  const periodLabel = formatPeriodLabel(requestScope.dateStart, requestScope.dateEnd);
  const backFilters = useMemo<LmpsFilterUrlState>(() => {
    const filters = readLmpsFilters();
    return {
      dateStart: requestScope.dateStart,
      dateEnd: requestScope.dateEnd,
      competence: filters.competence,
      branches: requestScope.branch ? [requestScope.branch] : [],
      listingTypes: [],
      statuses: [],
    };
  }, [requestScope]);

  const proposalFields = useMemo(
    () =>
      item
        ? [
            {
              label: OPERATIONAL_UNIT_COLUMN_LABEL,
              hint: LMPS_HELP_TOOLTIPS.detail.proposalBranch,
              value: formatOperationalUnitCode(item.branch),
            },
            {
              label: "Tipo",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalKind,
              value: formatListingKind(item.listing_kind),
            },
            {
              label: "Nº Proposta",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalNumber,
              value: item.sale_number,
            },
            {
              label: "Descrição",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalDescription,
              value: item.sale_description || "—",
              wide: true,
            },
            {
              label: "Data início",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalStartDate,
              value: formatDate(item.start_date),
            },
            {
              label: "Data fim",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalEndDate,
              value: formatDate(item.end_date),
            },
            {
              label: "Status classificação",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalStatus,
              value: renderStatusBadge(item.status),
            },
            {
              label: "Nível",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalNivel,
              value: item.nivel,
            },
            {
              label: "Dias úteis (SLA)",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalSlaDays,
              value: String(item.dias_uteis_sla),
            },
            {
              label: "Data limite",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalLimitDate,
              value: formatDate(item.data_limite),
            },
            {
              label: "Lead time útil",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalLeadTime,
              value:
                item.lead_time_util == null ? "—" : String(item.lead_time_util),
            },
            {
              label: "Qtd PI",
              hint: LMPS_HELP_TOOLTIPS.detail.proposalQtdPi,
              value: String(item.qtd_pi ?? 0),
            },
          ]
        : [],
    [item]
  );

  const engineeringFields = useMemo(
    () =>
      item
        ? [
            {
              label: "Status engenharia",
              hint: LMPS_HELP_TOOLTIPS.detail.engineeringStatus,
              value: item.engineering_status ?? "—",
            },
            {
              label: "Entradas engenharia",
              hint: LMPS_HELP_TOOLTIPS.detail.engineeringEntries,
              value: String(item.qtd_engineering_entries ?? 0),
            },
            {
              label: "Encerramentos",
              hint: LMPS_HELP_TOOLTIPS.detail.engineeringClosed,
              value: String(item.qtd_engineering_closed ?? 0),
            },
            {
              label: "Avanços",
              hint: LMPS_HELP_TOOLTIPS.detail.engineeringAdvanced,
              value: String(item.qtd_advanced_from_engineering ?? 0),
            },
            {
              label: "Retornos",
              hint: LMPS_HELP_TOOLTIPS.detail.engineeringReturned,
              value: String(item.qtd_returned_from_engineering ?? 0),
            },
            {
              label: "Tempo total",
              hint: LMPS_HELP_TOOLTIPS.detail.engineeringTotalTime,
              value: formatMinutes(item.engineering_total_minutes),
            },
            {
              label: "SLA (minutos)",
              hint: LMPS_HELP_TOOLTIPS.detail.engineeringSlaMinutes,
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
            {
              label: "Cliente",
              hint: LMPS_HELP_TOOLTIPS.detail.customerName,
              value: item.costumer_name ?? "—",
            },
            {
              label: "Código cliente",
              hint: LMPS_HELP_TOOLTIPS.detail.customerCode,
              value: item.costumer_code ?? "—",
            },
            {
              label: "Loja",
              hint: LMPS_HELP_TOOLTIPS.detail.customerStore,
              value: item.costumer_store ?? "—",
            },
            {
              label: "Vendedor",
              hint: LMPS_HELP_TOOLTIPS.detail.sellerName,
              value: item.seller_name ?? "—",
            },
            {
              label: "Código vendedor",
              hint: LMPS_HELP_TOOLTIPS.detail.sellerCode,
              value: item.seller_code ?? "—",
            },
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
          <div className="lmps-header-action">
            <button
              type="button"
              className={GHOST_BTN}
              onClick={detail.reload}
              disabled={detail.loading}
            >
              <RefreshCw size={16} aria-hidden />
              Atualizar
            </button>
            <HelpTooltip
              content={LMPS_HELP_TOOLTIPS.actions.detailRefresh}
              ariaLabel="Ajuda: atualizar detalhe"
              className="lmps-header-action__help"
            />
          </div>
          <div className="lmps-header-action">
            <button
              type="button"
              className={GHOST_BTN}
              onClick={() => navigateLmpsBack(LMPS_ROUTES.home, backFilters)}
            >
              <ArrowLeft size={16} aria-hidden />
              Voltar
            </button>
            <HelpTooltip
              content={LMPS_HELP_TOOLTIPS.actions.back}
              ariaLabel="Ajuda: voltar ao dashboard"
              className="lmps-header-action__help"
            />
          </div>
        </div>
      </header>

      {detail.error ? (
        <div className={STATE_BOX_ERROR} role="alert">
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
              titleHint={LMPS_HELP_TOOLTIPS.detail.statusKpi}
              value={item.status}
              subtitle={item.engineering_status ?? "Engenharia"}
              icon={<CircleGauge size={22} />}
            />
            <KpiCard
              title="Lead time útil"
              titleHint={LMPS_HELP_TOOLTIPS.detail.leadTimeKpi}
              value={item.lead_time_util == null ? "—" : String(item.lead_time_util)}
              subtitle={`${item.nivel} · ${item.dias_uteis_sla} dias úteis`}
              icon={<Clock3 size={22} />}
            />
            <KpiCard
              title="Tempo engenharia"
              titleHint={LMPS_HELP_TOOLTIPS.detail.engineeringTimeKpi}
              value={formatMinutes(item.engineering_total_minutes)}
              subtitle={`${item.qtd_pi ?? 0} PI · ${periodLabel}`}
              icon={<BarChart3 size={22} />}
            />
          </section>

          <section className="lmps-detail-layout">
            <DetailCard
              title="Proposta"
              titleHint={LMPS_HELP_TOOLTIPS.detail.proposalSection}
              hint="Dados da OV e classificação de prazo"
              icon={<FileText size={20} aria-hidden />}
            >
              <DetailFieldGrid fields={proposalFields} />
            </DetailCard>

            <DetailCard
              title="Engenharia"
              titleHint={LMPS_HELP_TOOLTIPS.detail.engineeringSection}
              hint="Resumo de entradas, encerramentos e tempo"
              icon={<Wrench size={20} aria-hidden />}
            >
              <DetailFieldGrid fields={engineeringFields} />
            </DetailCard>

            <DetailCard
              title="Cliente e vendedor"
              titleHint={LMPS_HELP_TOOLTIPS.detail.customerSection}
              hint="Identificação comercial da proposta"
              icon={<UserRound size={20} aria-hidden />}
            >
              <DetailFieldGrid fields={customerFields} />
            </DetailCard>

            <DetailCard
              title="Produtos"
              titleHint={LMPS_HELP_TOOLTIPS.detail.productsSection}
              hint={`${item.list_products?.length ?? 0} item(ns) vinculado(s)`}
              icon={<Building2 size={20} aria-hidden />}
            >
              <DataTable
                columns={productColumns}
                rows={item.list_products ?? []}
                rowKey={(row) => row.code || row.description}
                emptyMessage="Nenhum produto vinculado."
              />
            </DetailCard>

            {productStructures.shouldRender ? (
              <LmpProductStructuresSection
                entries={productStructures.entries}
                loading={productStructures.loading}
              />
            ) : null}

            <DetailCard
              title="Histórico da OV"
              titleHint={LMPS_HELP_TOOLTIPS.detail.historySection}
              hint="Linha do tempo de eventos no TOTVS (AIJ010), alinhada à revisão do painel LMP"
              icon={<History size={20} aria-hidden />}
              className="lmps-detail-card--full"
            >
              <LmpHistorySection
                events={item.list_history ?? []}
                referenceRevision={item.reference_revision}
                panelStartDate={item.start_date}
              />
            </DetailCard>
          </section>
        </>
      ) : null}
    </main>
  );
}
