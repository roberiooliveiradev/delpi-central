import { useEffect, useMemo, useState } from "react";

import {
  createEntryAuditAnalysis,
  getEntryAuditAnalysis,
  listEntryAuditAnalyses,
  listEntryAuditOptions,
  type EntryAuditAnalysis,
  type EntryAuditAnalysisListItem,
  type EntryAuditOptions,
} from "../../api/entryAuditApi";
import { ApiError } from "../../api/httpClient";
import {
  CfActionButton,
  CfDateField,
  CfEmptyState,
  CfLoadingCard,
  CfMultiSelectField,
  CfPageHero,
  CfPagePath,
  CfProgressTracker,
  CfSectionCard,
  CfStateBanner,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import {
  ENTRY_AUDIT_ACTION_ICONS,
  auditStatusBadgeVariant,
  formatAuditStatus,
  formatBranches,
  formatDocumentTypes,
  formatDateTimeShort,
  formatPeriodLabel,
  formatStage,
} from "./entryAuditPresentation";

type LoadState =
  | { kind: "loading" }
  | { kind: "forbidden" }
  | { kind: "error"; message: string }
  | {
      kind: "ready";
      options: EntryAuditOptions;
      analyses: EntryAuditAnalysisListItem[];
    };

const STAGE_ORDER = [
  "queued",
  "reading_protheus",
  "reading_xml",
  "auditing",
  "saving",
  "done",
] as const;

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function monthStart(): string {
  return `${today().slice(0, 8)}01`;
}

function stageState(
  current: string,
  target: string,
): "complete" | "current" | "available" | "locked" | "error" {
  if (current === "failed" && target === current) return "error";
  if (current === "partial" && target === "done") return "complete";
  const curIdx = STAGE_ORDER.indexOf(current as (typeof STAGE_ORDER)[number]);
  const tgtIdx = STAGE_ORDER.indexOf(target as (typeof STAGE_ORDER)[number]);
  if (curIdx < 0 || tgtIdx < 0) return "available";
  if (tgtIdx < curIdx) return "complete";
  if (tgtIdx === curIdx) return "current";
  return "locked";
}

export function EntryAuditHomePage({ basePath }: { basePath: string }) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [dateFrom, setDateFrom] = useState(monthStart);
  const [dateTo, setDateTo] = useState(today);
  const [branches, setBranches] = useState<string[]>([]);
  const [documentTypes, setDocumentTypes] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [activeAnalysis, setActiveAnalysis] =
    useState<EntryAuditAnalysis | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      listEntryAuditOptions(controller.signal),
      listEntryAuditAnalyses({ page_size: 50 }, controller.signal),
    ])
      .then(([options, analyses]) => {
        if (controller.signal.aborted) return;
        setState({ kind: "ready", options, analyses: analyses.items });
        setBranches(options.branches.map((option) => option.code));
        setDocumentTypes(
          options.document_types
            .filter((option) => option.default !== false)
            .map((option) => option.code),
        );
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof ApiError && error.status === 403) {
          setState({ kind: "forbidden" });
        } else {
          setState({
            kind: "error",
            message:
              error instanceof Error
                ? error.message
                : "Falha ao carregar auditorias.",
          });
        }
      });
    return () => controller.abort();
  }, []);

  const openAnalysis = (id: string) =>
    navigatePluginPath(
      `${basePath}/entry-audit/analyses/${encodeURIComponent(id)}`,
    );

  useEffect(() => {
    if (!activeAnalysis || !["queued", "running"].includes(activeAnalysis.status)) {
      return;
    }
    const analysisId = activeAnalysis.id;
    const timer = window.setInterval(() => {
      void getEntryAuditAnalysis(analysisId).then((analysis) => {
        setActiveAnalysis(analysis);
        if (!["queued", "running"].includes(analysis.status)) {
          navigatePluginPath(
            `${basePath}/entry-audit/analyses/${encodeURIComponent(analysis.id)}`,
          );
        }
      });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [activeAnalysis, basePath]);

  const create = async () => {
    if (!dateFrom || !dateTo || branches.length === 0 || documentTypes.length === 0) {
      setCreateError("Informe o período, ao menos uma filial e um tipo de documento.");
      return;
    }
    if (dateFrom > dateTo) {
      setCreateError("A data inicial deve ser menor ou igual à data final.");
      return;
    }
    setCreating(true);
    setCreateError("");
    try {
      const created = await createEntryAuditAnalysis({
        date_from: dateFrom,
        date_to: dateTo,
        branches,
        document_types: documentTypes,
        via: "user",
      });
      const analysis = await getEntryAuditAnalysis(created.id);
      setActiveAnalysis(analysis);
      if (!["queued", "running"].includes(analysis.status)) openAnalysis(analysis.id);
    } catch (error) {
      setCreateError(
        error instanceof Error ? error.message : "Não foi possível criar a análise.",
      );
    } finally {
      setCreating(false);
    }
  };

  const branchOptions = state.kind === "ready" ? state.options.branches : [];

  const columns: DataTableColumn<EntryAuditAnalysisListItem>[] = useMemo(
    () => [
      {
        key: "period",
        header: "Período",
        render: (row) => formatPeriodLabel(row.date_from, row.date_to),
      },
      {
        key: "branches",
        header: "Filiais",
        render: (row) => formatBranches(row.branches, branchOptions),
      },
      {
        key: "types",
        header: "Tipos",
        render: (row) => formatDocumentTypes(row.document_types),
      },
      {
        key: "status",
        header: "Situação",
        render: (row) => (
          <CfStatusBadge
            label={formatAuditStatus(row.status)}
            variant={auditStatusBadgeVariant(row.status)}
          />
        ),
      },
      {
        key: "created",
        header: "Criada em",
        render: (row) => formatDateTimeShort(row.created_at),
      },
      {
        key: "open",
        header: "Ação",
        render: () => (
          <span className="cf-action-with-icon">
            {ENTRY_AUDIT_ACTION_ICONS.open}
            Abrir
          </span>
        ),
      },
    ],
    [branchOptions],
  );

  if (state.kind === "loading") {
    return <CfLoadingCard title="Carregando auditoria de entradas…" />;
  }
  if (state.kind === "forbidden") {
    return (
      <CfStateBanner variant="default">
        Você não tem autorização para acessar a Auditoria de Entradas.
      </CfStateBanner>
    );
  }
  if (state.kind === "error") {
    return <CfStateBanner variant="error">{state.message}</CfStateBanner>;
  }

  return (
    <section className="cf-page-stack" aria-label="Auditoria de Entradas">
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        items={[
          {
            id: "home",
            label: "Início",
            href: basePath,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              navigatePluginPath(basePath);
            },
          },
          {
            id: "notas",
            label: "Notas fiscais",
            href: basePath,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              navigatePluginPath(basePath);
            },
          },
        ]}
        current="Auditoria de Entradas"
      />
      <CfPageHero
        eyebrow="Notas fiscais"
        title={
          <CfTitleWithHelp
            title="Auditoria de Entradas"
            hint={CF_HELP.entryAudit.page}
          />
        }
        description="Compare documentos do Protheus com os XML fiscais e trate ocorrências."
      />

      <CfSectionCard
        title="Nova análise"
        hint={CF_HELP.entryAudit.create}
        subtitle={CF_HELP.entryAudit.whatAudits}
      >
        <div className="cf-filters-grid">
          <CfDateField
            id="entry-audit-from"
            label="De"
            value={dateFrom}
            onChange={setDateFrom}
          />
          <CfDateField
            id="entry-audit-to"
            label="Até"
            value={dateTo}
            onChange={setDateTo}
          />
          <CfMultiSelectField
            id="entry-audit-branches"
            label="Filiais"
            options={state.options.branches.map((option) => ({
              value: option.code,
              label: option.name?.trim()
                ? option.name
                : `Filial ${option.code}`,
            }))}
            selectedValues={branches}
            onChange={setBranches}
            searchable
          />
          <CfMultiSelectField
            id="entry-audit-document-types"
            label="Tipos"
            options={state.options.document_types.map((option) => ({
              value: option.code,
              label: option.label ?? formatDocumentTypes([option.code]),
            }))}
            selectedValues={documentTypes}
            onChange={setDocumentTypes}
          />
        </div>
        {createError ? (
          <CfStateBanner variant="error">{createError}</CfStateBanner>
        ) : null}
        <div className="cf-filters-grid__actions">
          <CfActionButton
            type="button"
            variant="primary"
            onClick={create}
            disabled={creating}
            softDisabled
            title={CF_HELP.entryAudit.create}
          >
            <span className="cf-action-with-icon">
              {ENTRY_AUDIT_ACTION_ICONS.play}
              {creating ? "Executando…" : "Executar auditoria"}
            </span>
          </CfActionButton>
        </div>
      </CfSectionCard>

      {activeAnalysis ? (
        <CfSectionCard title="Processamento da análise">
          {activeAnalysis.runs.map((run) => {
            const expected = run.counts.xml_expected;
            const read = run.counts.xml_read ?? run.xml_downloaded;
            const currentStage =
              run.stage === "failed" || run.stage === "partial"
                ? run.stage
                : run.stage;
            const steps = STAGE_ORDER.map((stage) => ({
              id: stage,
              label: formatStage(stage),
              state: stageState(
                currentStage === "failed" ? "failed" : currentStage,
                stage,
              ),
            }));
            const counters =
              typeof read === "number"
                ? `XML lidos: ${read}${typeof expected === "number" ? ` de ${expected}` : ""}`
                : formatStage(run.stage);
            return (
              <article key={run.branch} className="cf-page-stack">
                <strong>
                  {formatBranches([run.branch], state.options.branches)}
                </strong>
                <CfProgressTracker
                  steps={steps}
                  currentStepId={
                    STAGE_ORDER.includes(
                      run.stage as (typeof STAGE_ORDER)[number],
                    )
                      ? run.stage
                      : "queued"
                  }
                  density="compact"
                  compactSummary={counters}
                  ariaLabel={`Andamento da filial ${run.branch}`}
                />
                {run.error ? <p role="alert">{run.error}</p> : null}
              </article>
            );
          })}
          {!["queued", "running"].includes(activeAnalysis.status) ? (
            <CfActionButton onClick={() => openAnalysis(activeAnalysis.id)}>
              <span className="cf-action-with-icon">
                {ENTRY_AUDIT_ACTION_ICONS.open}
                Abrir resultado
              </span>
            </CfActionButton>
          ) : null}
        </CfSectionCard>
      ) : null}

      {state.analyses.length ? (
        <DataTableSection
          title="Análises anteriores"
          titleHint={CF_HELP.entryAudit.history}
          columns={columns}
          rows={state.analyses}
          rowKey={(row) => row.id}
          hideSearch
          onRowClick={(row) => openAnalysis(row.id)}
        />
      ) : (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Nenhuma análise anterior. Defina o escopo e execute a primeira."
        />
      )}
    </section>
  );
}
