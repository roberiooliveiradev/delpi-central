/**
 * Checklist da competência — Central de Fechamento (P2-READ).
 *
 * Consome `GET|POST /closing/competences*` da BFF. Exibe o snapshot dos
 * itens esperados da competência — «Esperado» nunca é apresentado como
 * documento entregue, recebido ou validado. Lacunas reais do checklist
 * (destinatário, R-ID) aparecem como pendências, nunca inventadas.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  createExceptionalItem,
  getCompetenceItem,
  listCompetences,
  listCompetenceItems,
  openCompetence,
  type ClosingCompetence,
  type CompetenceChecklistItem,
  type CompetenceChecklistItemDetail,
  type CompetenceItemBranchScope,
  type CompetenceItemOrigin,
  type CompetenceItemRecipient,
  type CompetenceSheet,
} from "../../api/competencesApi";
import {
  CfActionButton,
  CfDialog,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  CalendarDays,
  ClipboardList,
  FolderOpen,
  Layers,
  ListChecks,
} from "lucide-react";
import {
  ClosingHero,
  type ClosingHeroMetric,
} from "../../app/ClosingHero";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import {
  FilterInputField,
  FilterSelectField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { CF_HELP } from "../../content/helpTooltips";
import { buildPluginPath } from "../../app/pluginRoutes";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { ClosingDocumentsPanel } from "./ClosingDocumentsPanel";
import { ItemValidationPanel } from "./ItemValidationPanel";
import { P3CutoffPanel } from "./P3CutoffPanel";
import { ReportsMatrixPanel } from "./ReportsMatrixPanel";

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

const SHEET_OPTIONS = [
  { value: "", label: "Todas as origens de folha" },
  { value: "ELETRONICO", label: "Eletrônico" },
  { value: "FISICO", label: "Físico" },
] as const;

const ORIGIN_OPTIONS = [
  { value: "", label: "Todas as fontes" },
  { value: "TOTVS", label: "ERP TOTVS" },
  { value: "EXTERNAL", label: "Fonte externa" },
  { value: "MIXED", label: "Origem mista" },
] as const;

const RECIPIENT_OPTIONS = [
  { value: "", label: "Todos os destinatários" },
  { value: "CONTABIL", label: "Contábil" },
  { value: "FISCAL", label: "Fiscal" },
] as const;

const BRANCH_OPTIONS = [
  { value: "", label: "Todos os escopos" },
  { value: "MATRIX", label: "Matriz" },
  { value: "BRANCH", label: "Filial" },
  { value: "BOTH", label: "Matriz e filial" },
] as const;

const ORIGIN_LABELS: Record<string, string> = {
  TOTVS: "ERP TOTVS",
  EXTERNAL: "Externa",
  MIXED: "Mista",
};

const RECIPIENT_LABELS: Record<string, string> = {
  CONTABIL: "Contábil",
  FISCAL: "Fiscal",
};

const BRANCH_LABELS: Record<string, string> = {
  MATRIX: "Matriz",
  BRANCH: "Filial",
  BOTH: "Matriz e filial",
};

const STATE_LABELS: Record<string, string> = {
  EXPECTED: "Esperado",
  ACCEPTED: "Aceito",
  NOT_APPLICABLE: "Não aplicável",
  CANCELLED: "Cancelado",
};

const VALIDATION_SCOPE_LABELS: Record<string, string> = {
  PER_ATTACHMENT: "Por anexo",
  WHOLE_SET: "Conjunto",
};

const APPLICABILITY_OPTIONS = [
  { value: "REQUIRED", label: "Obrigatório" },
  { value: "CONDITIONAL", label: "Condicional" },
  { value: "OPTIONAL", label: "Opcional" },
] as const;

type QueryError = {
  status: number;
  code: string | null;
  message: string;
};

function toQueryError(error: unknown, fallback: string): QueryError {
  if (error instanceof ApiError) {
    return { status: error.status, code: error.code, message: error.message };
  }
  return { status: 0, code: null, message: fallback };
}

function currentCompetence(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

type ItemsResult =
  | { key: string; kind: "ready"; items: CompetenceChecklistItem[] }
  | { key: string; kind: "not_opened" }
  | { key: string; kind: "error"; error: QueryError };

export function ClosingChecklistPage({ period }: { period?: string }) {
  const [selectedPeriod, setSelectedPeriod] = useState(
    period ?? currentCompetence(),
  );
  const [competences, setCompetences] = useState<{
    key: string;
    data: ClosingCompetence[];
  } | null>(null);
  const [itemsResult, setItemsResult] = useState<ItemsResult | null>(null);
  const [listError, setListError] = useState<{
    key: string;
    error: QueryError;
  } | null>(null);
  const [opening, setOpening] = useState(false);
  const [detailState, setDetailState] = useState<{
    period: string;
    item: CompetenceChecklistItemDetail;
  } | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const requestId = useRef(0);

  const [sheet, setSheet] = useState("");
  const [origin, setOrigin] = useState("");
  const [recipient, setRecipient] = useState("");
  const [branchScope, setBranchScope] = useState("");

  const [exceptionalOpen, setExceptionalOpen] = useState(false);
  const [exceptionalBusy, setExceptionalBusy] = useState(false);
  const [exceptionalError, setExceptionalError] = useState<string | null>(
    null,
  );
  const [exName, setExName] = useState("");
  const [exSheet, setExSheet] = useState<CompetenceSheet>("ELETRONICO");
  const [exApplicability, setExApplicability] = useState<
    "REQUIRED" | "CONDITIONAL" | "OPTIONAL"
  >("CONDITIONAL");
  const [exJustification, setExJustification] = useState("");

  const activePeriod = period ?? "";
  const periodValid = PERIOD_PATTERN.test(activePeriod);

  // Resultados keyed pela query vigente — sem reset dentro de effects.
  const itemsQueryKey = JSON.stringify({
    period: activePeriod,
    sheet,
    origin,
    recipient,
    branchScope,
    retryNonce,
  });
  const currentItems =
    periodValid && itemsResult?.key === itemsQueryKey ? itemsResult : null;
  const items = currentItems?.kind === "ready" ? currentItems.items : null;
  const notOpened = currentItems?.kind === "not_opened";
  const itemsError =
    currentItems?.kind === "error" ? currentItems.error : null;

  const listQueryKey = `list:${retryNonce}`;
  const currentList =
    competences?.key === listQueryKey ? competences.data : null;
  const error =
    listError?.key === listQueryKey ? listError.error : itemsError;
  const detail =
    detailState?.period === activePeriod ? detailState.item : null;
  const loading =
    periodValid && currentItems === null && !notOpened && !itemsError;

  const navigateToPeriod = useCallback((value: string) => {
    if (!PERIOD_PATTERN.test(value)) return;
    navigatePluginPath(`${buildPluginPath("checklist")}/${value}`);
  }, []);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  const clearFilters = useCallback(() => {
    setSheet("");
    setOrigin("");
    setRecipient("");
    setBranchScope("");
    setSelectedPeriod(currentCompetence());
  }, []);

  // Sem período na rota: lista competências abertas.
  useEffect(() => {
    if (period) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    listCompetences({ signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setCompetences({ key: listQueryKey, data });
        setLastUpdated(new Date());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setListError({
          key: listQueryKey,
          error: toQueryError(err, "Falha ao listar competências."),
        });
      });
    return () => controller.abort();
  }, [period, listQueryKey]);

  // Com período: itens do snapshot da competência.
  useEffect(() => {
    if (!period || !periodValid) return;
    const id = ++requestId.current;
    const controller = new AbortController();

    listCompetenceItems(
      period,
      {
        sheet: (sheet || undefined) as CompetenceSheet | undefined,
        originKind: (origin || undefined) as CompetenceItemOrigin | undefined,
        recipientArea: (recipient || undefined) as
          | CompetenceItemRecipient
          | undefined,
        branchScope: (branchScope || undefined) as
          | CompetenceItemBranchScope
          | undefined,
      },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setItemsResult({ key: itemsQueryKey, kind: "ready", items: data });
        setLastUpdated(new Date());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        const mapped = toQueryError(
          err,
          "Falha ao consultar o checklist da competência.",
        );
        if (mapped.code === "competence_not_opened") {
          setItemsResult({ key: itemsQueryKey, kind: "not_opened" });
        } else {
          setItemsResult({ key: itemsQueryKey, kind: "error", error: mapped });
        }
      });
    return () => controller.abort();
  }, [period, periodValid, sheet, origin, recipient, branchScope, itemsQueryKey]);

  const openCurrentPeriod = useCallback(() => {
    if (!periodValid) return;
    setOpening(true);
    openCompetence(activePeriod)
      .then(() => {
        setOpening(false);
        retry();
      })
      .catch((err: unknown) => {
        setOpening(false);
        setItemsResult({
          key: itemsQueryKey,
          kind: "error",
          error: toQueryError(err, "Falha ao abrir a competência."),
        });
      });
  }, [activePeriod, periodValid, retry, itemsQueryKey]);

  const openDetail = useCallback(
    (itemKey: string) => {
      getCompetenceItem(activePeriod, itemKey)
        .then((item) => setDetailState({ period: activePeriod, item }))
        .catch(() => setDetailState(null));
    },
    [activePeriod],
  );

  const refreshAfterItemChange = useCallback(() => {
    retry();
    if (detail) openDetail(detail.item_key);
  }, [retry, detail, openDetail]);

  const submitExceptional = useCallback(() => {
    if (!exName.trim() || !exJustification.trim()) return;
    setExceptionalBusy(true);
    setExceptionalError(null);
    createExceptionalItem(activePeriod, {
      sheet: exSheet,
      name: exName.trim(),
      justification: exJustification.trim(),
      applicability: exApplicability,
    })
      .then(() => {
        setExceptionalBusy(false);
        setExceptionalOpen(false);
        setExName("");
        setExJustification("");
        retry();
      })
      .catch((err: unknown) => {
        setExceptionalBusy(false);
        setExceptionalError(
          err instanceof ApiError
            ? err.message
            : "Falha ao registrar o item excepcional.",
        );
      });
  }, [activePeriod, exName, exSheet, exApplicability, exJustification, retry]);

  const columns = useMemo<DataTableColumn<CompetenceChecklistItem>[]>(
    () => [
      {
        key: "item_key",
        header: "Item",
        className: "cf-table__col--compact",
        render: (row) => (
          <span className="cf-cell-primary">{row.item_key}</span>
        ),
      },
      {
        key: "name",
        header: "Entregável esperado",
        className: "cf-table__col--wrap",
        render: (row) => <span title={row.name}>{row.name}</span>,
      },
      {
        key: "sheet",
        header: "Folha",
        className: "cf-table__col--compact",
        render: (row) =>
          row.sheet === "FISICO" ? "Físico" : "Eletrônico",
      },
      {
        key: "origin_kind",
        header: "Origem",
        className: "cf-table__col--status",
        render: (row) => (
          <CfStatusBadge
            label={ORIGIN_LABELS[row.origin_kind] ?? row.origin_kind}
            variant={row.origin_kind === "TOTVS" ? "info" : "neutral"}
          />
        ),
      },
      {
        key: "recipient_area",
        header: "Destinatário",
        className: "cf-table__col--compact",
        render: (row) =>
          row.recipient_area ? (
            (RECIPIENT_LABELS[row.recipient_area] ?? row.recipient_area)
          ) : (
            <span className="cf-cell-muted">A definir</span>
          ),
      },
      {
        key: "branch_scope",
        header: "Escopo",
        className: "cf-table__col--compact",
        render: (row) => BRANCH_LABELS[row.branch_scope] ?? row.branch_scope,
      },
      {
        key: "totvs_report_ref",
        header: "Relatório",
        className: "cf-table__col--compact",
        render: (row) =>
          row.totvs_report_ref ? (
            row.totvs_report_ref
          ) : (
            <span className="cf-cell-muted">—</span>
          ),
      },
      {
        key: "state",
        header: "Estado",
        className: "cf-table__col--status",
        render: (row) => (
          <CfStatusBadge
            label={STATE_LABELS[row.state] ?? row.state}
            variant="neutral"
          />
        ),
      },
    ],
    [],
  );

  const heroMetrics = useMemo<ClosingHeroMetric[] | undefined>(() => {
    if (!items) {
      return loading
        ? [
            {
              id: "competence",
              label: "Competência",
              value: activePeriod,
              icon: <CalendarDays size={20} aria-hidden />,
            },
            {
              id: "items",
              label: "Itens esperados",
              value: "",
              icon: <ListChecks size={20} aria-hidden />,
            },
          ]
        : undefined;
    }
    return [
      {
        id: "competence",
        label: "Competência",
        value: activePeriod,
        hint: "snapshot próprio do mês",
        icon: <CalendarDays size={20} aria-hidden />,
      },
      {
        id: "items",
        label: "Itens esperados",
        value: String(items.length),
        hint: "estado inicial — sem entrega registrada",
        icon: <ListChecks size={20} aria-hidden />,
      },
      {
        id: "sheets",
        label: "Folhas",
        value: `${items.filter((i) => i.sheet === "ELETRONICO").length} eletr. · ${
          items.filter((i) => i.sheet === "FISICO").length
        } fís.`,
        icon: <Layers size={20} aria-hidden />,
      },
    ];
  }, [items, loading, activePeriod]);

  const competencePicker = (
    <form
      className="cf-settlements-filters"
      onSubmit={(event) => event.preventDefault()}
    >
      <FiltersRow>
        <FilterInputField
          id="cf-checklist-period"
          label="Competência"
          type="month"
          value={selectedPeriod}
          onChange={setSelectedPeriod}
        />
      </FiltersRow>
      <CfActionButton
        type="button"
        onClick={() => navigateToPeriod(selectedPeriod)}
        disabled={!PERIOD_PATTERN.test(selectedPeriod)}
      >
        Consultar competência
      </CfActionButton>
    </form>
  );

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Checklist da competência"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Checklist da competência"
            hint={CF_HELP.checklist.page}
          />
        }
        subtitle="Itens esperados do fechamento mensal, conforme a versão publicada do checklist."
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={loading}
        metrics={heroMetrics}
        notice={
          <CfFeedbackMessage intent="info" title="Itens esperados, não entregues">
            «Esperado» indica entrega prevista — não é documento recebido nem
            validado. Lacunas do checklist aparecem como pendências.
          </CfFeedbackMessage>
        }
        filters={period ? undefined : competencePicker}
        onClearFilters={clearFilters}
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="o checklist da competência"
            onRetry={retry}
          />
        ) : null}

        {!period && currentList && currentList.length > 0 ? (
          <CfSectionCard
            title="Competências abertas"
            hint={CF_HELP.checklist.competence}
          >
            <ul className="cf-competence-list">
              {currentList.map((competence) => (
                <li key={competence.competence_id}>
                  <button
                    type="button"
                    className="cf-competence-link"
                    onClick={() => navigateToPeriod(competence.period)}
                  >
                    <FolderOpen size={16} aria-hidden /> {competence.period}
                    {competence.item_count !== undefined
                      ? ` · ${competence.item_count} itens`
                      : ""}
                  </button>
                </li>
              ))}
            </ul>
          </CfSectionCard>
        ) : null}

        {!period && currentList && currentList.length === 0 ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhuma competência aberta. Informe um mês acima para abrir ou consultar."
          />
        ) : null}

        {period && !periodValid ? (
          <CfFeedbackMessage intent="error" title="Competência inválida">
            A competência da rota deve estar no formato AAAA-MM.
          </CfFeedbackMessage>
        ) : null}

        {period && periodValid && notOpened ? (
          <>
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage={`A competência ${activePeriod} ainda não foi aberta.`}
            />
            <CfFeedbackMessage intent="info" title="Abertura governada">
              A abertura copia os itens da versão publicada do checklist —
              nunca recria uma competência existente.
            </CfFeedbackMessage>
            <div className="cf-settlements-actions">
              <CfActionButton
                type="button"
                onClick={openCurrentPeriod}
                disabled={opening}
              >
                <ClipboardList size={16} aria-hidden />{" "}
                {opening ? "Abrindo…" : "Abrir competência"}
              </CfActionButton>
            </div>
          </>
        ) : null}

        {period && periodValid && items ? (
          <>
            <form
              className="cf-settlements-filters"
              onSubmit={(event) => event.preventDefault()}
            >
              <FiltersRow>
                <FilterSelectField
                  label="Folha"
                  value={sheet}
                  onChange={setSheet}
                  options={SHEET_OPTIONS}
                />
                <FilterSelectField
                  label="Origem"
                  value={origin}
                  onChange={setOrigin}
                  options={ORIGIN_OPTIONS}
                />
                <FilterSelectField
                  label="Destinatário"
                  value={recipient}
                  onChange={setRecipient}
                  options={RECIPIENT_OPTIONS}
                />
                <FilterSelectField
                  label="Escopo de filial"
                  value={branchScope}
                  onChange={setBranchScope}
                  options={BRANCH_OPTIONS}
                />
              </FiltersRow>
            </form>

            <div className="cf-settlements-actions">
              <CfActionButton
                type="button"
                title={CF_HELP.checklist.exceptionalItem}
                onClick={() => {
                  setExceptionalError(null);
                  setExceptionalOpen(true);
                }}
              >
                Adicionar item excepcional
              </CfActionButton>
            </div>

            <DataTableSection<CompetenceChecklistItem>
              title="Itens esperados"
              titleHint={CF_HELP.checklist.table}
              columns={columns}
              rows={items}
              rowKey={(row) => row.item_key}
              loading={loading}
              hideSearch
              emptyMessage="Nenhum item corresponde aos filtros aplicados."
              columnPreferencesKey="cf:closing:checklist:v1"
              fontSizePreferencesKey="cf:closing:checklist:font:v1"
              resizableColumns
              onRowClick={(row) => openDetail(row.item_key)}
            />

            <P3CutoffPanel period={activePeriod} />

            <ReportsMatrixPanel period={activePeriod} />

            {detail ? (
              <CfSectionCard
                title={`Detalhe — ${detail.item_key}`}
                hint={CF_HELP.checklist.detail}
              >
                <dl className="cf-detail-list">
                  <div>
                    <dt>Entregável</dt>
                    <dd>{detail.name}</dd>
                  </div>
                  <div>
                    <dt>Origem</dt>
                    <dd>
                      {ORIGIN_LABELS[detail.origin_kind] ?? detail.origin_kind}
                      {detail.totvs_report_ref
                        ? ` · ${detail.totvs_report_ref}`
                        : ""}
                    </dd>
                  </div>
                  <div>
                    <dt>Destinatário</dt>
                    <dd>
                      {detail.recipient_area
                        ? (RECIPIENT_LABELS[detail.recipient_area] ??
                          detail.recipient_area)
                        : "A definir"}
                    </dd>
                  </div>
                  <div>
                    <dt>Aplicabilidade</dt>
                    <dd>{detail.applicability}</dd>
                  </div>
                  <div>
                    <dt>Escopo de filial</dt>
                    <dd>
                      {BRANCH_LABELS[detail.branch_scope] ??
                        detail.branch_scope}
                    </dd>
                  </div>
                  <div>
                    <dt>Estado</dt>
                    <dd>
                      {STATE_LABELS[detail.state] ?? detail.state}
                      {detail.exceptional ? " · excepcional" : ""}
                    </dd>
                  </div>
                  <div>
                    <dt>Regra de validação</dt>
                    <dd>
                      {VALIDATION_SCOPE_LABELS[detail.validation_scope] ??
                        detail.validation_scope}
                    </dd>
                  </div>
                  {detail.requirement_notes ? (
                    <div>
                      <dt>Requisitos e notas</dt>
                      <dd>{detail.requirement_notes}</dd>
                    </div>
                  ) : null}
                  <div>
                    <dt>Versão do template</dt>
                    <dd>
                      {detail.source_version_id ??
                        "item excepcional desta competência"}
                    </dd>
                  </div>
                </dl>
                <CfSectionCard
                  title="Validação humana"
                  hint={CF_HELP.checklist.validation}
                >
                  <ItemValidationPanel
                    period={activePeriod}
                    item={detail}
                    onChanged={refreshAfterItemChange}
                  />
                </CfSectionCard>
                <CfSectionCard
                  title="Evidências do item"
                  hint={CF_HELP.checklist.itemDocuments}
                >
                  <ClosingDocumentsPanel
                    period={activePeriod}
                    snapshotItemId={detail.snapshot_item_id}
                  />
                </CfSectionCard>
              </CfSectionCard>
            ) : null}

            <CfSectionCard
              title="Evidências da competência"
              hint={CF_HELP.checklist.documents}
            >
              <ClosingDocumentsPanel period={activePeriod} />
            </CfSectionCard>
          </>
        ) : null}
      </div>

      {exceptionalOpen ? (
        <CfDialog
          open
          title="Adicionar item excepcional"
          onClose={() => !exceptionalBusy && setExceptionalOpen(false)}
          closeAriaLabel="Fechar item excepcional"
        >
          <div className="cf-validation-panel__form">
            <p className="cf-validation-panel__doc-detail">
              O item excepcional vale apenas para a competência{" "}
              {activePeriod} — o checklist mestre não é alterado.
            </p>
            {exceptionalError ? (
              <CfFeedbackMessage
                intent="error"
                title="Item excepcional não registrado"
              >
                {exceptionalError}
              </CfFeedbackMessage>
            ) : null}
            <label>
              Entregável
              <input
                value={exName}
                disabled={exceptionalBusy}
                onChange={(event) => setExName(event.target.value)}
              />
            </label>
            <label>
              Folha
              <select
                value={exSheet}
                disabled={exceptionalBusy}
                onChange={(event) =>
                  setExSheet(event.target.value as CompetenceSheet)
                }
              >
                <option value="ELETRONICO">Eletrônico</option>
                <option value="FISICO">Físico</option>
              </select>
            </label>
            <label>
              Aplicabilidade
              <select
                value={exApplicability}
                disabled={exceptionalBusy}
                onChange={(event) =>
                  setExApplicability(
                    event.target.value as
                      | "REQUIRED"
                      | "CONDITIONAL"
                      | "OPTIONAL",
                  )
                }
              >
                {APPLICABILITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Justificativa
              <textarea
                value={exJustification}
                disabled={exceptionalBusy}
                rows={3}
                onChange={(event) => setExJustification(event.target.value)}
              />
            </label>
            <div className="cf-validation-panel__form-actions">
              <CfActionButton
                type="button"
                disabled={
                  exceptionalBusy ||
                  !exName.trim() ||
                  !exJustification.trim()
                }
                onClick={submitExceptional}
              >
                {exceptionalBusy ? "Registrando…" : "Registrar item"}
              </CfActionButton>
              <CfActionButton
                type="button"
                variant="ghost"
                disabled={exceptionalBusy}
                onClick={() => setExceptionalOpen(false)}
              >
                Voltar
              </CfActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}
    </section>
  );
}
