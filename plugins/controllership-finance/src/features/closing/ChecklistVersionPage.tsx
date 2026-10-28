/**
 * Página contextual de uma versão do checklist mestre (UX-015, nível 2
 * da navegação em cascata): metadados da versão, os documentos/itens
 * daquele snapshot histórico e as ações governadas pelo estado.
 *
 * Consome `GET /admin/checklist-templates/{id}/versions/{n}` — dados
 * reais da versão selecionada, nunca o catálogo vigente. Edição de
 * itens só em DRAFT, atômica com OCC `revision`; PUBLISHED e INACTIVE
 * são somente leitura. Alterações prospectivas de exigência seguem o
 * fluxo do catálogo documental (UX-012).
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ActionButton } from "@delpi/plugin-ui/index";

import { History } from "lucide-react";

import {
  getTemplateVersion,
  listChecklistTemplates,
  updateTemplateDraft,
  type ChecklistTemplate,
  type ChecklistTemplateVersionDetail,
} from "../../api/adminApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfDataRecordCard,
  CfEmptyState,
  CfPageHero,
  CfPagePath,
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
  checklistAdminVersionDocumentPath,
} from "../../app/pluginRoutes";
import {
  APPLICABILITY_OPTIONS,
  ChecklistItemFormDialog,
  EMPTY_ITEM,
  ORIGIN_OPTIONS,
  RECIPIENT_OPTIONS,
  SCOPE_OPTIONS,
  STATUS_LABELS,
  STATUS_VARIANTS,
  toQueryError,
  useChecklistVersionActions,
  VersionStatusActions,
  type EditableItem,
  type QueryError,
} from "./checklistAdminShared";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

export function ChecklistVersionPage({
  basePath,
  version,
}: {
  basePath: string;
  version: number;
}) {
  const [nonce, setNonce] = useState(0);
  const [template, setTemplate] = useState<ChecklistTemplate | null>(
    null,
  );
  const [templateLoaded, setTemplateLoaded] = useState(false);
  const [detail, setDetail] = useState<{
    key: string;
    data: ChecklistTemplateVersionDetail;
  } | null>(null);
  const [error, setError] = useState<QueryError | null>(null);

  const [editing, setEditing] = useState<{
    revision: number;
    items: EditableItem[];
  } | null>(null);
  const [itemForm, setItemForm] = useState<EditableItem | null>(null);
  const [itemFormIndex, setItemFormIndex] = useState<number | null>(
    null,
  );

  const requestId = useRef(0);
  const detailKey = template
    ? `${template.template_id}:${version}:${nonce}`
    : "";
  const detailData = detail?.key === detailKey ? detail.data : null;
  const loading = !templateLoaded && !error;

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  const backToAdmin = useCallback(
    () => navigatePluginView("checklist_admin", { basePath }),
    [basePath],
  );

  const actions = useChecklistVersionActions({
    templateId: template?.template_id ?? null,
    onDone: reload,
    onDiscarded: backToAdmin,
  });

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listChecklistTemplates({ signal: controller.signal })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setTemplate(items[0] ?? null);
        setTemplateLoaded(true);
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
    getTemplateVersion(template.template_id, version, {
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setDetail({ key: detailKey, data });
        // Novo snapshot da versão: edição e formulário de item sempre
        // recomeçam do estado carregado — nunca carrega itens de outra
        // versão quando a rota muda sem remontar o componente.
        setEditing(null);
        setItemForm(null);
        setItemFormIndex(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError(toQueryError(err, "Falha ao carregar a versão."));
      });
    return () => controller.abort();
  }, [template, version, detailKey]);

  const startEditing = useCallback(() => {
    if (!detailData || detailData.status !== "DRAFT") return;
    setEditing({
      revision: detailData.revision,
      items: detailData.items.map((item) => ({
        item_id: item.item_id,
        item_key: item.item_key,
        sort_order: item.sort_order,
        sheet: item.sheet,
        name: item.name,
        purpose: item.purpose,
        origin_kind: item.origin_kind,
        recipient_area: item.recipient_area,
        applicability: item.applicability,
        branch_scope: item.branch_scope,
        totvs_report_ref: item.totvs_report_ref,
        requirement_notes: item.requirement_notes,
        validation_scope: item.validation_scope,
      })),
    });
  }, [detailData]);

  const saveDraft = useCallback(() => {
    if (!template || !detailData || !editing) return;
    actions.run(
      () =>
        updateTemplateDraft(template.template_id, detailData.version, {
          revision: editing.revision,
          items: editing.items.map((item) => ({
            item_key: item.item_key,
            sort_order: item.sort_order,
            sheet: item.sheet,
            name: item.name,
            purpose: item.purpose,
            origin_kind: item.origin_kind,
            recipient_area: item.recipient_area,
            applicability: item.applicability,
            branch_scope: item.branch_scope,
            totvs_report_ref: item.totvs_report_ref,
            requirement_notes: item.requirement_notes,
            validation_scope: item.validation_scope,
          })),
        }),
      () => setEditing(null),
    );
  }, [template, detailData, editing, actions]);

  const submitItemForm = useCallback(() => {
    if (!editing || !itemForm) return;
    const items = [...editing.items];
    if (itemFormIndex !== null && itemFormIndex >= 0) {
      items[itemFormIndex] = itemForm;
    } else {
      items.push(itemForm);
    }
    setEditing({ ...editing, items });
    setItemForm(null);
    setItemFormIndex(null);
  }, [editing, itemForm, itemFormIndex]);

  const openItem = useCallback(
    (itemKey: string) => {
      navigatePluginPath(
        checklistAdminVersionDocumentPath(version, itemKey, basePath),
      );
    },
    [version, basePath],
  );

  const itemColumns = useMemo<DataTableColumn<EditableItem>[]>(() => {
    const columns: DataTableColumn<EditableItem>[] = [
      {
        key: "item_key",
        header: "Item",
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) => row.item_key,
        render: (row) => (
          <span className="cf-cell-primary">{row.item_key}</span>
        ),
      },
      {
        key: "name",
        header: "Entregável",
        className: "cf-table__col--wrap",
        sortable: true,
        sortValue: (row) => row.name,
        render: (row) => row.name,
      },
      {
        key: "sheet",
        header: "Folha",
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) =>
          row.sheet === "FISICO" ? "Físico" : "Eletrônico",
        render: (row) =>
          row.sheet === "FISICO" ? "Físico" : "Eletrônico",
      },
      {
        key: "origin",
        header: "Origem",
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) =>
          ORIGIN_OPTIONS.find((o) => o.value === row.origin_kind)
            ?.label ?? row.origin_kind,
        render: (row) =>
          ORIGIN_OPTIONS.find((o) => o.value === row.origin_kind)
            ?.label ?? row.origin_kind,
      },
      {
        key: "recipient",
        header: "Destinatário",
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) =>
          (row.recipient_area &&
            (RECIPIENT_OPTIONS.find(
              (o) => o.value === row.recipient_area,
            )?.label ?? row.recipient_area)) ??
          "",
        render: (row) =>
          row.recipient_area ? (
            (RECIPIENT_OPTIONS.find(
              (o) => o.value === row.recipient_area,
            )?.label ?? row.recipient_area)
          ) : (
            <span className="cf-cell-muted">A definir</span>
          ),
      },
      {
        key: "applicability",
        header: "Obrigatório",
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) =>
          APPLICABILITY_OPTIONS.find(
            (o) => o.value === row.applicability,
          )?.label ?? row.applicability,
        render: (row) =>
          APPLICABILITY_OPTIONS.find(
            (o) => o.value === row.applicability,
          )?.label ?? row.applicability,
      },
      {
        key: "scope",
        header: "Validação",
        className: "cf-table__col--compact",
        sortable: true,
        sortValue: (row) =>
          SCOPE_OPTIONS.find((o) => o.value === row.validation_scope)
            ?.label ?? row.validation_scope,
        render: (row) =>
          SCOPE_OPTIONS.find((o) => o.value === row.validation_scope)
            ?.label ?? row.validation_scope,
      },
    ];
    if (!editing) return columns;
    return [
      ...columns,
      {
        key: "actions",
        header: "Ações",
        className: "cf-table__col--status",
        rowClick: "stop" as const,
        render: (row: EditableItem) => {
          const index = editing.items.indexOf(row);
          return (
            <div className="cf-validation-panel__doc-actions">
              <ActionButton
                variant="ghost"
                disabled={actions.busy}
                onClick={() => {
                  setItemForm({ ...row });
                  setItemFormIndex(index);
                }}
              >
                Editar
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={actions.busy}
                onClick={() =>
                  setEditing({
                    ...editing,
                    items: editing.items.filter(
                      (_, i) => i !== index,
                    ),
                  })
                }
              >
                Remover
              </ActionButton>
            </div>
          );
        },
      },
    ];
  }, [editing, actions.busy]);

  const renderItemCard = useCallback(
    (row: EditableItem) => {
      const fields: DataRecordCardField[] = [
        {
          id: "sheet",
          label: "Folha",
          value: row.sheet === "FISICO" ? "Físico" : "Eletrônico",
        },
        {
          id: "origin",
          label: "Origem",
          value:
            ORIGIN_OPTIONS.find((o) => o.value === row.origin_kind)
              ?.label ?? row.origin_kind,
        },
        {
          id: "recipient",
          label: "Destinatário",
          value: row.recipient_area
            ? (RECIPIENT_OPTIONS.find(
                (o) => o.value === row.recipient_area,
              )?.label ?? row.recipient_area)
            : "A definir",
        },
        {
          id: "scope",
          label: "Validação",
          value:
            SCOPE_OPTIONS.find(
              (o) => o.value === row.validation_scope,
            )?.label ?? row.validation_scope,
        },
      ];
      const applicabilityLabel =
        APPLICABILITY_OPTIONS.find(
          (o) => o.value === row.applicability,
        )?.label ?? row.applicability;
      if (!editing) {
        const href = checklistAdminVersionDocumentPath(
          version,
          row.item_key,
          basePath,
        );
        return (
          <CfDataRecordCard
            href={href}
            onNavigate={(event) => {
              event.preventDefault();
              navigatePluginPath(href);
            }}
            title={row.name}
            subtitle={row.item_key}
            status={applicabilityLabel}
            fields={fields}
            ariaLabel={`Abrir documento ${row.name}`}
          />
        );
      }
      const index = editing.items.indexOf(row);
      return (
        <div className="cf-version-card">
          <CfDataRecordCard
            title={row.name}
            subtitle={row.item_key}
            status={applicabilityLabel}
            fields={fields}
            ariaLabel={`Item ${row.name}`}
          />
          <div className="cf-version-card__actions">
            <ActionButton
              variant="ghost"
              disabled={actions.busy}
              onClick={() => {
                setItemForm({ ...row });
                setItemFormIndex(index);
              }}
            >
              Editar
            </ActionButton>
            <ActionButton
              variant="ghost"
              disabled={actions.busy}
              onClick={() =>
                setEditing({
                  ...editing,
                  items: editing.items.filter((_, i) => i !== index),
                })
              }
            >
              Remover
            </ActionButton>
          </div>
        </div>
      );
    },
    [editing, actions.busy, version, basePath],
  );

  // Host da toolbar da listagem — renderizada no hero via portal do
  // DataTableSection (mesma instância/estado; `toolbarPortalTarget`).
  const [toolbarHost, setToolbarHost] =
    useState<HTMLElement | null>(null);

  return (
    <section
      className="cf-page-stack cf-closing-layout cf-hero-page"
      aria-label={`Versão v${version} do checklist`}
    >
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={{
          label: "Administração",
          href: `${basePath}/closing/admin`,
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            backToAdmin();
          },
        }}
        items={[
          {
            id: "admin",
            label: "Administração",
            href: `${basePath}/closing/admin`,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              backToAdmin();
            },
          },
        ]}
        current={`Versão v${version}`}
      />

      <div className="cf-hero-page__content">
        <CfPageHero
          aria-label={`Versão v${version} do checklist`}
          eyebrow="Administração"
          title={
            <CfTitleWithHelp
              title={`Versão v${version}`}
              hint={CF_HELP.adminVersion.page}
            />
          }
          badge={
            detailData ? (
              <CfStatusBadge
                label={
                  STATUS_LABELS[detailData.status] ??
                  detailData.status
                }
                variant={
                  STATUS_VARIANTS[detailData.status] ?? "neutral"
                }
              />
            ) : null
          }
          description={template?.name ?? "Checklist de Fechamento Mensal"}
          highlights={
            detailData
              ? [
                  {
                    id: "items",
                    label: "Documentos",
                    value: String(detailData.items.length),
                  },
                  {
                    id: "effective",
                    label: "Vigente desde",
                    value: detailData.effective_from_period ?? "—",
                  },
                  {
                    id: "published",
                    label: "Publicada em",
                    value: detailData.published_at
                      ? formatDateTime(detailData.published_at)
                      : "—",
                  },
                  {
                    id: "publishedBy",
                    label: "Publicada por",
                    // UX-014: contrato Core→BFF para atores
                    // administrativos ainda pendente — fallback neutro,
                    // nunca o subject cru como nome nem no hero.
                    value: detailData.published_by
                      ? "Identidade não disponível"
                      : "—",
                  },
                  {
                    id: "revision",
                    label: "Revisão",
                    value: String(detailData.revision),
                  },
                ]
              : undefined
          }
          actions={
            detailData ? (
              <div className="cf-validation-panel__item-actions">
                <CfActionButton
                  type="button"
                  variant="ghost"
                  onClick={() =>
                    navigatePluginPath(
                      checklistAdminEventsPath(version, basePath),
                    )
                  }
                >
                  <History
                    size={15}
                    strokeWidth={1.9}
                    aria-hidden="true"
                  />
                  Histórico da versão
                </CfActionButton>
                {detailData.status === "DRAFT" && !editing ? (
                  <CfActionButton
                    type="button"
                    disabled={actions.busy}
                    onClick={startEditing}
                  >
                    Editar itens
                  </CfActionButton>
                ) : null}
                <VersionStatusActions
                  version={detailData}
                  busy={actions.busy}
                  actions={actions}
                />
              </div>
            ) : undefined
          }
        >
          <div
            ref={setToolbarHost}
            className="cf-hero-toolbar"
            data-testid="version-listing-toolbar"
          />
        </CfPageHero>

        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="a versão do checklist"
            onRetry={reload}
          />
        ) : null}
        {actions.actionError ? (
          <CfFeedbackMessage intent="error" title="Ação não concluída">
            {actions.actionError.message}
            {actions.actionError.code === "stale_revision" ? (
              <>
                {" "}
                <button
                  type="button"
                  className="cf-link-button"
                  onClick={() => {
                    reload();
                  }}
                >
                  Recarregar versão
                </button>
              </>
            ) : null}
          </CfFeedbackMessage>
        ) : null}

        {loading || (templateLoaded && template && !detailData && !error) ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Carregando versão…"
          />
        ) : !error && templateLoaded && !template ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum template de checklist registrado."
          />
        ) : detailData ? (
          <>
            <div className="cf-flex-listing">
              <DataTableSection<EditableItem>
                title="Documentos da versão"
                titleHint={
                  editing
                    ? CF_HELP.admin.editDraft
                    : CF_HELP.adminVersion.items
                }
                columns={itemColumns}
                rows={editing ? editing.items : detailData.items}
                rowKey={(row) => row.item_key}
                loading={false}
                emptyMessage="Nenhum item nesta versão."
                columnPreferencesKey="cf-checklist-version-items-columns"
                viewLayoutPreferencesKey="cf-checklist-version-items"
                renderCard={renderItemCard}
                onRowClick={
                  editing
                    ? undefined
                    : (row) => openItem(row.item_key)
                }
                getSearchText={(row) =>
                  `${row.item_key} ${row.name} ${row.sheet} ${row.origin_kind} ${row.recipient_area ?? ""}`
                }
                toolbarPortalTarget={toolbarHost}
                tableLayout="scroll"
                headerActions={
                  editing ? (
                    <div className="cf-validation-panel__item-actions">
                      <CfActionButton
                        type="button"
                        disabled={
                          actions.busy || editing.items.length === 0
                        }
                        onClick={saveDraft}
                      >
                        {actions.busy
                          ? "Salvando…"
                          : "Salvar rascunho"}
                      </CfActionButton>
                      <CfActionButton
                        type="button"
                        variant="ghost"
                        disabled={actions.busy}
                        onClick={() => {
                          setItemForm({ ...EMPTY_ITEM });
                          setItemFormIndex(null);
                        }}
                      >
                        Adicionar item
                      </CfActionButton>
                      <CfActionButton
                        type="button"
                        variant="ghost"
                        disabled={actions.busy}
                        onClick={() => setEditing(null)}
                      >
                        Descartar edição
                      </CfActionButton>
                    </div>
                  ) : undefined
                }
              />
            </div>
          </>
        ) : null}
      </div>

      {actions.dialogs}

      {itemForm ? (
        <ChecklistItemFormDialog
          item={itemForm}
          isNew={itemFormIndex === null}
          onChange={setItemForm}
          onSubmit={submitItemForm}
          onClose={() => {
            setItemForm(null);
            setItemFormIndex(null);
          }}
        />
      ) : null}
    </section>
  );
}
