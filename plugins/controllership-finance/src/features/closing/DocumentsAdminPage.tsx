/**
 * «Documentos do fechamento» — catálogo mestre administrativo (UX-012).
 *
 * Listagem derivada da timeline de versões publicadas do checklist mestre:
 * cada `item_key` vira uma linha com janelas de vigência calculadas a
 * partir de `effective_from_period` — nenhuma persistência paralela.
 * Cadastro/edição acontecem em páginas completas (`DocumentConfigFormPage`),
 * nunca em modal. Filtros vivem na URL (mesmo padrão RW01): F5, deep link
 * e voltar/avançar restauram o contexto.
 *
 * Autorização: a BFF exige `controllership-finance.manage` em todos os
 * endpoints — a página apenas renderiza o resultado (403 → banner honesto).
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { FilePlus2 } from "lucide-react";

import { ApiError } from "../../api/httpClient";
import {
  getTemplateVersion,
  listChecklistTemplates,
  listTemplateVersions,
  type ChecklistTemplate,
} from "../../api/adminApi";
import {
  FiltersRow,
  FilterInputField,
  FilterSelectField,
} from "../../app/cfFiltersUi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
  type CfQueryError,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfEmptyState,
  CfPagePath,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import {
  APPLICABILITY_LABELS,
  RECIPIENT_LABELS,
  SITUATION_LABELS,
  deriveDocumentCatalog,
  formatPeriod,
  type DocumentCatalogRow,
  type DocumentSituation,
  type VersionWithItems,
} from "./documentCatalog";
import { useReportQuerySync } from "./reportQueryParams";
import { DocumentConfigFormPage } from "./DocumentConfigFormPage";
import { ERROR_MESSAGES } from "./checklistAdminShared";

const LIST_PATH = "closing/admin/documents";

type ListFilters = {
  q: string;
  status: "" | DocumentSituation;
  dest: "" | "CONTABIL" | "FISCAL" | "INTERNAL";
};

function parseListFilters(params: URLSearchParams): ListFilters {
  const rawStatus = params.get("status");
  const rawDest = params.get("dest");
  return {
    q: params.get("q") ?? "",
    status:
      rawStatus === "vigente" ||
      rawStatus === "futuro" ||
      rawStatus === "encerrado"
        ? rawStatus
        : "",
    dest:
      rawDest === "CONTABIL" ||
      rawDest === "FISCAL" ||
      rawDest === "INTERNAL"
        ? rawDest
        : "",
  };
}

function serializeListFilters(filters: ListFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.status) params.set("status", filters.status);
  if (filters.dest) params.set("dest", filters.dest);
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function toQueryError(
  error: unknown,
  fallback: string,
): CfQueryError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code,
      message:
        (error.code && ERROR_MESSAGES[error.code]) || error.message,
    };
  }
  return { status: 0, code: null, message: fallback };
}

const SITUATION_VARIANTS: Record<
  DocumentSituation,
  "success" | "info" | "neutral"
> = {
  vigente: "success",
  futuro: "info",
  encerrado: "neutral",
};

export function documentsAdminListPath(
  base: string,
  search = "",
): string {
  return `${base}/${LIST_PATH}${search}`;
}

export function DocumentsAdminPage({
  basePath,
  itemKey,
}: {
  basePath: string;
  itemKey?: string;
}) {
  const [template, setTemplate] =
    useState<ChecklistTemplate | null>(null);
  const [versions, setVersions] =
    useState<VersionWithItems[] | null>(null);
  const [error, setError] = useState<CfQueryError | null>(null);
  const [savedKey] = useState(
    () =>
      new URLSearchParams(
        typeof window === "undefined"
          ? ""
          : window.location.search,
      ).get("saved"),
  );
  const [filters, setFilters] = useState<ListFilters>(() =>
    parseListFilters(
      new URLSearchParams(
        typeof window === "undefined" ? "" : window.location.search,
      ),
    ),
  );

  const hydrate = useCallback((params: URLSearchParams) => {
    setFilters(parseListFilters(params));
  }, []);

  useReportQuerySync({
    enabled: itemKey === undefined,
    serialize: () => serializeListFilters(filters),
    hydrate,
  });

  const loading = versions === null && !error;
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    listChecklistTemplates({ signal: controller.signal })
      .then(async (templates) => {
        const first = templates[0] ?? null;
        if (!first) {
          if (!controller.signal.aborted) {
            setTemplate(null);
            setVersions([]);
          }
          return;
        }
        const versionList = await listTemplateVersions(
          first.template_id,
          { signal: controller.signal },
        );
        const details = await Promise.all(
          versionList.map((version) =>
            getTemplateVersion(
              first.template_id,
              version.version,
              { signal: controller.signal },
            ),
          ),
        );
        if (!controller.signal.aborted) {
          setTemplate(first);
          setVersions(details);
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          toQueryError(
            err,
            "Não foi possível carregar o catálogo de documentos.",
          ),
        );
      });
    return () => controller.abort();
  }, [nonce]);

  const reload = useCallback(() => {
    setError(null);
    setVersions(null);
    setNonce((n) => n + 1);
  }, []);

  const rows = useMemo(
    () => deriveDocumentCatalog(versions ?? []),
    [versions],
  );

  const filteredRows = useMemo(() => {
    const needle = filters.q.trim().toLocaleLowerCase("pt-BR");
    return rows.filter((row) => {
      if (
        needle &&
        !row.name.toLocaleLowerCase("pt-BR").includes(needle) &&
        !(row.purpose ?? "")
          .toLocaleLowerCase("pt-BR")
          .includes(needle)
      ) {
        return false;
      }
      if (filters.status && row.situation !== filters.status) {
        return false;
      }
      if (filters.dest === "INTERNAL") {
        return row.recipientArea === null;
      }
      if (filters.dest) {
        return row.recipientArea === filters.dest;
      }
      return true;
    });
  }, [rows, filters]);

  const openDocument = useCallback(
    (key: string) => {
      navigatePluginPath(
        `${basePath}/${LIST_PATH}/${encodeURIComponent(key)}${window.location.search}`,
      );
    },
    [basePath],
  );

  const columns = useMemo<DataTableColumn<DocumentCatalogRow>[]>(
    () => [
      {
        key: "document",
        header: "Documento",
        render: (row) => (
          <div>
            <p className="cf-validation-panel__doc-name">{row.name}</p>
            {row.purpose ? (
              <p className="cf-validation-panel__doc-detail">
                {row.purpose}
              </p>
            ) : null}
          </div>
        ),
      },
      {
        key: "applicability",
        header: "Exigência",
        className: "cf-table__col--compact",
        render: (row) =>
          APPLICABILITY_LABELS[row.applicability] ?? row.applicability,
      },
      {
        key: "recipient",
        header: "Destino",
        className: "cf-table__col--compact",
        render: (row) =>
          row.recipientArea
            ? (RECIPIENT_LABELS[row.recipientArea] ?? row.recipientArea)
            : "Uso interno",
      },
      {
        key: "from",
        header: "Vigência inicial",
        className: "cf-table__col--compact",
        render: (row) => formatPeriod(row.vigenciaInicial),
      },
      {
        key: "to",
        header: "Vigência final",
        className: "cf-table__col--compact",
        render: (row) =>
          row.vigenciaFinal ? formatPeriod(row.vigenciaFinal) : "Sem término",
      },
      {
        key: "situation",
        header: "Situação",
        className: "cf-table__col--status",
        render: (row) => (
          <CfStatusBadge
            variant={SITUATION_VARIANTS[row.situation]}
            label={SITUATION_LABELS[row.situation]}
          />
        ),
      },
      {
        key: "actions",
        header: "Ações",
        className: "cf-table__col--status",
        render: (row) => (
          <CfActionButton
            variant="ghost"
            onClick={() => openDocument(row.itemKey)}
          >
            Editar
          </CfActionButton>
        ),
      },
    ],
    [openDocument],
  );

  if (itemKey !== undefined) {
    return (
      <DocumentConfigFormPage basePath={basePath} itemKey={itemKey} />
    );
  }

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Documentos do fechamento"
    >
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={{
          label: "Início",
          href: basePath,
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            navigatePluginPath(basePath);
          },
        }}
        items={[
          {
            id: "admin",
            label: "Administração",
            href: `${basePath}/closing/admin`,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              navigatePluginPath(`${basePath}/closing/admin`);
            },
          },
        ]}
        current="Documentos do fechamento"
      />

      <div className="cf-checklist-page__content">
        <div className="cf-lead-stack">
          <CfTitleWithHelp
            title="Documentos do fechamento"
            hint={CF_HELP.documentsAdmin.page}
          />
          <p className="cf-validation-panel__doc-detail">
            Configure quais documentos serão exigidos em cada período e
            quais deverão ser enviados à Contabilidade.
          </p>
        </div>

        {savedKey ? (
          <CfFeedbackMessage
            intent="success"
            title="Documento salvo"
          >
            A configuração foi publicada com vigência prospectiva —
            competências já abertas não foram alteradas.
          </CfFeedbackMessage>
        ) : null}

        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="o catálogo de documentos"
            onRetry={() => reload()}
          />
        ) : loading ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Carregando catálogo de documentos…"
          />
        ) : (
          <>
            <div className="cf-validation-panel__item-actions">
              <CfActionButton
                type="button"
                variant="primary"
                onClick={() => openDocument("new")}
              >
                <FilePlus2
                  size={15}
                  strokeWidth={1.9}
                  aria-hidden="true"
                />
                Adicionar documento
              </CfActionButton>
              <CfActionButton
                type="button"
                variant="ghost"
                onClick={() =>
                  navigatePluginPath(`${basePath}/closing/admin`)
                }
              >
                Versões e auditoria
              </CfActionButton>
            </div>

            <form
              className="cf-settlements-filters"
              onSubmit={(event) => event.preventDefault()}
            >
              <FiltersRow>
                <FilterInputField
                  id="cf-documents-search"
                  label="Pesquisar por nome"
                  type="text"
                  value={filters.q}
                  onChange={(value) =>
                    setFilters({ ...filters, q: value })
                  }
                />
                <FilterSelectField
                  id="cf-documents-status"
                  label="Situação"
                  value={filters.status}
                  options={[
                    { value: "", label: "Todas" },
                    { value: "vigente", label: "Vigente" },
                    { value: "futuro", label: "Futuro" },
                    { value: "encerrado", label: "Encerrado" },
                  ]}
                  onChange={(value) =>
                    setFilters({
                      ...filters,
                      status: value as ListFilters["status"],
                    })
                  }
                />
                <FilterSelectField
                  id="cf-documents-dest"
                  label="Destino"
                  value={filters.dest}
                  options={[
                    { value: "", label: "Todos" },
                    { value: "CONTABIL", label: "Contabilidade" },
                    { value: "FISCAL", label: "Fiscal" },
                    { value: "INTERNAL", label: "Uso interno" },
                  ]}
                  onChange={(value) =>
                    setFilters({
                      ...filters,
                      dest: value as ListFilters["dest"],
                    })
                  }
                />
              </FiltersRow>
            </form>

            {template === null ? (
              <CfEmptyState
                classNames={cfEmptyStateClassNames}
                defaultMessage="Nenhum template de checklist registrado — a administração do checklist ainda não foi inicializada."
              />
            ) : (
              <DataTableSection<DocumentCatalogRow>
                title="Tipos de documento"
                titleHint={CF_HELP.documentsAdmin.list}
                columns={columns}
                rows={filteredRows}
                rowKey={(row) => row.itemKey}
                loading={false}
                emptyMessage="Nenhum documento encontrado. Ajuste os filtros ou cadastre o primeiro documento."
              />
            )}
          </>
        )}
      </div>
    </section>
  );
}
