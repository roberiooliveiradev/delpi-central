import { useCallback, useEffect, useRef, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringDateField,
  EngineeringEmptyState,
  EngineeringFieldLabel,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringSectionCard,
  EngineeringStateBanner,
  EngineeringStatusBadge,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/DataTable";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import {
  fetchNcIndicators,
  fetchNonconformities,
  fetchNonconformitiesExport,
  fetchProblemTags,
  importNonconformities,
} from "../api/nonconformityApi";
import {
  formatNcDate,
  formatNcDateTime,
  NC_HELP,
  NC_SORT_OPTIONS,
  NC_STATUS_LABELS,
  NC_STATUS_VARIANTS,
} from "../ncCopy";
import { NC_PATHS, navigateNc } from "../nonconformityRoutes";
import {
  buildNcHeroHighlights,
  buildNcProductsSummary,
  describeNcProduct,
} from "../ncPresentation";
import type {
  NcImportReport,
  NcIndicators,
  NcListResult,
  NcProblemTag,
  NcProduct,
  Nonconformity,
} from "../types";

const PAGE_SIZE = 20;

type Filters = {
  status: string;
  sale_number: string;
  lmp_number: string;
  customer_name: string;
  product_code: string;
  problem_tag: string;
  date_start: string;
  date_end: string;
};

const EMPTY_FILTERS: Filters = {
  status: "",
  sale_number: "",
  lmp_number: "",
  customer_name: "",
  product_code: "",
  problem_tag: "",
  date_start: "",
  date_end: "",
};

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof HomeApiError) return error.message;
  return fallback;
}

export function NonconformitiesListPage() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);
  const [sortBy, setSortBy] = useState("occurrence_date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  const [list, setList] = useState<NcListResult | null>(null);
  const [indicators, setIndicators] = useState<NcIndicators | null>(null);
  const [tags, setTags] = useState<NcProblemTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const requestRef = useRef(0);
  const tagsRef = useRef<NcProblemTag[]>([]);

  const load = useCallback(async () => {
    const requestId = ++requestRef.current;
    setLoading(true);
    setError(null);
    try {
      const [listResult, indicatorsResult, tagsResult] = await Promise.all([
        fetchNonconformities({
          ...applied,
          sort_by: sortBy,
          sort_dir: sortDir,
          page,
          page_size: PAGE_SIZE,
        }),
        fetchNcIndicators(),
        tagsRef.current.length
          ? Promise.resolve(tagsRef.current)
          : fetchProblemTags(),
      ]);
      if (requestRef.current !== requestId) return;
      setList(listResult);
      setIndicators(indicatorsResult);
      tagsRef.current = tagsResult;
      setTags(tagsResult);
    } catch (err) {
      if (requestRef.current !== requestId) return;
      setList(null);
      setError(
        errorMessage(err, "Não foi possível carregar as não conformidades."),
      );
    } finally {
      if (requestRef.current === requestId) setLoading(false);
    }
  }, [applied, page, sortBy, sortDir]);

  useEffect(() => {
    void load();
  }, [load]);

  const applyFilters = () => {
    setPage(1);
    setApplied({ ...filters });
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
    setApplied(EMPTY_FILTERS);
    setPage(1);
  };

  const toggleSort = (column: string) => {
    setPage(1);
    if (sortBy === column) {
      setSortDir((dir) => (dir === "desc" ? "asc" : "desc"));
    } else {
      setSortBy(column);
      setSortDir("desc");
    }
  };

  const onExport = async () => {
    setExporting(true);
    try {
      const payload = await fetchNonconformitiesExport();
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `nao-conformidades-${payload.generated_at.slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(errorMessage(err, "Falha ao exportar as não conformidades."));
    } finally {
      setExporting(false);
    }
  };

  const columns: DataTableColumn<Nonconformity>[] = [
    {
      key: "occurrence_date",
      header: "Ocorrência",
      sortable: true,
      render: (row) => formatNcDate(row.occurrence_date),
    },
    {
      key: "sale_number",
      header: "OV",
      sortable: true,
      render: (row) => row.sale_number ?? "—",
    },
    {
      key: "lmp_number",
      header: "LMP",
      sortable: true,
      render: (row) => row.lmp_number ?? "—",
    },
    {
      key: "customer_name",
      header: "Cliente",
      sortable: true,
      render: (row) => row.customer_name ?? "—",
    },
    {
      key: "products",
      header: "Produtos associados",
      headerHint: NC_HELP.colProducts,
      render: (row) => <NcProductsCell products={row.products} />,
    },
    {
      key: "status",
      header: "Status",
      headerHint: NC_HELP.status,
      sortable: true,
      render: (row) => (
        <EngineeringStatusBadge
          label={NC_STATUS_LABELS[row.status] ?? row.status}
          variant={NC_STATUS_VARIANTS[row.status] ?? "neutral"}
        />
      ),
    },
    {
      key: "defect_description",
      header: "Problema",
      headerHint: NC_HELP.colDefect,
      render: (row) => (
        <span
          className="engineering-nc-defect"
          title={row.defect_description ?? ""}
        >
          {row.defect_description ?? "—"}
        </span>
      ),
    },
    {
      key: "problem_tags",
      header: "Tags",
      headerHint: NC_HELP.problemTag,
      render: (row) =>
        row.problem_tags.length ? row.problem_tags.join(", ") : "—",
    },
    {
      key: "registered_at",
      header: "Registro",
      headerHint: NC_HELP.colRegisteredAt,
      sortable: true,
      render: (row) => formatNcDateTime(row.registered_at),
    },
  ];

  return (
    <main className="engineering-nonconformities">
      <EngineeringPagePath
        back={{
          label: "Início",
          href: "/apps/engineering",
          onNavigate: (event) => {
            event.preventDefault();
            navigateEngineeringView("home");
          },
        }}
        items={[]}
        current="Não conformidades"
      />

      <EngineeringPageHero
        eyebrow="Portal Engenharia"
        title="Não conformidades"
        description="Registro e acompanhamento das não conformidades de Engenharia — dados oficiais da Engineering API."
        highlights={buildNcHeroHighlights(indicators)}
        actions={
          <>
            <EngineeringActionButton
              variant="primary"
              onClick={() => navigateNc(NC_PATHS.new)}
            >
              Nova não conformidade
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="ghost"
              onClick={() => void onExport()}
              disabled={exporting}
            >
              {exporting ? "Exportando…" : "Exportar"}
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="ghost"
              onClick={() => setImportOpen((v) => !v)}
            >
              Importar
            </EngineeringActionButton>
          </>
        }
      >
        <div
          className="engineering-nc-filters"
          role="group"
          aria-label="Filtros de não conformidades"
        >
          <label className="engineering-nc-field">
            <EngineeringFieldLabel label="Status" hint={NC_HELP.status} />
            <select
              value={filters.status}
              onChange={(e) =>
                setFilters((f) => ({ ...f, status: e.target.value }))
              }
              disabled={loading}
            >
              <option value="">Todos</option>
              <option value="open">Aberta</option>
              <option value="in_progress">Em andamento</option>
              <option value="done">Concluída</option>
            </select>
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel label="OV" hint={NC_HELP.saleNumber} />
            <input
              value={filters.sale_number}
              onChange={(e) =>
                setFilters((f) => ({ ...f, sale_number: e.target.value }))
              }
              disabled={loading}
              placeholder="Número da OV"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel label="LMP" hint={NC_HELP.lmpNumber} />
            <input
              value={filters.lmp_number}
              onChange={(e) =>
                setFilters((f) => ({ ...f, lmp_number: e.target.value }))
              }
              disabled={loading}
              placeholder="Número da LMP"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Cliente"
              hint={NC_HELP.customerName}
            />
            <input
              value={filters.customer_name}
              onChange={(e) =>
                setFilters((f) => ({ ...f, customer_name: e.target.value }))
              }
              disabled={loading}
              placeholder="Nome do cliente"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Produto"
              hint={NC_HELP.productCode}
            />
            <input
              value={filters.product_code}
              onChange={(e) =>
                setFilters((f) => ({ ...f, product_code: e.target.value }))
              }
              disabled={loading}
              placeholder="Código do produto"
            />
          </label>
          <label className="engineering-nc-field">
            <EngineeringFieldLabel
              label="Problema identificado"
              hint={NC_HELP.problemTag}
            />
            <select
              value={filters.problem_tag}
              onChange={(e) =>
                setFilters((f) => ({ ...f, problem_tag: e.target.value }))
              }
              disabled={loading}
            >
              <option value="">Todas</option>
              {tags.map((tag) => (
                <option key={tag.id} value={tag.label}>
                  {tag.label}
                </option>
              ))}
            </select>
          </label>
          <EngineeringDateField
            label="Ocorrência inicial"
            hint={NC_HELP.dateStart}
            type="date"
            value={filters.date_start}
            disabled={loading}
            onChange={(value) =>
              setFilters((f) => ({ ...f, date_start: value }))
            }
          />
          <EngineeringDateField
            label="Ocorrência final"
            hint={NC_HELP.dateEnd}
            type="date"
            value={filters.date_end}
            disabled={loading}
            onChange={(value) =>
              setFilters((f) => ({ ...f, date_end: value }))
            }
          />
        </div>
        <div className="engineering-nc-actions">
          <EngineeringActionButton
            variant="primary"
            onClick={applyFilters}
            disabled={loading}
          >
            Filtrar
          </EngineeringActionButton>
          <EngineeringActionButton
            variant="ghost"
            onClick={clearFilters}
            disabled={loading}
          >
            Limpar
          </EngineeringActionButton>
        </div>
      </EngineeringPageHero>

      {importOpen ? (
        <NcImportPanel
          onClose={() => setImportOpen(false)}
          onDone={() => {
            setImportOpen(false);
            void load();
          }}
        />
      ) : null}

      {error ? (
        <EngineeringStateBanner variant="error">
          {`Não conformidades indisponíveis — ${error}`}
        </EngineeringStateBanner>
      ) : null}

      {loading && !list ? (
        <EngineeringLoadingActivityCard
          title="Carregando não conformidades"
          description="Consultando a Engineering API com seus filtros."
        />
      ) : null}

      {!loading && !error && list && list.items.length === 0 ? (
        <EngineeringEmptyState message="Nenhuma não conformidade encontrada com os filtros atuais." />
      ) : null}

      {list && list.items.length > 0 ? (
        <DataTableSection
          title="Registro de não conformidades"
          titleHint={NC_HELP.table}
          hint={`${list.total} registro(s) — ordenado por ${
            NC_SORT_OPTIONS.find((o) => o.value === sortBy)?.label ?? sortBy
          } (${sortDir === "desc" ? "decrescente" : "crescente"})`}
          columns={columns}
          rows={list.items}
          rowKey={(row) => row.id}
          loading={loading}
          hideSearch
          serverSort={{
            sortKey: sortBy,
            sortDirection: sortDir,
            onSortChange: toggleSort,
          }}
          serverPagination={{
            page,
            pageSize: PAGE_SIZE,
            total: list.total,
            onPageChange: setPage,
          }}
          onRowClick={(row) => navigateNc(NC_PATHS.detail(row.id))}
          getRowClassName={() => "engineering-nc-row--clickable"}
        />
      ) : null}
    </main>
  );
}

/** Célula compacta de produtos — primeiros itens + contador de
 * excedentes; a lista completa fica acessível via `title`/`aria-label`
 * e no detalhe da NC (a linha inteira navega). */
function NcProductsCell({ products }: { products: NcProduct[] }) {
  if (!products.length) {
    return <span className="engineering-nc-muted">—</span>;
  }
  const summary = buildNcProductsSummary(products);
  return (
    <span
      className="engineering-nc-products-cell"
      title={summary.fullLabel}
      aria-label={`Produtos associados: ${summary.fullLabel}`}
    >
      {summary.visible.map((product) => (
        <span
          key={product.product_code}
          className="engineering-nc-products-item"
        >
          {describeNcProduct(product)}
        </span>
      ))}
      {summary.overflowCount > 0 ? (
        <span className="engineering-nc-products-more">
          +{summary.overflowCount}
        </span>
      ) : null}
    </span>
  );
}

/** Painel de importação E-NC-10 — dry-run obrigatório antes da
 * substituição total; confirmação explícita destrutiva. */
function NcImportPanel({
  onClose,
  onDone,
}: {
  onClose: () => void;
  onDone: () => void;
}) {
  const [rawText, setRawText] = useState("");
  const [report, setReport] = useState<NcImportReport | null>(null);
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (dryRun: boolean) => {
    setError(null);
    let items: unknown[];
    try {
      const parsed = JSON.parse(rawText);
      items = Array.isArray(parsed) ? parsed : parsed?.items;
      if (!Array.isArray(items)) throw new Error("shape");
    } catch {
      setError("JSON inválido — informe uma lista ou um objeto com items.");
      return;
    }
    if (!dryRun && !confirmReplace) {
      setError("Confirme a substituição total do acervo para executar.");
      return;
    }
    setBusy(true);
    try {
      const result = await importNonconformities(items, {
        dryRun,
        confirmReplace: true,
      });
      setReport(result);
      if (!dryRun) onDone();
    } catch (err) {
      setError(errorMessage(err, "Falha na importação."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <EngineeringSectionCard
      title="Importar não conformidades"
      hint={NC_HELP.importPanel}
      subtitle="A importação substitui todo o acervo (semântica oficial). Execute o dry-run primeiro e confirme a substituição."
    >
      <div className="engineering-nc-import">
        <textarea
          className="engineering-nc-textarea"
          rows={8}
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder='[{"occurrence_date":"2026-01-10","sale_number":"004101","defect_description":"…"}]'
          aria-label="JSON de importação"
        />
        <label className="engineering-nc-check">
          <input
            type="checkbox"
            checked={confirmReplace}
            onChange={(e) => setConfirmReplace(e.target.checked)}
          />
          Confirmo que esta importação substitui todo o acervo de não
          conformidades.
        </label>
        <div className="engineering-nc-actions">
          <EngineeringActionButton
            variant="ghost"
            onClick={() => void run(true)}
            disabled={busy}
          >
            {busy ? "Processando…" : "Dry-run"}
          </EngineeringActionButton>
          <EngineeringActionButton
            variant="primary"
            onClick={() => void run(false)}
            disabled={busy || !confirmReplace}
          >
            Executar importação
          </EngineeringActionButton>
          <EngineeringActionButton variant="ghost" onClick={onClose}>
            Fechar
          </EngineeringActionButton>
        </div>
        {error ? (
          <p className="engineering-nc-error" role="alert">
            {error}
          </p>
        ) : null}
        {report ? (
          <div className="engineering-nc-import-report" aria-live="polite">
            <p>
              Resultado: {report.created} criada(s), {report.deleted}{" "}
              removida(s), {report.skipped} ignorada(s), {report.errors}{" "}
              erro(s).
            </p>
            {report.items.slice(0, 10).map((item, idx) => (
              <p key={idx} className="engineering-nc-import-item">
                [{item.index}] {item.result}
                {item.reason ? ` — ${item.reason}` : ""}
                {item.sale_number ? ` (OV ${item.sale_number})` : ""}
              </p>
            ))}
          </div>
        ) : null}
      </div>
    </EngineeringSectionCard>
  );
}
