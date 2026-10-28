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

import { ActionButton } from "@delpi/plugin-ui/index";

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
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
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
  toQueryError,
  useChecklistVersionActions,
  VersionStatusActions,
  type QueryError,
} from "./checklistAdminShared";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

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
        className: "cf-table__col--compact",
        render: (row) => `v${row.version}`,
      },
      {
        key: "status",
        header: "Estado",
        className: "cf-table__col--status",
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
        className: "cf-table__col--compact",
        render: (row) => row.item_count,
      },
      {
        key: "effective",
        header: "Vigente desde",
        className: "cf-table__col--compact",
        render: (row) =>
          row.effective_from_period ?? (
            <span className="cf-cell-muted">—</span>
          ),
      },
      {
        key: "published",
        header: "Publicação",
        className: "cf-table__col--wrap",
        render: (row) =>
          row.published_at ? (
            `${formatDateTime(row.published_at)}`
          ) : (
            <span className="cf-cell-muted">—</span>
          ),
      },
      {
        key: "actions",
        header: "Ações",
        className: "cf-table__col--status",
        render: (row) => (
          <div className="cf-validation-panel__doc-actions">
            <ActionButton
              variant="ghost"
              disabled={actions.busy}
              onClick={() => openVersion(row.version)}
            >
              Abrir versão
            </ActionButton>
            <VersionStatusActions
              version={row}
              busy={actions.busy}
              actions={actions}
            />
          </div>
        ),
      },
    ],
    [actions, openVersion],
  );

  const draftOpen = (currentVersions ?? []).some(
    (v) => v.status === "DRAFT" || v.status === "REVIEW",
  );

  return (
    <section
      className="cf-checklist-page"
      aria-label="Administração do checklist"
    >
      <div className="cf-checklist-page__content">
        <CfTitleWithHelp
          title="Administração do checklist mestre"
          hint={CF_HELP.admin.page}
        />

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
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Carregando administração…"
          />
        ) : !error && !template ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum template de checklist registrado."
          />
        ) : template ? (
          <CfSectionCard
            title={`${template.name} (${template.code})`}
            hint={CF_HELP.admin.versions}
          >
            <div className="cf-card-stack">
              <div className="cf-validation-panel__item-actions">
                <CfActionButton
                  type="button"
                  variant="primary"
                  disabled={actions.busy || draftOpen}
                  title={
                    draftOpen
                      ? "Já existe um rascunho aberto — edite-o ou publique-o antes."
                      : undefined
                  }
                  onClick={() =>
                    actions.run(() =>
                      createTemplateDraft(template.template_id),
                    )
                  }
                >
                  Criar versão rascunho
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
                  Eventos de auditoria
                </CfActionButton>
                <CfActionButton
                  type="button"
                  variant="ghost"
                  onClick={() => navigatePluginView("documents_admin")}
                >
                  Documentos do fechamento
                </CfActionButton>
              </div>
              <DataTableSection<ChecklistTemplateVersion>
                title="Versões"
                titleHint={CF_HELP.admin.versions}
                columns={versionColumns}
                rows={currentVersions ?? []}
                rowKey={(row) => row.version_id}
                loading={currentVersions === null}
                hideSearch
                emptyMessage="Nenhuma versão registrada."
              />
            </div>
          </CfSectionCard>
        ) : null}
      </div>

      {actions.dialogs}
    </section>
  );
}
