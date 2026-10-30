/**
 * Notas Fiscais a Desconsiderar — R11 — Central de Fechamento.
 *
 * Consome `GET /closing/billing-exclusion-roster` (+`/export`) da BFF.
 * Lista investigativa (doc 126/127): o universo «candidates» aplica o
 * predicado histórico observado no artefato de set/2026 — SD2 pelo eixo
 * D2_EMISSAO, grupo 9035 ∩ TES 594 (11 linhas / R$ 97.462,71) — sem
 * comprovar generalização para outras competências (E11b pendente).
 * A visão «out_of_criteria» expõe linhas relacionadas fora do predicado,
 * com totalizadores próprios, nunca somados ao conjunto candidato.
 *
 * Achados são sempre POSSIBLE_DIVERGENCE ou explicações estruturais —
 * nunca erro confirmado. Nenhuma nota é excluída automaticamente de
 * CPV, faturamento, estoque ou DRE: a correção é atividade humana
 * externa no TOTVS/Protheus (E11a pendente — a apuração afetada ainda
 * não foi comprovada).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import { saveDocumentBlob } from "../../api/documentsApi";
import {
  billingExclusionExportFilename,
  exportBillingExclusionRoster,
  getBillingExclusionRoster,
  type BillingExclusionItem,
  type BillingExclusionPayload,
  type BillingExclusionView,
  type StockInventoryBranch,
} from "../../api/billingExclusionRosterApi";
import {
  CfActionButton,
  CfMetricStrip,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";
import {
  CalendarDays,
  CircleDollarSign,
  Download,
  ListOrdered,
  OctagonAlert,
} from "lucide-react";
import {
  ClosingHero,
  type ClosingHeroMetric,
} from "../../app/ClosingHero";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import {
  FilterInputField,
  FilterSelectField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { CF_HELP } from "../../content/helpTooltips";
import {
  formatAmount,
  formatCivilDate,
  formatQuantity,
} from "../../utils/formatters";

const BRANCH_OPTIONS = [
  { value: "all", label: "Todas as filiais" },
  { value: "01", label: "Matriz (01)" },
  { value: "02", label: "Filial 02" },
] as const;

const VIEW_OPTIONS = [
  { value: "candidates", label: "Candidatas (critério histórico)" },
  { value: "out_of_criteria", label: "Relacionadas fora do critério" },
  { value: "all", label: "Todas (universo ampliado)" },
] as const;

const STATUS_LABELS: Record<string, string> = {
  available: "Disponível",
  no_matching_items: "Sem dados para o filtro",
};

const RULE_LABELS: Record<string, string> = {
  "DV-R11-01": "Critério histórico",
  "DV-R11-02": "Custo estrutural zero",
  "DV-R11-03": "Sem item-irmão de estoque",
  "DV-R11-04": "Fora do critério observado",
};

const SELECTION_STATUS_LABELS: Record<string, string> = {
  matches_historical_criteria: "Candidata",
  related_out_of_criteria: "Fora do critério",
};

const VIEW_LABELS: Record<BillingExclusionView, string> = {
  candidates: "candidatas",
  out_of_criteria: "relacionadas fora do critério",
  all: "universo ampliado",
};

function currentCompetence(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

type AppliedFilters = {
  period: string;
  branch: StockInventoryBranch;
  view: BillingExclusionView;
  productGroup: string;
  productCode: string;
  document: string;
  tes: string;
  page: number;
  pageSize: number;
};

type FetchResult =
  | { key: string; kind: "error"; status: number; code: string | null; message: string }
  | { key: string; kind: "ready"; payload: BillingExclusionPayload };

export type BillingExclusionReportContext = { period: string };

export function BillingExclusionRosterPage({
  reportContext,
}: {
  reportContext?: BillingExclusionReportContext;
}) {
  const [period, setPeriod] = useState(
    () => reportContext?.period ?? currentCompetence(),
  );
  const [branch, setBranch] = useState<StockInventoryBranch>("all");
  const [view, setView] = useState<BillingExclusionView>("candidates");
  const [productGroup, setProductGroup] = useState("");
  const [productCode, setProductCode] = useState("");
  const [document, setDocument] = useState("");
  const [tes, setTes] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [result, setResult] = useState<FetchResult | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const requestId = useRef(0);

  const effectivePeriod = reportContext?.period ?? period;
  const filtersValid = /^\d{4}-(0[1-9]|1[0-2])$/.test(effectivePeriod);
  const applied: AppliedFilters | null = useMemo(
    () =>
      filtersValid
        ? {
            period: effectivePeriod,
            branch,
            view,
            productGroup: productGroup.trim(),
            productCode: productCode.trim(),
            document: document.trim(),
            tes: tes.trim(),
            page,
            pageSize,
          }
        : null,
    [
      filtersValid,
      effectivePeriod,
      branch,
      view,
      productGroup,
      productCode,
      document,
      tes,
      page,
      pageSize,
    ],
  );

  const clearFilters = useCallback(() => {
    setPeriod(reportContext?.period ?? currentCompetence());
    setBranch("all");
    setView("candidates");
    setProductGroup("");
    setProductCode("");
    setDocument("");
    setTes("");
    setPage(1);
  }, [reportContext]);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  const handleExport = useCallback(
    async (format: "csv" | "pdf") => {
      if (!applied || exporting) return;
      setExporting(format);
      setExportError(null);
      try {
        const blob = await exportBillingExclusionRoster(
          {
            period: applied.period,
            branch: applied.branch,
            view: applied.view,
            productGroup: applied.productGroup || undefined,
            productCode: applied.productCode || undefined,
            document: applied.document || undefined,
            tes: applied.tes || undefined,
          },
          format,
        );
        saveDocumentBlob(
          blob,
          billingExclusionExportFilename(applied, format),
        );
      } catch (error) {
        setExportError(
          error instanceof ApiError
            ? error.message
            : "Não foi possível exportar o relatório agora.",
        );
      } finally {
        setExporting(null);
      }
    },
    [applied, exporting],
  );

  const queryKey = applied
    ? JSON.stringify({ ...applied, retryNonce })
    : null;
  const current: FetchResult | null =
    result && result.key === queryKey ? result : null;
  const loading = applied !== null && current === null;
  const payload = current?.kind === "ready" ? current.payload : null;

  useEffect(() => {
    if (!applied || !queryKey) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    getBillingExclusionRoster(
      {
        period: applied.period,
        branch: applied.branch,
        view: applied.view,
        productGroup: applied.productGroup || undefined,
        productCode: applied.productCode || undefined,
        document: applied.document || undefined,
        tes: applied.tes || undefined,
        page: applied.page,
        pageSize: applied.pageSize,
      },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setResult({ key: queryKey, kind: "ready", payload: data });
        setLastUpdated(new Date());
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setResult({
          key: queryKey,
          kind: "error",
          status: error instanceof ApiError ? error.status : 0,
          code: error instanceof ApiError ? error.code : null,
          message:
            error instanceof ApiError
              ? error.message
              : "Falha de comunicação com a API de notas a desconsiderar.",
        });
      });
    return () => controller.abort();
  }, [applied, queryKey]);

  const columns = useMemo<DataTableColumn<BillingExclusionItem>[]>(
    () => [
      {
        key: "issueDate",
        header: "Emissão",
        headerHint: CF_HELP.billingExclusionRoster.columns.issueDate,
        render: (row) => formatCivilDate(row.issueDate),
      },
      {
        key: "document",
        header: "Documento",
        render: (row) => (
          <div>
            <div>{row.document}</div>
            <div className="cf-cell-muted">
              {row.series ? `série ${row.series} · ` : ""}item {row.item} ·{" "}
              {row.documentItemCount} item(ns)
            </div>
          </div>
        ),
      },
      {
        key: "productCode",
        header: "Produto",
        headerHint: CF_HELP.billingExclusionRoster.columns.product,
        render: (row) => (
          <div>
            <div>{row.productCode}</div>
            <div className="cf-cell-muted">
              {row.productDescription ?? ""}
              {row.productGroup ? ` · grupo ${row.productGroup}` : ""}
            </div>
          </div>
        ),
      },
      {
        key: "tes",
        header: "TES / CFOP",
        render: (row) => (
          <div>
            <div>{row.tes ?? "—"}</div>
            <div className="cf-cell-muted">
              CFOP {row.cf ?? "—"}
              {row.tesStockMovement === "N" ? " · sem estoque" : ""}
            </div>
          </div>
        ),
      },
      {
        key: "customer",
        header: "Cliente",
        render: (row) => (
          <div>
            <div>{row.customerCode ?? "—"}</div>
            <div className="cf-cell-muted">{row.customerName ?? ""}</div>
          </div>
        ),
      },
      {
        key: "quantity",
        header: "Quantidade",
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatQuantity(row.quantity)}
          </span>
        ),
      },
      {
        key: "totalValue",
        header: "Valor",
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.totalValue)}
          </span>
        ),
      },
      {
        key: "stockCost",
        header: "Custo",
        headerHint: CF_HELP.billingExclusionRoster.columns.cost,
        align: "right",
        className: "cf-table__col--numeric",
        render: (row) => (
          <span className="cf-cell-amount">
            {formatAmount(row.stockCost)}
          </span>
        ),
      },
      {
        key: "selectionStatus",
        header: "Situação",
        headerHint: CF_HELP.billingExclusionRoster.columns.status,
        render: (row) => (
          <div className="cf-page-stack">
            <CfStatusBadge
              label={
                SELECTION_STATUS_LABELS[row.selectionStatus] ??
                row.selectionStatus
              }
              variant={
                row.selectionStatus === "matches_historical_criteria"
                  ? "warning"
                  : "info"
              }
            />
            {row.hasStockSiblingItem ? null : (
              <CfStatusBadge
                label="Sem item-irmão de estoque"
                variant="warning"
              />
            )}
          </div>
        ),
      },
      {
        key: "findings",
        header: "Alertas",
        headerHint: CF_HELP.billingExclusionRoster.columns.findings,
        className: "cf-table__col--status",
        render: (row) =>
          row.findings.length > 0 ? (
            <div className="cf-page-stack">
              {row.findings.map((ruleId) => (
                <CfStatusBadge
                  key={ruleId}
                  label={RULE_LABELS[ruleId] ?? ruleId}
                  variant={
                    ruleId === "DV-R11-02" ? "info" : "warning"
                  }
                />
              ))}
            </div>
          ) : (
            "—"
          ),
      },
    ],
    [],
  );

  const heroMetrics = useMemo<ClosingHeroMetric[] | undefined>(() => {
    if (!payload) {
      return loading
        ? [
            {
              id: "status",
              label: "Disponibilidade",
              value: "",
              icon: <CalendarDays size={20} aria-hidden />,
            },
          ]
        : undefined;
    }
    const summary = payload.summary;
    return [
      {
        id: "status",
        label: "Disponibilidade",
        value: STATUS_LABELS[payload.status] ?? payload.status,
        hint: `competência ${payload.period} · ${VIEW_LABELS[payload.view]}`,
        tone: payload.status === "available" ? "default" : "warning",
        icon: <CalendarDays size={20} aria-hidden />,
      },
      {
        id: "lines",
        label: "Linhas",
        value: String(summary?.lineCount ?? 0),
        hint: `${summary?.documentCount ?? 0} documentos · ${summary?.candidateLineCount ?? 0} candidata(s)`,
        icon: <ListOrdered size={20} aria-hidden />,
      },
      {
        id: "total",
        label: "Valor total",
        value: formatAmount(summary?.totalValue ?? "0"),
        hint:
          payload.view === "candidates"
            ? "universo do critério histórico"
            : "visão investigativa — nunca somada",
        icon: <CircleDollarSign size={20} aria-hidden />,
      },
      {
        id: "findings",
        label: "Possíveis divergências",
        value: String(summary?.findingCount ?? 0),
        hint: "candidatos a revisão no ERP",
        tone: (summary?.findingCount ?? 0) > 0 ? "warning" : "default",
        icon: <OctagonAlert size={20} aria-hidden />,
      },
    ];
  }, [payload, loading]);

  const renderStatusBanner = () => {
    if (!payload) return null;
    if (payload.status === "no_matching_items") {
      return (
        <CfFeedbackMessage intent="info" title="Sem dados para o filtro">
          A origem respondeu, mas nenhuma nota fiscal corresponde aos
          filtros aplicados nesta visão.
        </CfFeedbackMessage>
      );
    }
    return null;
  };

  const exportDisabled = exporting !== null || !payload;

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Notas fiscais a desconsiderar — R11"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Notas fiscais a desconsiderar — R11"
            hint={CF_HELP.billingExclusionRoster.page}
          />
        }
        subtitle={
          reportContext
            ? `Notas da competência ${reportContext.period} selecionadas pelo critério histórico observado — conferência no ERP.`
            : "Lista investigativa de notas fiscais (eixo de emissão) — critério histórico observado e possíveis divergências. Leitura: nenhuma correção é executada no ERP."
        }
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage
            intent="info"
            title="Lista investigativa — não é exclusão oficial"
          >
            Seleção histórica reproduzida para set/2026 filial 01 (11
            linhas / R$ 97.462,71, grupo 9035 ∩ TES 594). A finalidade da
            desconsideração e o predicado oficial seguem pendentes de
            decisão funcional — esta lista não autoriza excluir notas de
            CPV, faturamento ou DRE; a correção é atividade humana no
            Protheus.
          </CfFeedbackMessage>
        }
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <FiltersRow>
              {reportContext ? null : (
                <FilterInputField
                  id="cf-r11-period"
                  label="Competência"
                  type="month"
                  value={period}
                  onChange={setPeriod}
                />
              )}
              <FilterSelectField
                label="Filial"
                value={branch}
                onChange={(value) =>
                  setBranch(value as StockInventoryBranch)
                }
                options={BRANCH_OPTIONS}
              />
              <FilterSelectField
                label="Visão"
                value={view}
                onChange={(value) => {
                  setView(value as BillingExclusionView);
                  setPage(1);
                }}
                options={VIEW_OPTIONS}
              />
              <FilterInputField
                id="cf-r11-group"
                label="Grupo"
                type="text"
                value={productGroup}
                onChange={setProductGroup}
                placeholder="ex.: 9035"
              />
              <FilterInputField
                id="cf-r11-product"
                label="Produto"
                type="text"
                value={productCode}
                onChange={setProductCode}
                placeholder="código"
              />
              <FilterInputField
                id="cf-r11-doc"
                label="Documento"
                type="text"
                value={document}
                onChange={setDocument}
                placeholder="número"
              />
              <FilterInputField
                id="cf-r11-tes"
                label="TES"
                type="text"
                value={tes}
                onChange={setTes}
                placeholder="ex.: 594"
              />
            </FiltersRow>
            {!filtersValid ? (
              <CfFeedbackMessage intent="error" title="Competência inválida">
                Informe uma competência válida no formato AAAA-MM.
              </CfFeedbackMessage>
            ) : null}
            {payload && payload.view !== "candidates" ? (
              <CfFeedbackMessage
                intent="info"
                title="Visão investigativa"
              >
                Estas linhas ficam fora do critério histórico observado —
                os totais desta visão nunca se somam ao conjunto
                candidato e não representam notas a desconsiderar sem
                decisão funcional.
              </CfFeedbackMessage>
            ) : null}
          </form>
        }
        onClearFilters={clearFilters}
        extraActions={
          <>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("csv")}
              disabled={exportDisabled}
              title={CF_HELP.billingExclusionRoster.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "csv" ? "Exportando…" : "Exportar CSV"}
            </CfActionButton>
            <CfActionButton
              variant="ghost"
              type="button"
              onClick={() => handleExport("pdf")}
              disabled={exportDisabled}
              title={CF_HELP.billingExclusionRoster.export}
            >
              <Download size={16} aria-hidden />{" "}
              {exporting === "pdf" ? "Exportando…" : "Exportar PDF"}
            </CfActionButton>
          </>
        }
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {exportError ? (
          <CfFeedbackMessage intent="error" title="Exportação não concluída">
            {exportError}
          </CfFeedbackMessage>
        ) : null}
        {current?.kind === "error" ? (
          <CfQueryErrorBanner
            error={current}
            dataset="as notas fiscais a desconsiderar"
            onRetry={retry}
          />
        ) : null}
        {renderStatusBanner()}

        {payload?.summary ? (
          <CfSectionCard
            title="Totais da visão"
            hint={CF_HELP.billingExclusionRoster.totals}
          >
            <CfMetricStrip
              aria-label="Totais das notas a desconsiderar"
              items={[
                {
                  id: "lines",
                  label: "Linhas",
                  value: String(payload.summary.lineCount),
                  description: `${payload.summary.documentCount} documentos`,
                },
                {
                  id: "total",
                  label: "Valor total",
                  value: formatAmount(payload.summary.totalValue),
                  description:
                    payload.view === "candidates"
                      ? "critério histórico"
                      : "investigação — nunca somado",
                },
                {
                  id: "zerocost",
                  label: "Custo zero estrutural",
                  value: String(payload.summary.zeroCostCount),
                  description: `${payload.summary.missingStockSiblingDocumentCount} doc(s) sem item-irmão de estoque`,
                },
                {
                  id: "findings",
                  label: "Possíveis divergências",
                  value: String(payload.summary.findingCount),
                  description:
                    "candidatos a revisão — não são erro confirmado",
                },
              ]}
            />
            <p className="cf-cell-muted">
              <CfStatusBadge
                label={
                  payload.parityStatus === "PENDING"
                    ? "Paridade oficial: pendente"
                    : `Paridade: ${payload.parityStatus}`
                }
                variant="warning"
              />{" "}
              {(payload.parityNotes ?? []).join(" ")}
            </p>
          </CfSectionCard>
        ) : null}

        {payload && payload.findings.length > 0 ? (
          <CfSectionCard
            title="Findings e explicações"
            hint={CF_HELP.billingExclusionRoster.findings}
          >
            <ul className="cf-page-stack" aria-label="Lista de findings investigativos">
              {payload.findings.slice(0, 25).map((finding) => {
                const src = finding.sourceRecord as Record<
                  string,
                  unknown
                >;
                return (
                  <li key={finding.findingId}>
                    <CfFeedbackMessage
                      intent={
                        finding.ruleId === "DV-R11-02"
                          ? "info"
                          : "warning"
                      }
                      title={`${RULE_LABELS[finding.ruleId] ?? finding.ruleId} — doc ${src.document ?? "—"} item ${src.item ?? "—"}`}
                    >
                      {finding.findingExplanation}
                      <br />
                      <span className="cf-cell-muted">
                        Produto {String(src.productCode ?? "—")} · TES{" "}
                        {String(src.tes ?? "—")} · CFOP{" "}
                        {String(src.cf ?? "—")} ·{" "}
                        {finding.erpReviewGuidance}
                      </span>
                    </CfFeedbackMessage>
                  </li>
                );
              })}
            </ul>
            {payload.findingsTruncated || payload.findings.length > 25 ? (
              <p className="cf-cell-muted">
                Exibindo {Math.min(payload.findings.length, 25)} de{" "}
                {payload.summary?.findingCount ?? payload.findings.length}{" "}
                achados — use a exportação para a lista completa.
              </p>
            ) : null}
          </CfSectionCard>
        ) : null}

        <DataTableSection<BillingExclusionItem>
          title={
            payload?.view === "candidates"
              ? "Notas do critério histórico observado"
              : payload?.view === "out_of_criteria"
                ? "Linhas relacionadas fora do critério"
                : "Universo investigativo ampliado"
          }
          titleHint={CF_HELP.billingExclusionRoster.table}
          columns={columns}
          rows={payload?.items ?? []}
          rowKey={(row) => String(row.lineId)}
          loading={loading}
          hideSearch
          emptyMessage="Nenhuma nota no período para os filtros aplicados."
          columnPreferencesKey="cf:closing:billing-exclusion-roster:v1"
          serverPagination={
            payload?.pagination
              ? {
                  page: payload.pagination.page,
                  pageSize: payload.pagination.page_size,
                  total: payload.pagination.total_items,
                  onPageChange: setPage,
                  onPageSizeChange: (size) => {
                    setPageSize(size);
                    setPage(1);
                  },
                }
              : undefined
          }
        />
      </div>
    </section>
  );
}
