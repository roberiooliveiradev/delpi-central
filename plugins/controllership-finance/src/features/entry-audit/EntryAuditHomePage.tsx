import { useEffect, useState } from "react";

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
  CfSectionCard,
  CfStateBanner,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import { formatAuditStatus, formatStage } from "./entryAuditPresentation";

type LoadState =
  | { kind: "loading" }
  | { kind: "forbidden" }
  | { kind: "error"; message: string }
  | {
      kind: "ready";
      options: EntryAuditOptions;
      analyses: EntryAuditAnalysisListItem[];
    };

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function monthStart(): string {
  return `${today().slice(0, 8)}01`;
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

  useEffect(() => {
    if (!activeAnalysis || !["queued", "running"].includes(activeAnalysis.status)) {
      return;
    }
    const timer = window.setInterval(() => {
      void getEntryAuditAnalysis(activeAnalysis.id).then(setActiveAnalysis);
    }, 3000);
    return () => window.clearInterval(timer);
  }, [activeAnalysis]);

  const openAnalysis = (id: string) =>
    navigatePluginPath(
      `${basePath}/entry-audit/analyses/${encodeURIComponent(id)}`,
    );

  const create = async () => {
    if (!dateFrom || !dateTo || branches.length === 0 || documentTypes.length === 0) {
      setCreateError("Informe o período, ao menos uma filial e um tipo de documento.");
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

  const columns: DataTableColumn<EntryAuditAnalysisListItem>[] = [
    {
      key: "period",
      header: "Período",
      render: (row) =>
        `${new Date(`${row.date_from}T12:00:00`).toLocaleDateString("pt-BR")} a ${new Date(`${row.date_to}T12:00:00`).toLocaleDateString("pt-BR")}`,
    },
    { key: "branches", header: "Filiais", render: (row) => row.branches.join(", ") },
    {
      key: "types",
      header: "Documentos",
      render: (row) => row.document_types.join(", ").toUpperCase(),
    },
    {
      key: "status",
      header: "Situação",
      render: (row) => formatAuditStatus(row.status),
    },
    {
      key: "created",
      header: "Criada em",
      render: (row) => new Date(row.created_at).toLocaleString("pt-BR"),
    },
  ];

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
      <CfPageHero
        eyebrow="Fiscal"
        title={
          <CfTitleWithHelp
            title="Auditoria de Entradas"
            hint={CF_HELP.entryAudit.page}
          />
        }
        description="Compare documentos do Protheus com os XML fiscais e trate ocorrências."
      />

      <CfSectionCard title="Nova análise" hint={CF_HELP.entryAudit.create}>
        <div className="cf-filters-grid">
          <CfDateField
            id="entry-audit-from"
            label="Data inicial"
            value={dateFrom}
            onChange={setDateFrom}
          />
          <CfDateField
            id="entry-audit-to"
            label="Data final"
            value={dateTo}
            onChange={setDateTo}
          />
          <CfMultiSelectField
            id="entry-audit-branches"
            label="Filiais"
            options={state.options.branches.map((option) => ({
              value: option.code,
              label: `${option.code}${option.name ? ` — ${option.name}` : ""}`,
            }))}
            selectedValues={branches}
            onChange={setBranches}
            searchable
          />
          <CfMultiSelectField
            id="entry-audit-document-types"
            label="Tipos de documento"
            options={state.options.document_types.map((option) => ({
              value: option.code,
              label: option.label ?? option.code.toUpperCase(),
            }))}
            selectedValues={documentTypes}
            onChange={setDocumentTypes}
          />
        </div>
        {createError ? (
          <CfStateBanner variant="error">{createError}</CfStateBanner>
        ) : null}
        <CfActionButton type="button" onClick={create} disabled={creating} softDisabled>
          {creating ? "Criando análise…" : "Criar análise"}
        </CfActionButton>
      </CfSectionCard>

      {activeAnalysis ? (
        <CfSectionCard title="Processamento da análise">
          {activeAnalysis.runs.map((run) => {
            const expected = run.counts.xml_expected;
            const read = run.counts.xml_read ?? run.xml_downloaded;
            return (
              <article key={run.branch}>
                <strong>Filial {run.branch}</strong>
                <p>{formatStage(run.stage)}</p>
                {typeof read === "number" ? (
                  <p>
                    XML lidos: {read}
                    {typeof expected === "number" ? ` de ${expected}` : ""}
                  </p>
                ) : null}
                {run.error ? <p role="alert">{run.error}</p> : null}
              </article>
            );
          })}
          {!["queued", "running"].includes(activeAnalysis.status) ? (
            <CfActionButton onClick={() => openAnalysis(activeAnalysis.id)}>
              Abrir resultado
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
          defaultMessage="Nenhuma análise anterior. Defina o escopo e crie a primeira."
        />
      )}
    </section>
  );
}
