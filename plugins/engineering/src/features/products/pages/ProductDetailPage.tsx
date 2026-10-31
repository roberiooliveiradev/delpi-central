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
import { ProductStructureTree } from "../../lmps/components/ProductStructureTree";
import { StructureLegend } from "../../lmps/components/StructureLegend";
import type { ProductStructureData } from "../../lmps/types/productStructure";
import type { RichTreeNode } from "../../lmps/types/richTree";
import {
  buildProductStructureTree,
  countRichTreeNodes,
} from "../../lmps/utils/productStructureTree";
import {
  FilePreviewView,
  useFilePreviewLoader,
} from "@delpi/plugin-ui/index";
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
  productDescriptionDisplay,
  productStatusLabel,
  productTypeLabel,
} from "../productCopy";
import {
  PRODUCT_PATHS,
  navigateProducts,
  parseProductTab,
  productDetailTabPath,
  useLocationSearch,
  type ProductTabKey,
} from "../productRoutes";
import type {
  ProductDrawingMetadata,
  ProductPurchaseHistoryResult,
  ProductRecord,
  ProductSupplier,
} from "../types";

type ProductDetailPageProps = {
  code: string;
};

const TAB_ORDER: readonly { key: ProductTabKey; label: string }[] = [
  { key: "overview", label: PRODUCT_COPY.tabs.overview },
  { key: "structure", label: PRODUCT_COPY.tabs.structure },
  { key: "where-used", label: PRODUCT_COPY.tabs.whereUsed },
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
  /** Identidade do recurso — troca de produto invalida o cache local
   * para nunca reaproveitar dados da ficha anterior. */
  resourceKey: string,
  fetcher: (signal: AbortSignal) => Promise<T>,
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const loadedFor = useRef<string | null>(null);

  useEffect(() => {
    if (loadedFor.current !== resourceKey) {
      loadedFor.current = null;
      setData(null);
      setError(null);
    }
    if (!active || loadedFor.current === resourceKey) return undefined;
    const controller = new AbortController();
    setLoading(true);
    fetcher(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          loadedFor.current = resourceKey;
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
  }, [active, resourceKey, fetcher]);

  return { data, error, loading };
}

function field(
  label: string,
  value: ReactNode,
  hint?: string,
): { label: string; value: ReactNode; hint?: string } {
  return { label, value: value ?? "—", hint };
}

/** Descrição oficial exibida como gravada — placeholders ("#") ficam
 * sinalizados como não informativos sem inventar substituto. */
function descriptionValue(description: string | null): ReactNode {
  const display = productDescriptionDisplay(description);
  if (display.informative || display.text === "—") return display.text;
  return (
    <span
      className="engineering-products__placeholder-value"
      title={PRODUCT_HELP.nonInformativeDescription}
    >
      {display.text}
    </span>
  );
}

function overviewFields(product: ProductRecord) {
  return {
    identification: [
      field("Código", product.code, PRODUCT_HELP.code),
      field(
        "Descrição",
        descriptionValue(product.description),
        PRODUCT_HELP.description,
      ),
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

/** Teto de segurança para "Expandir todos" — acima disso o DOM da
 * árvore fica pesado demais para uma ação única (doc 67 §3.3). */
const EXPAND_ALL_NODE_LIMIT = 600;

/** Card R2 das abas Estrutura/Onde é usado: título oficial + contagem +
 * toolbar Expandir/Recolher todos sobre a ProductStructureTree oficial.
 * Expandir/recolher tudo = remontar a árvore com outro `expandDepth`
 * (`key` por época) — zero alteração no estado interno do RichTree. */
function ProductTreeCard({
  title,
  hint,
  structure,
  onNodeNavigate,
  footerLabel,
}: {
  title: string;
  hint?: string;
  structure: ProductStructureData;
  onNodeNavigate: (node: RichTreeNode) => void;
  footerLabel: (nodeCount: number) => string;
}) {
  const root = useMemo(() => buildProductStructureTree(structure), [structure]);
  const nodeCount = useMemo(
    () => (root ? countRichTreeNodes(root) : 0),
    [root],
  );
  const [expandDepth, setExpandDepth] = useState(1);
  const [epoch, setEpoch] = useState(0);
  const canExpandAll = nodeCount <= EXPAND_ALL_NODE_LIMIT;

  return (
    <EngineeringDetailCard
      title={title}
      titleHint={hint}
      hint={`${nodeCount} nó(s)`}
      headerActions={
        root ? (
          <div
            className="engineering-product-tree__toolbar"
            role="group"
            aria-label="Ações da árvore"
          >
            <EngineeringActionButton
              variant="ghost"
              disabled={!canExpandAll}
              title={
                canExpandAll
                  ? "Expandir todos os níveis da árvore"
                  : `Indisponível acima de ${EXPAND_ALL_NODE_LIMIT} nós`
              }
              onClick={() => {
                setExpandDepth(Number.MAX_SAFE_INTEGER);
                setEpoch((value) => value + 1);
              }}
            >
              Expandir todos
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="ghost"
              title="Recolher todos os níveis"
              onClick={() => {
                setExpandDepth(0);
                setEpoch((value) => value + 1);
              }}
            >
              Recolher todos
            </EngineeringActionButton>
          </div>
        ) : null
      }
    >
      <div className="engineering-lmps">
        <StructureLegend />
        <ProductStructureTree
          key={epoch}
          structure={structure}
          expandDepth={expandDepth}
          onNodeNavigate={onNodeNavigate}
          footerLabel={footerLabel}
        />
      </div>
    </EngineeringDetailCard>
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

/** Pré-visualização automática do desenho — viewer oficial do kit
 * (`useFilePreviewLoader` + `FilePreviewView`): blob autenticado,
 * object URL revogada no cleanup e requests cancelados na troca de aba. */
function DrawingsSection({
  code,
  metadata,
}: {
  code: string;
  metadata: ProductDrawingMetadata;
}) {
  const source = useCallback(() => fetchProductDrawingPdf(code), [code]);
  const preview = useFilePreviewLoader({
    source: metadata.found ? source : null,
    mimeType: metadata.media_type ?? "application/pdf",
    fileName: metadata.filename,
    enabled: metadata.found,
  });

  const openExternal = useCallback(() => {
    if (preview.previewUrl) {
      window.open(preview.previewUrl, "_blank", "noopener,noreferrer");
    }
  }, [preview.previewUrl]);

  const download = useCallback(() => {
    if (!preview.previewUrl) return;
    const anchor = document.createElement("a");
    anchor.href = preview.previewUrl;
    anchor.download = metadata.filename ?? `${code}.pdf`;
    anchor.rel = "noopener";
    anchor.click();
  }, [preview.previewUrl, metadata.filename, code]);

  if (!metadata.found) {
    return (
      <EngineeringEmptyState
        message={
          metadata.message ??
          "Nenhum desenho técnico localizado para este produto na fonte oficial."
        }
      />
    );
  }

  return (
    <div className="engineering-product-drawing__workspace">
      <div
        className="engineering-product-drawing__bar"
        role="group"
        aria-label="Metadados do desenho técnico"
      >
        <dl className="engineering-product-drawing__meta">
          <div>
            <dt>Arquivo</dt>
            <dd title={metadata.filename ?? undefined}>
              {metadata.filename ?? "—"}
            </dd>
          </div>
          <div>
            <dt>Revisão</dt>
            <dd>{metadata.revision?.trim() || "Revisão não informada"}</dd>
          </div>
          {metadata.variant_suffix ? (
            <div>
              <dt>Variante</dt>
              <dd>{metadata.variant_suffix}</dd>
            </div>
          ) : null}
          <div>
            <dt>Tamanho</dt>
            <dd>{formatBytes(metadata.size_bytes)}</dd>
          </div>
          <div>
            <dt>Modificado em</dt>
            <dd>{formatProductDateTime(metadata.modified_at)}</dd>
          </div>
          <div>
            <dt>Tipo</dt>
            <dd>{metadata.media_type ?? "—"}</dd>
          </div>
        </dl>
        <div className="engineering-product-drawing__actions">
          {preview.previewUrl ? (
            <>
              <EngineeringActionButton variant="ghost" onClick={openExternal}>
                Abrir ampliado
              </EngineeringActionButton>
              <EngineeringActionButton variant="ghost" onClick={download}>
                Baixar PDF
              </EngineeringActionButton>
            </>
          ) : null}
        </div>
      </div>
      <div className="engineering-product-drawing__viewer">
        <FilePreviewView
          state={preview}
          title={metadata.filename ?? `Desenho do produto ${code}`}
          labels={{
            loading: "Carregando desenho técnico…",
            loadFailed: "Não foi possível carregar o desenho técnico.",
          }}
        />
      </div>
    </div>
  );
}

export function ProductDetailPage({ code }: ProductDetailPageProps) {
  const search = useLocationSearch();
  const tab = parseProductTab(search);
  const goToProduct = useCallback((node: RichTreeNode) => {
    if (node.navCode) navigateProducts(PRODUCT_PATHS.detail(node.navCode));
  }, []);
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
    code,
    useCallback(
      (signal: AbortSignal) => fetchProductStructure(code, signal),
      [code],
    ),
  );
  const parents = useTabData(
    tab === "where-used",
    code,
    useCallback(
      (signal: AbortSignal) => fetchProductParents(code, signal),
      [code],
    ),
  );
  const suppliers = useTabData(
    tab === "suppliers",
    code,
    useCallback(
      (signal: AbortSignal) => fetchProductSuppliers(code, signal),
      [code],
    ),
  );
  const drawing = useTabData(
    tab === "drawings",
    code,
    useCallback(
      (signal: AbortSignal) => fetchProductDrawing(code, signal),
      [code],
    ),
  );
  const history = useTabData(
    tab === "history",
    code,
    useCallback(
      (signal: AbortSignal) => fetchProductHistory(code, signal),
      [code],
    ),
  );

  /** Aba é estado de URL — clique registra entrada de histórico e
   * back/forward do navegador navegam entre seções da ficha. */
  const selectTab = useCallback(
    (key: ProductTabKey) => {
      if (key === tab) return;
      navigateProducts(productDetailTabPath(code, key));
    },
    [code, tab],
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
      selectTab(key);
      tabRefs.current[key]?.focus();
    },
    [selectTab],
  );

  /** `?tab=` inválido/legado → normaliza para a aba resolvida sem
   * poluir o histórico (replace). */
  useEffect(() => {
    const raw = new URLSearchParams(search).get("tab");
    if (raw && raw !== tab) {
      navigateProducts(productDetailTabPath(code, tab), { replace: true });
    }
  }, [search, tab, code]);

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
            ? `${product.code} — ${productDescriptionDisplay(product.description).text} (${productTypeLabel(product.type)})`
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
                      ? "danger"
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
                onClick={() => selectTab(item.key)}
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
                  {product.drawing_code ? (
                    <div className="engineering-product-overview__drawing-link">
                      <EngineeringActionButton
                        variant="ghost"
                        title="Abrir a aba Desenhos desta ficha"
                        onClick={() => selectTab("drawings")}
                      >
                        Ver desenho técnico
                      </EngineeringActionButton>
                    </div>
                  ) : null}
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
                    <ProductTreeCard
                      title="Estrutura do produto"
                      hint={PRODUCT_HELP.structure}
                      structure={structure.data}
                      onNodeNavigate={goToProduct}
                      footerLabel={(count) =>
                        `${count} componente(s) na estrutura`
                      }
                    />
                  ) : (
                    <EngineeringEmptyState message="Este produto não possui estrutura cadastrada na fonte oficial." />
                  )
                ) : null}
              </>
            ) : null}

            {tab === "where-used" ? (
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
                    <ProductTreeCard
                      title="Onde é usado"
                      hint={PRODUCT_HELP.whereUsed}
                      structure={parents.data}
                      onNodeNavigate={goToProduct}
                      footerLabel={(count) =>
                        `${count} produto(s) utilizam este componente`
                      }
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
