import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringStateBanner,
  EngineeringStatusBadge,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/DataTable";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import {
  fetchProductDetail,
  fetchProductDrawing,
  fetchProductDrawingPdf,
  fetchProductHistory,
  fetchProductParents,
  fetchProductStructure,
  fetchProductSuppliers,
} from "../api/productApi";
import {
  PRODUCT_COPY,
  PRODUCT_HELP,
  formatBytes,
  formatProductDate,
  formatProductDateTime,
  productStatusLabel,
  productTypeLabel,
} from "../productCopy";
import { PRODUCT_PATHS, navigateProducts } from "../productRoutes";
import type {
  ProductBomNode,
  ProductDrawingMetadata,
  ProductParentNode,
  ProductPurchaseHistoryResult,
  ProductRecord,
  ProductSupplier,
} from "../types";

type ProductDetailPageProps = {
  code: string;
};

type TabKey =
  | "overview"
  | "structure"
  | "whereUsed"
  | "suppliers"
  | "drawings"
  | "history";

const TAB_ORDER: readonly { key: TabKey; label: string }[] = [
  { key: "overview", label: PRODUCT_COPY.tabs.overview },
  { key: "structure", label: PRODUCT_COPY.tabs.structure },
  { key: "whereUsed", label: PRODUCT_COPY.tabs.whereUsed },
  { key: "suppliers", label: PRODUCT_COPY.tabs.suppliers },
  { key: "drawings", label: PRODUCT_COPY.tabs.drawings },
  { key: "history", label: PRODUCT_COPY.tabs.history },
];

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof HomeApiError) return error.message;
  return fallback;
}

function isNotFound(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 404;
}

function isForbidden(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 403;
}

/** Estado honesto por aba — loading, forbidden, not_found, error,
 * empty e indisponível são renderizações distintas (spec 61). */
function TabError({
  error,
  fallback,
}: {
  error: unknown;
  fallback: string;
}) {
  if (isForbidden(error)) {
    return (
      <EngineeringEmptyState message="Acesso negado pela fonte oficial — você não tem autorização para esta seção." />
    );
  }
  if (isNotFound(error)) {
    return <EngineeringEmptyState message={PRODUCT_COPY.notFound} />;
  }
  return (
    <EngineeringStateBanner variant="error">
      {errorMessage(error, fallback)}
    </EngineeringStateBanner>
  );
}

function useTabData<T>(
  active: boolean,
  fetcher: (signal: AbortSignal) => Promise<T>,
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const loaded = useRef(false);

  useEffect(() => {
    if (!active || loaded.current) return undefined;
    const controller = new AbortController();
    setLoading(true);
    fetcher(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          loaded.current = true;
          setData(result);
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [active, fetcher]);

  return { data, error, loading };
}

function field(
  label: string,
  value: ReactNode,
  hint?: string,
): { label: string; value: ReactNode; hint?: string } {
  return { label, value: value ?? "—", hint };
}

function overviewFields(product: ProductRecord) {
  return {
    identification: [
      field("Código", product.code, PRODUCT_HELP.code),
      field("Descrição", product.description, PRODUCT_HELP.description),
      field("Tipo", productTypeLabel(product.type), PRODUCT_HELP.type),
      field("Grupo", product.group_code, PRODUCT_HELP.group),
      field("Subgrupo", product.subgroup),
      field("Código anterior", product.previous_code),
      field("Situação", productStatusLabel(product)),
      field("Ref. cliente", product.customer_reference),
    ],
    engineering: [
      field(
        "Código do desenho",
        product.drawing_code,
        PRODUCT_HELP.drawingCode,
      ),
      field("Unidade", product.unit, PRODUCT_HELP.unit),
      field("Unidade secundária", product.secondary_unit),
      field("Tipo de material", product.material_type),
      field("Linha de produção", product.production_line),
      field(
        "Revisão atual",
        product.current_revision,
        PRODUCT_HELP.revision,
      ),
      field(
        "Última revisão",
        formatProductDate(product.last_revision_date),
        PRODUCT_HELP.revisionDate,
      ),
      field("Peso líquido", product.net_weight),
      field("Fabricar ou comprar", product.make_or_buy),
    ],
    logistics: [
      field("Armazém padrão", product.default_warehouse),
      field("Qtd. por embalagem", product.package_quantity),
      field("Código de barras", product.barcode),
      field("Embalagem do cliente", product.customer_packaging),
      field("Última compra", formatProductDate(product.last_purchase_date)),
    ],
  };
}

/** Árvore BOM/onde-usado — renderização recursiva do payload oficial,
 * sem recomputar hierarquia no cliente. */
function ProductTree({
  nodes,
  childKey,
}: {
  nodes: ProductBomNode[] | ProductParentNode[];
  childKey: "components" | "parents";
}) {
  if (!nodes.length) return null;
  return (
    <ul className="engineering-product-tree">
      {nodes.map((node, index) => {
        const children =
          (node as Record<string, unknown>)[childKey] as
            | ProductBomNode[]
            | ProductParentNode[]
            | undefined;
        return (
          <li key={`${node.code}-${index}`}>
            <span className="engineering-product-tree-node">
              <strong>{node.code}</strong>
              {node.description ? ` — ${node.description}` : ""}
              <span className="engineering-product-tree-meta">
                {[
                  node.type ? productTypeLabel(node.type) : null,
                  node.quantity != null
                    ? `qtd ${node.quantity}`
                    : null,
                  node.unit,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </span>
            </span>
            {children?.length ? (
              <ProductTree nodes={children} childKey={childKey} />
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

const supplierColumns: DataTableColumn<ProductSupplier>[] = [
  {
    key: "supplier_code",
    header: "Fornecedor",
    render: (row) =>
      `${row.supplier_code}${row.supplier_store ? `/${row.supplier_store}` : ""}`,
  },
  {
    key: "supplier_name",
    header: "Nome",
    render: (row) => row.supplier_name ?? "—",
  },
  {
    key: "supplier_part_number",
    header: "Part number",
    render: (row) => row.supplier_part_number ?? "—",
  },
  {
    key: "lead_time",
    header: "Lead time",
    render: (row) =>
      row.registered_lead_time_days != null
        ? `${row.registered_lead_time_days} dia(s)`
        : "—",
  },
  {
    key: "real_lead_time",
    header: "Lead real (média)",
    render: (row) =>
      row.real_avg_lead_time_days != null
        ? `${row.real_avg_lead_time_days} dia(s)`
        : "—",
  },
];

function DrawingsSection({
  code,
  metadata,
}: {
  code: string;
  metadata: ProductDrawingMetadata;
}) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<unknown>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(
    () => () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    },
    [pdfUrl],
  );

  const openPdf = useCallback(async () => {
    setPdfLoading(true);
    setPdfError(null);
    try {
      const blob = await fetchProductDrawingPdf(code);
      setPdfUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return URL.createObjectURL(blob);
      });
    } catch (err) {
      setPdfError(err);
    } finally {
      setPdfLoading(false);
    }
  }, [code]);

  const openExternal = useCallback(() => {
    if (pdfUrl) window.open(pdfUrl, "_blank", "noopener,noreferrer");
  }, [pdfUrl]);

  return (
    <div className="engineering-product-drawing">
      <EngineeringDetailCard title="Desenho técnico">
        <EngineeringDetailFieldGrid
          fields={[
            field("Arquivo", metadata.filename),
            field("Revisão", metadata.revision),
            field("Variante", metadata.variant_suffix),
            field("Tamanho", formatBytes(metadata.size_bytes)),
            field(
              "Modificado em",
              formatProductDateTime(metadata.modified_at),
            ),
            field("Tipo de mídia", metadata.media_type),
          ]}
        />
      </EngineeringDetailCard>
      <div className="engineering-nc-actions">
        <EngineeringActionButton
          variant="primary"
          onClick={() => void openPdf()}
          disabled={pdfLoading}
        >
          {pdfLoading ? "Abrindo…" : pdfUrl ? "Recarregar PDF" : "Visualizar PDF"}
        </EngineeringActionButton>
        {pdfUrl ? (
          <EngineeringActionButton variant="ghost" onClick={openExternal}>
            Abrir ampliado
          </EngineeringActionButton>
        ) : null}
      </div>
      {pdfError ? <TabError error={pdfError} fallback="PDF indisponível." /> : null}
      {pdfUrl ? (
        <iframe
          className="engineering-product-drawing-frame"
          src={pdfUrl}
          title={`Desenho técnico do produto ${code}`}
        />
      ) : null}
    </div>
  );
}

export function ProductDetailPage({ code }: ProductDetailPageProps) {
  const [tab, setTab] = useState<TabKey>("overview");
  const [product, setProduct] = useState<ProductRecord | null>(null);
  const [productError, setProductError] = useState<unknown>(null);
  const [loadingProduct, setLoadingProduct] = useState(true);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const loadProduct = useCallback(() => {
    const controller = new AbortController();
    setLoadingProduct(true);
    setProductError(null);
    fetchProductDetail(code, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setProduct(result.product);
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) setProductError(err);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingProduct(false);
      });
    return () => controller.abort();
  }, [code]);

  useEffect(() => loadProduct(), [loadProduct]);

  const structure = useTabData(
    tab === "structure",
    useCallback(
      (signal: AbortSignal) => fetchProductStructure(code, signal),
      [code],
    ),
  );
  const parents = useTabData(
    tab === "whereUsed",
    useCallback(
      (signal: AbortSignal) => fetchProductParents(code, signal),
      [code],
    ),
  );
  const suppliers = useTabData(
    tab === "suppliers",
    useCallback(
      (signal: AbortSignal) => fetchProductSuppliers(code, signal),
      [code],
    ),
  );
  const drawing = useTabData(
    tab === "drawings",
    useCallback(
      (signal: AbortSignal) => fetchProductDrawing(code, signal),
      [code],
    ),
  );
  const history = useTabData(
    tab === "history",
    useCallback(
      (signal: AbortSignal) => fetchProductHistory(code, signal),
      [code],
    ),
  );

  const onTabKeyDown = useCallback(
    (event: React.KeyboardEvent, index: number) => {
      const last = TAB_ORDER.length - 1;
      let next: number | null = null;
      if (event.key === "ArrowRight") next = index === last ? 0 : index + 1;
      if (event.key === "ArrowLeft") next = index === 0 ? last : index - 1;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = last;
      if (next === null) return;
      event.preventDefault();
      const key = TAB_ORDER[next].key;
      setTab(key);
      tabRefs.current[key]?.focus();
    },
    [],
  );

  const statusLabel = product ? productStatusLabel(product) : null;
  const overview = useMemo(
    () => (product ? overviewFields(product) : null),
    [product],
  );

  return (
    <main className="engineering-products">
      <EngineeringPagePath
        back={{
          label: PRODUCT_COPY.breadcrumbBack,
          href: PRODUCT_PATHS.list,
          onNavigate: (event) => {
            event.preventDefault();
            navigateProducts(PRODUCT_PATHS.list);
          },
        }}
        items={[]}
        current={product ? product.code : "Ficha do Produto"}
      />

      <EngineeringPageHero
        eyebrow="Portal Engenharia"
        title={PRODUCT_COPY.detailTitle}
        description={
          product
            ? `${product.code} — ${product.description ?? ""} (${productTypeLabel(product.type)})`
            : `Produto ${code}`
        }
        actions={
          <>
            {statusLabel ? (
              <EngineeringStatusBadge
                label={statusLabel}
                variant={
                  statusLabel === "Ativo"
                    ? "success"
                    : statusLabel === "Bloqueado"
                      ? "error"
                      : "neutral"
                }
              />
            ) : null}
            <EngineeringStatusBadge
              label={PRODUCT_COPY.viewMode}
              variant="neutral"
            />
            <EngineeringActionButton
              variant="ghost"
              disabled
              title={PRODUCT_COPY.editBlocked}
              aria-label={`Editar — ${PRODUCT_COPY.editBlocked}`}
            >
              Editar
            </EngineeringActionButton>
          </>
        }
      />

      {loadingProduct ? (
        <EngineeringLoadingActivityCard
          title="Carregando ficha do produto"
          description="Consultando o cadastro oficial."
        />
      ) : null}

      {!loadingProduct && productError ? (
        <>
          <TabError
            error={productError}
            fallback="Ficha do produto indisponível."
          />
          <div className="engineering-nc-actions">
            <EngineeringActionButton
              variant="primary"
              onClick={() => navigateProducts(PRODUCT_PATHS.list)}
            >
              Voltar ao catálogo
            </EngineeringActionButton>
          </div>
        </>
      ) : null}

      {product ? (
        <>
          <nav
            className="engineering-product-tabs"
            role="tablist"
            aria-label="Seções da ficha do produto"
          >
            {TAB_ORDER.map((item, index) => (
              <button
                key={item.key}
                ref={(el) => {
                  tabRefs.current[item.key] = el;
                }}
                role="tab"
                type="button"
                id={`product-tab-${item.key}`}
                aria-selected={tab === item.key}
                aria-controls={`product-panel-${item.key}`}
                tabIndex={tab === item.key ? 0 : -1}
                className={`engineering-product-tab ${
                  tab === item.key ? "is-active" : ""
                }`}
                onClick={() => setTab(item.key)}
                onKeyDown={(event) => onTabKeyDown(event, index)}
              >
                {item.label}
              </button>
            ))}
          </nav>

          <div
            role="tabpanel"
            id={`product-panel-${tab}`}
            aria-labelledby={`product-tab-${tab}`}
          >
            {tab === "overview" && overview ? (
              <div className="engineering-product-overview">
                <EngineeringDetailCard title="Identificação">
                  <EngineeringDetailFieldGrid
                    fields={overview.identification}
                  />
                </EngineeringDetailCard>
                <EngineeringDetailCard title="Engenharia">
                  <EngineeringDetailFieldGrid fields={overview.engineering} />
                </EngineeringDetailCard>
                <EngineeringDetailCard title="Estoque e logística">
                  <EngineeringDetailFieldGrid fields={overview.logistics} />
                </EngineeringDetailCard>
              </div>
            ) : null}

            {tab === "structure" ? (
              <>
                {structure.loading ? (
                  <EngineeringLoadingActivityCard
                    title="Carregando estrutura"
                    description={PRODUCT_HELP.structure}
                  />
                ) : null}
                {structure.error ? (
                  <TabError
                    error={structure.error}
                    fallback="Estrutura indisponível."
                  />
                ) : null}
                {structure.data ? (
                  structure.data.items.length ? (
                    <ProductTree
                      nodes={structure.data.items}
                      childKey="components"
                    />
                  ) : (
                    <EngineeringEmptyState message="Este produto não possui estrutura cadastrada na fonte oficial." />
                  )
                ) : null}
              </>
            ) : null}

            {tab === "whereUsed" ? (
              <>
                {parents.loading ? (
                  <EngineeringLoadingActivityCard
                    title="Carregando onde é usado"
                    description={PRODUCT_HELP.whereUsed}
                  />
                ) : null}
                {parents.error ? (
                  <TabError
                    error={parents.error}
                    fallback="Consulta reversa indisponível."
                  />
                ) : null}
                {parents.data ? (
                  parents.data.items.length ? (
                    <ProductTree
                      nodes={parents.data.items}
                      childKey="parents"
                    />
                  ) : (
                    <EngineeringEmptyState message="Este produto não é componente de nenhuma estrutura cadastrada." />
                  )
                ) : null}
              </>
            ) : null}

            {tab === "suppliers" ? (
              <>
                {suppliers.loading ? (
                  <EngineeringLoadingActivityCard
                    title="Carregando fornecedores"
                    description={PRODUCT_HELP.suppliers}
                  />
                ) : null}
                {suppliers.error ? (
                  <TabError
                    error={suppliers.error}
                    fallback="Fornecedores indisponíveis."
                  />
                ) : null}
                {suppliers.data ? (
                  suppliers.data.items.length ? (
                    <DataTableSection
                      title={PRODUCT_COPY.tabs.suppliers}
                      titleHint={PRODUCT_HELP.leadTime}
                      columns={supplierColumns}
                      rows={suppliers.data.items}
                      rowKey={(row) =>
                        `${row.supplier_code}-${row.supplier_store}`
                      }
                      emptyMessage="Nenhum fornecedor vinculado."
                      hideSearch
                    />
                  ) : (
                    <EngineeringEmptyState message="Nenhum fornecedor vinculado a este produto na fonte oficial." />
                  )
                ) : null}
              </>
            ) : null}

            {tab === "drawings" ? (
              <>
                {drawing.loading ? (
                  <EngineeringLoadingActivityCard
                    title="Localizando desenho"
                    description={PRODUCT_HELP.drawings}
                  />
                ) : null}
                {drawing.error ? (
                  <TabError
                    error={drawing.error}
                    fallback="Acervo de desenhos indisponível."
                  />
                ) : null}
                {drawing.data ? (
                  <DrawingsSection code={code} metadata={drawing.data} />
                ) : null}
              </>
            ) : null}

            {tab === "history" ? (
              <div className="engineering-product-history">
                <EngineeringDetailCard title="Revisão cadastral">
                  <EngineeringDetailFieldGrid
                    fields={[
                      field(
                        "Revisão atual",
                        product.current_revision,
                        PRODUCT_HELP.revision,
                      ),
                      field(
                        "Última revisão",
                        formatProductDate(product.last_revision_date),
                        PRODUCT_HELP.revisionDate,
                      ),
                      field("Cadastrado por", product.created_by),
                      field("Atualizado por", product.updated_by),
                    ]}
                  />
                </EngineeringDetailCard>

                {history.loading ? (
                  <EngineeringLoadingActivityCard
                    title="Carregando histórico"
                    description={PRODUCT_HELP.history}
                  />
                ) : null}
                {history.error ? (
                  <TabError
                    error={history.error}
                    fallback="Histórico de compras indisponível."
                  />
                ) : null}
                {history.data ? (
                  <HistorySection history={history.data} />
                ) : null}

                <EngineeringEmptyState message="Histórico de revisões cadastrais não possui contrato oficial na fonte — seção pendente de decisão do owner (doc 63 §2.7)." />
              </div>
            ) : null}
          </div>
        </>
      ) : null}
    </main>
  );
}

function historyRows(payload: ProductPurchaseHistoryResult) {
  const sections: { title: string; rows: Record<string, unknown>[] }[] = [];
  for (const key of ["history", "price_history", "budget_history"]) {
    const rows = payload[key];
    if (Array.isArray(rows) && rows.length) {
      const title =
        key === "budget_history"
          ? "Histórico de orçamento de compra"
          : "Histórico de preço de compra";
      sections.push({ title, rows: rows as Record<string, unknown>[] });
    }
  }
  return sections;
}

function HistorySection({
  history,
}: {
  history: ProductPurchaseHistoryResult;
}) {
  const sections = historyRows(history);
  if (!sections.length) {
    return (
      <EngineeringEmptyState message="Nenhum histórico de compras registrado para este produto." />
    );
  }
  return (
    <>
      {sections.map((section) => {
        const keys = Array.from(
          new Set(section.rows.flatMap((row) => Object.keys(row))),
        );
        return (
          <EngineeringDetailCard key={section.title} title={section.title}>
            <div className="engineering-product-history-table-wrap">
              <table className="engineering-product-history-table">
                <thead>
                  <tr>
                    {keys.map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {section.rows.map((row, index) => (
                    <tr key={index}>
                      {keys.map((key) => (
                        <td key={key}>
                          {row[key] === null || row[key] === undefined
                            ? "—"
                            : String(row[key])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </EngineeringDetailCard>
        );
      })}
    </>
  );
}
