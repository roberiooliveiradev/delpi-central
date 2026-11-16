import { useMemo, useState } from "react";
import type { SupplierPerformance } from "../../api/supplierPerformance";
import {
  SuppliesActionButton,
  SuppliesCompactPagination,
  SuppliesDataTable,
  SuppliesSelectField,
  SuppliesTextField,
  type DataTableColumn,
} from "../../app/suppliesUi";
import {
  countLabel,
  COVERAGE_LABELS,
  filterSuppliers,
  scoreLabel,
  supplierKey,
} from "./supplierPerformancePresentation";

export function SupplierPerformanceTable({
  items,
  onSelect,
}: {
  items: SupplierPerformance[];
  onSelect: (item: SupplierPerformance) => void;
}) {
  const [query, setQuery] = useState("");
  const [coverage, setCoverage] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const filtered = useMemo(
    () => filterSuppliers(items, query, coverage),
    [items, query, coverage],
  );
  const currentPage = Math.min(
    page,
    Math.max(1, Math.ceil(filtered.length / pageSize)),
  );
  const columns: DataTableColumn<SupplierPerformance>[] = [
    {
      key: "supplier",
      header: "Fornecedor / loja",
      render: (item) => (
        <div className="sp-idf-supplier">
          <strong>{item.supplier_name}</strong>
          <small>
            {item.supplier_code} · Loja {item.supplier_store} · Filiais{" "}
            {item.branches.join(", ")}
          </small>
        </div>
      ),
    },
    {
      key: "quality",
      header: "Qualidade · 70%",
      align: "right",
      render: (item) => (
        <IndexCell
          value={item.quality.index}
          count={item.quality.assessed_count}
          label="inspeções"
        />
      ),
    },
    {
      key: "delivery",
      header: "Entrega · 30%",
      align: "right",
      render: (item) => (
        <IndexCell
          value={item.delivery.index}
          count={item.delivery.assessed_count}
          label="recebimentos"
        />
      ),
    },
    {
      key: "idf",
      header: "IDF / 100",
      align: "right",
      render: (item) => (
        <strong className="sp-idf-table-score">{scoreLabel(item.idf)}</strong>
      ),
    },
    {
      key: "coverage",
      header: "Disponibilidade",
      render: (item) => (
        <span
          className={`sp-idf-coverage sp-idf-coverage--${item.status === "complete" ? "complete" : "pending"}`}
        >
          {COVERAGE_LABELS[item.status]}
        </span>
      ),
    },
    {
      key: "details",
      header: "Detalhes",
      interactive: true,
      render: (item) => (
        <SuppliesActionButton variant="link" onClick={() => onSelect(item)}>
          Ver composição
          <span className="sp-idf-sr-only">
            {" "}
            de {item.supplier_name}, loja {item.supplier_store}
          </span>
        </SuppliesActionButton>
      ),
    },
  ];

  return (
    <div className="sp-idf-ranking">
      <div className="sp-idf-ranking__toolbar">
        <SuppliesTextField
          label="Buscar fornecedor"
          placeholder="Nome ou código"
          value={query}
          onChange={(value) => {
            setQuery(value);
            setPage(1);
          }}
        />
        <SuppliesSelectField
          label="Disponibilidade de dados"
          value={coverage}
          onChange={(value) => {
            setCoverage(value);
            setPage(1);
          }}
          options={[
            { value: "all", label: "Todos os fornecedores" },
            { value: "complete", label: "Com IDF calculado" },
            { value: "incomplete", label: "Com dados incompletos" },
          ]}
        />
      </div>
      <p className="sp-idf-caption">
        {countLabel(filtered.length)} fornecedor(es) · Maior IDF primeiro.
        Compare também o tamanho da base; poucas ocorrências podem resultar em
        nota 100.
      </p>
      <SuppliesDataTable
        columns={columns}
        rows={filtered.slice(
          (currentPage - 1) * pageSize,
          currentPage * pageSize,
        )}
        rowKey={supplierKey}
        emptyMessage="Nenhum fornecedor corresponde à busca e à disponibilidade selecionadas."
      />
      <SuppliesCompactPagination
        page={currentPage}
        total={filtered.length}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(value) => {
          setPageSize(value);
          setPage(1);
        }}
        pageSizeOptions={[15, 30, 60]}
      />
    </div>
  );
}

function IndexCell({
  value,
  count,
  label,
}: {
  value: number | null;
  count: number;
  label: string;
}) {
  return (
    <div className="sp-idf-index-cell">
      <strong>
        {scoreLabel(value)}
        {value == null ? "" : "%"}
      </strong>
      <small>
        {countLabel(count)} {label}
      </small>
    </div>
  );
}
