import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";

import { DataTable, type DataTableColumn } from "../components/DataTable";
import { NonconformityFilters } from "../components/NonconformityFilters";
import { Pagination } from "../components/Pagination";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { QUALITY_ROUTES } from "../constants/routes";
import { useNonconformities } from "../hooks/useQualityQueries";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { Nonconformity, NonconformityType } from "../types/nonconformity";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate } from "../utils/dates";
import { formatDecimal } from "../utils/format";

const PAGE_SIZE = 20;

type NonconformitiesPageProps = {
  pathname?: string;
};

function truncate(text: string | null, max = 80): string {
  if (!text) return "—";
  if (text.length <= max) return text;
  return `${text.slice(0, max)}…`;
}

export function NonconformitiesPage({ pathname }: NonconformitiesPageProps) {
  const [page, setPage] = useState(1);
  const [type, setType] = useState<NonconformityType>("all");
  const [status, setStatus] = useState("");
  const [itemCode, setItemCode] = useState("");
  const [description, setDescription] = useState("");

  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
  } = useQualityFilters();

  const listParams = useMemo(
    () => ({
      ...apiParams,
      type,
      status: status || undefined,
      item_code: itemCode || undefined,
      description: description || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
    [apiParams, type, status, itemCode, description, page]
  );

  const { data, loading, error, reload } = useNonconformities(listParams);

  useEffect(() => {
    setPage(1);
  }, [
    apiParams.branch,
    apiParams.date_start,
    apiParams.date_end,
    type,
    status,
    itemCode,
    description,
  ]);

  const columns = useMemo<DataTableColumn<Nonconformity>[]>(
    () => [
      {
        key: "type_label",
        header: "Tipo",
        render: (row) => row.type_label ?? row.type_code ?? "—",
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch,
      },
      {
        key: "code",
        header: "Código",
        render: (row) => `${row.code}/${row.revision}`,
      },
      {
        key: "registered_date",
        header: "Registro",
        render: (row) => formatDisplayDate(row.registered_date),
      },
      {
        key: "occurrence_date",
        header: "Ocorrência",
        render: (row) => formatDisplayDate(row.occurrence_date),
      },
      {
        key: "status_label",
        header: "Status",
        render: (row) => row.status_label ?? row.status_code ?? "—",
      },
      {
        key: "item_code",
        header: "Item",
        render: (row) => row.item_code ?? "—",
      },
      {
        key: "description",
        header: "Descrição",
        className: "dq-table__col--wide",
        render: (row) => truncate(row.description),
      },
      {
        key: "returned_quantity",
        header: "Qtd. devolvida",
        className: "dq-table__col--numeric",
        render: (row) => formatDecimal(row.returned_quantity),
      },
    ],
    []
  );

  const handleExportCsv = () => {
    const items = data?.items ?? [];
    if (items.length === 0) return;

    downloadCsv(
      `nao-conformidades-totvs-pagina-${page}.csv`,
      [
        "Tipo",
        "Filial",
        "Código",
        "Revisão",
        "Registro",
        "Ocorrência",
        "Status",
        "Item",
        "Descrição",
        "Qtd devolvida",
      ],
      items.map((row) => [
        row.type_label ?? row.type_code,
        row.branch,
        row.code,
        row.revision,
        formatDisplayDate(row.registered_date),
        formatDisplayDate(row.occurrence_date),
        row.status_label ?? row.status_code ?? "",
        row.item_code ?? "",
        row.description ?? "",
        String(row.returned_quantity ?? ""),
      ])
    );
  };

  return (
    <div className="dashboard-quality dashboard-page">
      <QualityPageHeader
        title="Não conformidades"
        subtitle="Listagem analítica do Protheus (TOTVS)"
        currentPath={pathname ?? QUALITY_ROUTES.nonconformities}
        onRefresh={reload}
        refreshing={loading && Boolean(data)}
        actions={
          <button
            type="button"
            className="dq-ghost-btn"
            onClick={handleExportCsv}
            disabled={!data?.items.length}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <TotvsSourceBanner />

      <NonconformityFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        type={type}
        status={status}
        itemCode={itemCode}
        description={description}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onTypeChange={setType}
        onStatusChange={setStatus}
        onItemCodeChange={setItemCode}
        onDescriptionChange={setDescription}
      />

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button className="dq-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      <section className="dq-table-section dq-card" aria-busy={loading}>
        <div className="dq-table-section__header">
          <h2 className="dq-section-title">Registros</h2>
          {data ? (
            <span className="dq-table-section__meta">
              {data.total} registro(s) no período
            </span>
          ) : null}
        </div>

        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(row) => `${row.code}-${row.revision}-${row.branch}`}
          loading={loading && !data}
          emptyMessage="Nenhuma não conformidade encontrada para os filtros."
        />

        {data ? (
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={setPage}
          />
        ) : null}
      </section>
    </div>
  );
}
