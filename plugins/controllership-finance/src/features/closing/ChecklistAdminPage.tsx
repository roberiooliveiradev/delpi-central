/**
 * Administração do checklist mestre — P6 (A3), nível 1 da navegação
 * em cascata (UX-015): lista as versões do template; o detalhe de
 * itens, a edição de rascunho e o histórico vivem em páginas
 * contextuais próprias (`closing/admin/versions/{n}` e
 * `closing/admin/events`), não mais em expansão/modal nesta página.
 *
 * Consome `/admin/checklist-templates*` da BFF (MANAGE efetivo — o
 * backend é a única autoridade; a página apenas renderiza e encaminha).
 * Versionamento prospectivo: publicar cria vigência futura e nunca
 * altera competências já abertas; inativar preserva histórico.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  FilePlus2,
  FileText,
  History,
} from "lucide-react";

import {
  createTemplateDraft,
  listChecklistTemplates,
  listTemplateVersions,
  type ChecklistTemplate,
  type ChecklistTemplateVersion,
} from "../../api/adminApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
  CfSectionLoading,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfDataRecordCard,
  CfEmptyState,
  CfPageHero,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
  type DataRecordCardField,
} from "../../app/controllershipFinanceUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import {
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import {
  checklistAdminEventsPath,
  checklistAdminVersionPath,
} from "../../app/pluginRoutes";
import {
  STATUS_LABELS,
  STATUS_VARIANTS,
  hintedLabel,
  toQueryError,
  useChecklistVersionActions,
  type QueryError,
} from "./checklistAdminShared";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

const ICON_PROPS = { size: 15, strokeWidth: 1.9, "aria-hidden": true } as const;

const VIEW_LAYOUT_KEY = "cf-checklist-admin-versions";
const COLUMN_PREFS_KEY = "cf-checklist-admin-versions-columns";

function versionSortLabel(
  row: ChecklistTemplateVersion,
): string | number {
  return STATUS_LABELS[row.status] ?? row.status;
}

export function ChecklistAdminPage({ basePath }: { basePath: string }) {
  const [nonce, setNonce] = useState(0);
  const [templates, setTemplates] = useState<{
    key: number;
    items: ChecklistTemplate[];
  } | null>(null);
  const [versions, setVersions] = useState<{
    key: string;
    items: ChecklistTemplateVersion[];
  } | null>(null);
  const [error, setError] = useState<QueryError | null>(null);

  const requestId = useRef(0);
  const template = templates?.items[0] ?? null;
  const versionsKey = template ? `${template.template_id}:${nonce}` : "";
  const currentVersions =
    versions?.key === versionsKey ? versions.items : null;
  const loading = templates === null && !error;

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  const actions = useChecklistVersionActions({
    templateId: template?.template_id ?? null,
    onDone: reload,
  });

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listChecklistTemplates({ signal: controller.signal })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setTemplates({ key: nonce, items });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError(
          toQueryError(err, "Falha ao listar templates de checklist."),
        );
      });
    return () => controller.abort();
  }, [nonce]);

  useEffect(() => {
    if (!template) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    listTemplateVersions(template.template_id, {
      signal: controller.signal,
    })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setVersions({ key: versionsKey, items });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError(toQueryError(err, "Falha ao listar as versões."));
      });
    return () => controller.abort();
  }, [template, versionsKey]);

  const openVersion = useCallback(
    (version: number) => {
      navigatePluginPath(checklistAdminVersionPath(version, basePath));
    },
    [basePath],
  );

  const versionColumns = useMemo<
    DataTableColumn<ChecklistTemplateVersion>[]
  >(
    () => [
      {
        key: "version",
        header: "Versão",
        headerHint: CF_HELP.admin.columns.version,
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) => row.version,
        render: (row) => `v${row.version}`,
      },
      {
        key: "status",
        header: "Estado",
        headerHint: CF_HELP.admin.columns.status,
        className: "cf-table__col--status",
        sortable: true,
        sortValue: versionSortLabel,
        render: (row) => (
          <CfStatusBadge
            label={STATUS_LABELS[row.status] ?? row.status}
            variant={STATUS_VARIANTS[row.status] ?? "neutral"}
          />
        ),
      },
      {
        key: "items",
        header: "Itens",
        headerHint: CF_HELP.admin.columns.items,
        className: "cf-table__col--compact",
        align: "right",
        sortable: true,
        sortValue: (row) => row.item_count,
        render: (row) => row.item_count,
      },
      {
        key: "effective",
        header: "Vigente desde",
        headerHint: CF_HELP.admin.columns.effective,
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) => row.effective_from_period ?? "",
        render: (row) =>
          row.effective_from_period ?? (
            <span className="cf-cell-muted">—</span>
          ),
      },
      {
        key: "published",
        header: "Publicação",
        headerHint: CF_HELP.admin.columns.published,
        className: "cf-table__col--wrap",
        sortable: true,
        sortValue: (row) => row.published_at ?? "",
        render: (row) =>
          row.published_at ? (
            `${formatDateTime(row.published_at)}`
          ) : (
            <span className="cf-cell-muted">—</span>
          ),
      },
    ],
    [],
  );

  const renderVersionCard = useCallback(
    (row: ChecklistTemplateVersion) => {
      const href = checklistAdminVersionPath(row.version, basePath);
      const fields: DataRecordCardField[] = [
        { id: "items", label: "Itens", value: String(row.item_count) },
        {
          id: "effective",
          label: "Vigente desde",
          value: row.effective_from_period ?? "—",
        },
        {
          id: "published",
          label: "Publicação",
          value: row.published_at
            ? formatDateTime(row.published_at)
            : "—",
        },
      ];
      return (
        <CfDataRecordCard
          href={href}
          onNavigate={(event) => {
            event.preventDefault();
            navigatePluginPath(href);
          }}
          title={`Versão ${row.version}`}
          subtitle={STATUS_LABELS[row.status] ?? row.status}
          status={
            <CfStatusBadge
              label={STATUS_LABELS[row.status] ?? row.status}
              variant={STATUS_VARIANTS[row.status] ?? "neutral"}
            />
          }
          fields={fields}
          ariaLabel={`Abrir versão ${row.version}`}
        />
      );
    },
    [basePath],
  );

  const draftOpen = (currentVersions ?? []).some(
    (v) => v.status === "DRAFT" || v.status === "REVIEW",
  );

  const latestVersion = useMemo(() => {
    if (!currentVersions?.length) return null;
    return currentVersions.reduce((latest, row) =>
      row.version > latest.version ? row : latest,
    );
  }, [currentVersions]);

  // Host da toolbar da listagem — renderizada no hero via portal do
  // DataTableSection (mesma instância/estado; `toolbarPortalTarget`).
  const [toolbarHost, setToolbarHost] =
    useState<HTMLElement | null>(null);

  return (
    <section
      className="cf-checklist-page cf-hero-page"
      aria-label="Administração do checklist"
    >
      <div className="cf-hero-page__content">
        <CfPageHero
          aria-label="Administração do checklist"
          eyebrow="Administração"
          title={
            <CfTitleWithHelp
              title={
                template?.name ?? "Checklist de Fechamento Mensal"
              }
              hint={CF_HELP.admin.page}
            />
          }
          description="Gerencie as versões e configurações documentais do fechamento."
          highlights={[
            {
              id: "versions",
              label: hintedLabel(
                "Versões",
                CF_HELP.admin.metrics.versions,
              ),
              value: String(currentVersions?.length ?? 0),
              loading: loading || (template !== null && currentVersions === null),
            },
            {
              id: "latest",
              label: hintedLabel(
                "Última versão",
                CF_HELP.admin.metrics.latest,
              ),
              value: latestVersion
                ? `v${latestVersion.version}`
                : "—",
              description: latestVersion
                ? (STATUS_LABELS[latestVersion.status] ??
                  latestVersion.status)
                : undefined,
            },
            {
              id: "effective",
              label: hintedLabel(
                "Vigente desde",
                CF_HELP.admin.metrics.effective,
              ),
              value: latestVersion?.effective_from_period ?? "—",
            },
          ]}
          actions={
            <div className="cf-validation-panel__item-actions">
              <CfActionButton
                type="button"
                variant="primary"
                disabled={
                  actions.busy || !template || draftOpen
                }
                title={
                  draftOpen
                    ? "Já existe um rascunho aberto — edite-o ou publique-o antes."
                    : undefined
                }
                onClick={() => {
                  if (!template) return;
                  actions.run(() =>
                    createTemplateDraft(template.template_id),
                  );
                }}
              >
                <FilePlus2 {...ICON_PROPS} />
                Nova versão
              </CfActionButton>
              <CfActionButton
                type="button"
                variant="ghost"
                onClick={() =>
                  navigatePluginPath(
                    checklistAdminEventsPath(undefined, basePath),
                  )
                }
              >
                <History {...ICON_PROPS} />
                Auditoria
              </CfActionButton>
              <CfActionButton
                type="button"
                variant="ghost"
                onClick={() => navigatePluginView("documents_admin")}
              >
                <FileText {...ICON_PROPS} />
                Documentos
              </CfActionButton>
            </div>
          }
        >
          <div
            ref={setToolbarHost}
            className="cf-hero-toolbar"
            data-testid="admin-listing-toolbar"
          />
        </CfPageHero>

        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="os templates de checklist"
            onRetry={reload}
          />
        ) : null}
        {actions.actionError ? (
          <CfFeedbackMessage intent="error" title="Ação não concluída">
            {actions.actionError.message}
          </CfFeedbackMessage>
        ) : null}

        {loading ? (
          <CfSectionLoading label="Carregando administração…" variant="compact" />
        ) : !error && !template ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum template de checklist registrado."
          />
        ) : template ? (
          <div className="cf-flex-listing">
            <DataTableSection<ChecklistTemplateVersion>
              title="Versões"
              titleHint={CF_HELP.admin.versions}
              columns={versionColumns}
              rows={currentVersions ?? []}
              rowKey={(row) => String(row.version)}
              loading={currentVersions === null}
              emptyMessage="Nenhuma versão registrada para este checklist."
              columnPreferencesKey={COLUMN_PREFS_KEY}
              viewLayoutPreferencesKey={VIEW_LAYOUT_KEY}
              renderCard={renderVersionCard}
              onRowClick={(row) => openVersion(row.version)}
              getSearchText={(row) =>
                `v${row.version} ${STATUS_LABELS[row.status] ?? row.status} ${row.effective_from_period ?? ""}`
              }
              toolbarPortalTarget={toolbarHost}
              tableLayout="scroll"
              searchHint={CF_HELP.admin.search}
            />
          </div>
        ) : null}
      </div>

      {actions.dialogs}
    </section>
  );
}
