/**
 * Administração do checklist mestre — P6 (A3).
 *
 * Consome `/admin/checklist-templates*` da BFF (MANAGE efetivo — o
 * backend é a única autoridade; a página apenas renderiza e encaminha).
 * Versionamento prospectivo: publicar cria vigência futura e nunca
 * altera competências já abertas; inativar preserva histórico.
 * Edição de DRAFT é atômica com OCC `revision` — `stale_revision`
 * pede recarga, nunca sobrescreve.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  ActionButton,
  ConfirmModalPanel,
} from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import { CatalogSaveError } from "./documentCatalog";
import {
  createTemplateDraft,
  discardTemplateVersion,
  getTemplateVersion,
  inactivateTemplateVersion,
  listChecklistTemplates,
  listTemplateEvents,
  listTemplateVersions,
  publishTemplateVersion,
  returnVersionToDraft,
  submitVersionForReview,
  updateTemplateDraft,
  type ChecklistTemplate,
  type ChecklistTemplateItem,
  type ChecklistTemplateVersion,
  type ChecklistTemplateVersionDetail,
  type DraftItemInput,
  type TemplateAuditEvent,
} from "../../api/adminApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfDateField,
  CfDialog,
  CfEmptyState,
  CfSectionCard,
  CfSelectField,
  CfStatusBadge,
  CfTextAreaField,
  CfTextField,
  CfTimeline,
  CfTitleWithHelp,
  cfConfirmModalClassNames,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

type QueryError = { status: number; code: string | null; message: string };

export const ERROR_MESSAGES: Record<string, string> = {
  forbidden:
    "Você não tem autorização administrativa (controllership-finance.manage).",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  template_not_found: "Template de checklist não encontrado.",
  version_not_found: "Versão do checklist não encontrada.",
  version_not_draft: "Somente versões DRAFT podem ser editadas.",
  stale_revision:
    "A versão foi alterada por outra sessão — recarregue antes de salvar.",
  draft_already_open:
    "Já existe uma versão DRAFT ou em revisão aberta para este template.",
  version_not_in_review:
    "Somente versões em revisão podem ser publicadas ou devolvidas.",
  already_published: "Esta versão já foi publicada.",
  invalid_effective_period:
    "A vigência deve ser uma competência futura no formato AAAA-MM.",
  not_latest_published:
    "Somente a versão publicada mais recente pode ser inativada.",
  catalog_draft_conflict:
    "Existe uma versão em rascunho ou revisão com outro conteúdo — conclua-a ou descarte-a na Administração do checklist.",
  window_covers_open_competence:
    "A vigência escolhida alcança uma competência já aberta — ajuste o período ou use item excepcional na competência.",
  empty_resulting_checklist:
    "A operação deixaria o checklist sem nenhum documento exigido — confirme a intenção antes de prosseguir.",
  idempotency_conflict:
    "A operação já foi enviada com outro conteúdo — recarregue a página e confira o estado atual.",
  retroactive_effective_period:
    "A vigência inicial não pode ser uma competência passada.",
  invalid_window:
    "A competência final não pode ser anterior à inicial.",
  item_key_mismatch:
    "O identificador do documento diverge da rota — recarregue a página.",
  busy:
    "Outra operação administrativa está em curso neste checklist — tente novamente em instantes.",
};

function toQueryError(error: unknown, fallback: string): QueryError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code,
      message:
        (error.code && ERROR_MESSAGES[error.code]) || error.message,
    };
  }
  if (error instanceof CatalogSaveError) {
    return {
      status: 0,
      code: error.code,
      message: ERROR_MESSAGES[error.code] ?? error.message,
    };
  }
  return { status: 0, code: null, message: fallback };
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Rascunho",
  REVIEW: "Em revisão",
  PUBLISHED: "Publicada",
  INACTIVE: "Inativada",
};

const STATUS_VARIANTS: Record<
  string,
  "neutral" | "success" | "info" | "warning"
> = {
  DRAFT: "info",
  REVIEW: "warning",
  PUBLISHED: "success",
  INACTIVE: "neutral",
  DISCARDED: "neutral",
};

export const EVENT_LABELS: Record<string, string> = {
  DRAFT_CREATED: "Rascunho criado",
  DRAFT_UPDATED: "Rascunho atualizado",
  VERSION_SUBMITTED_FOR_REVIEW: "Enviada a revisão",
  VERSION_RETURNED_TO_DRAFT: "Devolvida a rascunho",
  VERSION_PUBLISHED: "Versão publicada",
  VERSION_INACTIVATED: "Versão inativada",
  VERSION_DISCARDED: "Versão descartada",
};

/** Tom semântico do marker da timeline por tipo de evento de auditoria. */
export const EVENT_TONES: Record<
  string,
  "default" | "info" | "warning" | "success" | "danger"
> = {
  DRAFT_CREATED: "info",
  DRAFT_UPDATED: "default",
  VERSION_SUBMITTED_FOR_REVIEW: "warning",
  VERSION_RETURNED_TO_DRAFT: "warning",
  VERSION_PUBLISHED: "success",
  VERSION_INACTIVATED: "default",
  VERSION_DISCARDED: "danger",
};

const SHEET_OPTIONS = [
  { value: "ELETRONICO", label: "Eletrônico" },
  { value: "FISICO", label: "Físico" },
];

const ORIGIN_OPTIONS = [
  { value: "TOTVS", label: "ERP TOTVS" },
  { value: "EXTERNAL", label: "Fonte externa" },
  { value: "MIXED", label: "Origem mista" },
];

const RECIPIENT_OPTIONS = [
  { value: "", label: "A definir" },
  { value: "CONTABIL", label: "Contábil" },
  { value: "FISCAL", label: "Fiscal" },
];

const APPLICABILITY_OPTIONS = [
  { value: "REQUIRED", label: "Obrigatório" },
  { value: "CONDITIONAL", label: "Condicional" },
  { value: "OPTIONAL", label: "Opcional" },
];

const BRANCH_OPTIONS = [
  { value: "MATRIX", label: "Matriz" },
  { value: "BRANCH", label: "Filial" },
  { value: "BOTH", label: "Matriz e filiais" },
];

const SCOPE_OPTIONS = [
  { value: "PER_ATTACHMENT", label: "Por anexo" },
  { value: "WHOLE_SET", label: "Conjunto" },
];

type EditableItem = DraftItemInput & { item_id?: string };

function toDraftInput(item: ChecklistTemplateItem): EditableItem {
  return {
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
  };
}

const EMPTY_ITEM: EditableItem = {
  item_key: "",
  sheet: "ELETRONICO",
  name: "",
  origin_kind: "EXTERNAL",
  recipient_area: null,
  applicability: "REQUIRED",
  branch_scope: "BOTH",
  validation_scope: "PER_ATTACHMENT",
};

export function ChecklistAdminPage() {
  const [nonce, setNonce] = useState(0);
  const [templates, setTemplates] = useState<{
    key: number;
    items: ChecklistTemplate[];
  } | null>(null);
  const [versions, setVersions] = useState<{
    key: string;
    items: ChecklistTemplateVersion[];
  } | null>(null);
  const [detail, setDetail] = useState<{
    key: string;
    data: ChecklistTemplateVersionDetail;
  } | null>(null);
  const [error, setError] = useState<QueryError | null>(null);
  const [actionError, setActionError] = useState<QueryError | null>(null);
  const [busy, setBusy] = useState(false);

  const [editing, setEditing] = useState<{
    versionId: string;
    items: EditableItem[];
    revision: number;
  } | null>(null);
  const [itemForm, setItemForm] = useState<EditableItem | null>(null);
  const [itemFormIndex, setItemFormIndex] = useState<number | null>(null);

  const [publishTarget, setPublishTarget] =
    useState<ChecklistTemplateVersion | null>(null);
  const [publishPeriod, setPublishPeriod] = useState("");
  const [inactivateTarget, setInactivateTarget] =
    useState<ChecklistTemplateVersion | null>(null);
  const [returnTarget, setReturnTarget] =
    useState<ChecklistTemplateVersion | null>(null);
  const [returnReason, setReturnReason] = useState("");
  const [discardTarget, setDiscardTarget] =
    useState<ChecklistTemplateVersion | null>(null);
  const [eventsTemplate, setEventsTemplate] =
    useState<ChecklistTemplate | null>(null);
  const [events, setEvents] = useState<TemplateAuditEvent[] | null>(null);
  const [eventsError, setEventsError] = useState<QueryError | null>(null);

  const requestId = useRef(0);
  const template = templates?.items[0] ?? null;
  const versionsKey = template ? `${template.template_id}:${nonce}` : "";
  const currentVersions =
    versions?.key === versionsKey ? versions.items : null;
  const loading = templates === null && !error;

  const reload = useCallback(() => setNonce((n) => n + 1), []);

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

  const run = useCallback(
    (work: () => Promise<unknown>, onDone?: () => void) => {
      setBusy(true);
      setActionError(null);
      work()
        .then(() => {
          setBusy(false);
          onDone?.();
          reload();
        })
        .catch((err: unknown) => {
          setBusy(false);
          setActionError(
            toQueryError(err, "A ação não pôde ser concluída."),
          );
        });
    },
    [reload],
  );

  const openItems = useCallback(
    (version: ChecklistTemplateVersion, editable: boolean) => {
      if (!template) return;
      getTemplateVersion(template.template_id, version.version)
        .then((data) => {
          setDetail({ key: data.version_id, data });
          if (editable && data.status === "DRAFT") {
            setEditing({
              versionId: data.version_id,
              revision: data.revision,
              items: data.items.map(toDraftInput),
            });
          } else {
            setEditing(null);
          }
        })
        .catch((err: unknown) =>
          setActionError(
            toQueryError(err, "Falha ao carregar a versão."),
          ),
        );
    },
    [template],
  );

  const openEvents = useCallback(
    (target: ChecklistTemplate) => {
      setEventsTemplate(target);
      setEvents(null);
      setEventsError(null);
      listTemplateEvents(target.template_id)
        .then(setEvents)
        .catch((err: unknown) =>
          setEventsError(
            toQueryError(err, "Falha ao listar os eventos."),
          ),
        );
    },
    [],
  );

  const saveDraft = useCallback(() => {
    if (!template || !editing) return;
    run(
      () =>
        updateTemplateDraft(template.template_id, detail!.data.version, {
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
      () => {
        setEditing(null);
        setDetail(null);
      },
    );
  }, [template, editing, detail, run]);

  const submitPublish = useCallback(() => {
    if (!template || !publishTarget || !publishPeriod) return;
    run(
      () =>
        publishTemplateVersion(template.template_id, publishTarget.version, {
          effective_from_period: publishPeriod,
        }),
      () => setPublishTarget(null),
    );
  }, [template, publishTarget, publishPeriod, run]);

  const confirmSubmitReview = useCallback(
    (row: ChecklistTemplateVersion) => {
      if (!template) return;
      run(() =>
        submitVersionForReview(template.template_id, row.version),
      );
    },
    [template, run],
  );

  const submitReturn = useCallback(() => {
    if (!template || !returnTarget || !returnReason.trim()) return;
    run(
      () =>
        returnVersionToDraft(template.template_id, returnTarget.version, {
          reason: returnReason.trim(),
        }),
      () => {
        setReturnTarget(null);
        setReturnReason("");
      },
    );
  }, [template, returnTarget, returnReason, run]);

  const confirmInactivate = useCallback(() => {
    if (!template || !inactivateTarget) return;
    run(
      () =>
        inactivateTemplateVersion(
          template.template_id,
          inactivateTarget.version,
        ),
      () => setInactivateTarget(null),
    );
  }, [template, inactivateTarget, run]);

  const confirmDiscard = useCallback(() => {
    if (!template || !discardTarget) return;
    run(
      () =>
        discardTemplateVersion(
          template.template_id,
          discardTarget.version,
          discardTarget.revision,
        ),
      () => {
        setDiscardTarget(null);
        setDetail(null);
        setEditing(null);
      },
    );
  }, [template, discardTarget, run]);

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
              disabled={busy}
              onClick={() => openItems(row, row.status === "DRAFT")}
            >
              Itens
            </ActionButton>
            {row.status === "DRAFT" ? (
              <>
                <ActionButton
                  variant="ghost"
                  disabled={busy}
                  onClick={() => confirmSubmitReview(row)}
                >
                  Enviar para revisão
                </ActionButton>
                <ActionButton
                  variant="ghost"
                  className="cf-action-btn--danger"
                  disabled={busy}
                  onClick={() => setDiscardTarget(row)}
                >
                  Descartar
                </ActionButton>
              </>
            ) : null}
            {row.status === "REVIEW" ? (
              <>
                <ActionButton
                  variant="ghost"
                  disabled={busy}
                  onClick={() => {
                    setPublishTarget(row);
                    setPublishPeriod("");
                  }}
                >
                  Publicar
                </ActionButton>
                <ActionButton
                  variant="ghost"
                  disabled={busy}
                  onClick={() => {
                    setReturnTarget(row);
                    setReturnReason("");
                  }}
                >
                  Devolver
                </ActionButton>
              </>
            ) : null}
            {row.status === "PUBLISHED" ? (
              <ActionButton
                variant="ghost"
                className="cf-action-btn--danger"
                disabled={busy}
                onClick={() => setInactivateTarget(row)}
              >
                Inativar
              </ActionButton>
            ) : null}
          </div>
        ),
      },
    ],
    [busy, openItems, confirmSubmitReview],
  );

  const itemColumns = useMemo<DataTableColumn<EditableItem>[]>(
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
        header: "Entregável",
        className: "cf-table__col--wrap",
        render: (row) => row.name,
      },
      {
        key: "sheet",
        header: "Folha",
        className: "cf-table__col--compact",
        render: (row) =>
          row.sheet === "FISICO" ? "Físico" : "Eletrônico",
      },
      {
        key: "origin",
        header: "Origem",
        className: "cf-table__col--compact",
        render: (row) =>
          ORIGIN_OPTIONS.find((o) => o.value === row.origin_kind)
            ?.label ?? row.origin_kind,
      },
      {
        key: "recipient",
        header: "Destinatário",
        className: "cf-table__col--compact",
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
        render: (row) =>
          APPLICABILITY_OPTIONS.find(
            (o) => o.value === row.applicability,
          )?.label ?? row.applicability,
      },
      {
        key: "scope",
        header: "Validação",
        className: "cf-table__col--compact",
        render: (row) =>
          SCOPE_OPTIONS.find((o) => o.value === row.validation_scope)
            ?.label ?? row.validation_scope,
      },
      ...(editing
        ? [
            {
              key: "edit",
              header: "Ações",
              className: "cf-table__col--status",
              render: (row: EditableItem) => {
                const index = editing.items.indexOf(row);
                return (
                  <div className="cf-validation-panel__doc-actions">
                    <ActionButton
                      variant="ghost"
                      disabled={busy}
                      onClick={() => {
                        setItemForm({ ...row });
                        setItemFormIndex(index);
                      }}
                    >
                      Editar
                    </ActionButton>
                    <ActionButton
                      variant="ghost"
                      disabled={busy}
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
            } as DataTableColumn<EditableItem>,
          ]
        : []),
    ],
    [editing, busy],
  );

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

  const detailData = detail?.data ?? null;
  const draftOpen = (currentVersions ?? []).some(
    (v) => v.status === "DRAFT",
  );

  return (
    <section className="cf-checklist-page" aria-label="Administração do checklist">
      <div className="cf-checklist-page__content">
        <CfTitleWithHelp
          title="Administração do checklist mestre"
          hint={CF_HELP.admin.page}
        />

        {actionError ? (
          <CfFeedbackMessage intent="error" title="Ação não concluída">
            {actionError.message}
          </CfFeedbackMessage>
        ) : null}

        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="a administração do checklist"
            onRetry={reload}
          />
        ) : loading ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Carregando administração…"
          />
        ) : template ? (
          <>
            <CfSectionCard
              title={`${template.name} (${template.code})`}
              hint={CF_HELP.admin.versions}
            >
              <div className="cf-card-stack">
                <div className="cf-validation-panel__item-actions">
                  <CfActionButton
                    type="button"
                    variant="primary"
                    disabled={busy || draftOpen}
                    title={
                      draftOpen
                        ? "Já existe um rascunho aberto — edite-o ou publique-o antes."
                        : undefined
                    }
                    onClick={() =>
                      run(() => createTemplateDraft(template.template_id))
                    }
                  >
                    Criar versão rascunho
                  </CfActionButton>
                  <CfActionButton
                    type="button"
                    variant="ghost"
                    onClick={() => openEvents(template)}
                  >
                    Eventos de auditoria
                  </CfActionButton>
                  <CfActionButton
                    type="button"
                    variant="ghost"
                    onClick={() =>
                      navigatePluginView("documents_admin")
                    }
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

            {detailData ? (
              <CfSectionCard
                title={`Itens — v${detailData.version} (${STATUS_LABELS[detailData.status] ?? detailData.status})`}
                hint={
                  editing ? CF_HELP.admin.editDraft : CF_HELP.admin.items
                }
              >
              <div className="cf-card-stack">
                {editing ? (
                  <div className="cf-validation-panel__item-actions">
                    <CfActionButton
                      type="button"
                      disabled={busy || editing.items.length === 0}
                      onClick={saveDraft}
                    >
                      {busy ? "Salvando…" : "Salvar rascunho"}
                    </CfActionButton>
                    <CfActionButton
                      type="button"
                      variant="ghost"
                      disabled={busy}
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
                      disabled={busy}
                      onClick={() => {
                        setEditing(null);
                        openItems(detailData, false);
                      }}
                    >
                      Descartar edição
                    </CfActionButton>
                  </div>
                ) : null}
                <DataTableSection<EditableItem>
                  title="Itens do checklist"
                  columns={itemColumns}
                  rows={editing ? editing.items : detailData.items}
                  rowKey={(row) => row.item_key}
                  loading={false}
                  emptyMessage="Nenhum item nesta versão."
                />
              </div>
              </CfSectionCard>
            ) : null}
          </>
        ) : (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum template de checklist registrado."
          />
        )}
      </div>

      {publishTarget ? (
        <CfDialog
          open
          title={`Publicar v${publishTarget.version}`}
          onClose={() => !busy && setPublishTarget(null)}
          closeAriaLabel="Fechar publicação"
        >
          <div className="cf-validation-panel__form">
            <p className="cf-validation-panel__doc-detail">
              A publicação é prospectiva: a versão passa a valer a partir
              da competência informada e não altera competências já abertas.
            </p>
            <CfDateField
              label="Vigente a partir de (AAAA-MM)"
              type="month"
              required
              value={publishPeriod}
              disabled={busy}
              onChange={setPublishPeriod}
            />
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={
                  busy ||
                  !/^\d{4}-(0[1-9]|1[0-2])$/.test(publishPeriod)
                }
                onClick={submitPublish}
              >
                Publicar versão
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setPublishTarget(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}

      {returnTarget ? (
        <CfDialog
          open
          title={`Devolver v${returnTarget.version} a rascunho`}
          onClose={() => !busy && setReturnTarget(null)}
          closeAriaLabel="Fechar devolução"
        >
          <div className="cf-validation-panel__form">
            <p className="cf-validation-panel__doc-detail">
              A devolução reabre a versão para edição — o motivo fica
              registrado no histórico de auditoria da versão.
            </p>
            <CfTextAreaField
              label="Motivo da devolução"
              rows={3}
              required
              fullWidth
              value={returnReason}
              disabled={busy}
              onChange={setReturnReason}
            />
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={busy || !returnReason.trim()}
                onClick={submitReturn}
              >
                Devolver a rascunho
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setReturnTarget(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}

      {inactivateTarget ? (
        <CfDialog
          open
          title={`Inativar v${inactivateTarget.version}`}
          onClose={() => !busy && setInactivateTarget(null)}
          closeAriaLabel="Fechar inativação"
        >
          <ConfirmModalPanel
            message={
              <>
                Inativar a versão v{inactivateTarget.version}? A ação é
                prospectiva — competências abertas com esta versão não são
                alteradas e o histórico é preservado.
              </>
            }
            confirmLabel="Inativar versão"
            cancelLabel="Voltar"
            variant="danger"
            confirmBusy={busy}
            confirmBusyLabel="Inativando…"
            onConfirm={confirmInactivate}
            onCancel={() => setInactivateTarget(null)}
            classNames={cfConfirmModalClassNames}
          />
        </CfDialog>
      ) : null}

      {discardTarget ? (
        <CfDialog
          open
          title={`Descartar v${discardTarget.version}`}
          onClose={() => !busy && setDiscardTarget(null)}
          closeAriaLabel="Fechar descarte"
        >
          <ConfirmModalPanel
            message={
              <>
                Descartar a versão rascunho v{discardTarget.version} e
                seus {discardTarget.item_count} itens? A ação remove o
                rascunho de forma definitiva e registra o descarte no
                histórico de auditoria. Versões publicadas não podem ser
                descartadas.
              </>
            }
            confirmLabel="Descartar rascunho"
            cancelLabel="Voltar"
            variant="danger"
            confirmBusy={busy}
            confirmBusyLabel="Descartando…"
            onConfirm={confirmDiscard}
            onCancel={() => setDiscardTarget(null)}
            classNames={cfConfirmModalClassNames}
          />
        </CfDialog>
      ) : null}

      {eventsTemplate ? (
        <CfDialog
          open
          title={`Eventos — ${eventsTemplate.code}`}
          onClose={() => setEventsTemplate(null)}
          closeAriaLabel="Fechar eventos"
        >
          {eventsError ? (
            <CfFeedbackMessage
              intent="error"
              title="Falha ao listar eventos"
            >
              {eventsError.message}
            </CfFeedbackMessage>
          ) : events === null ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Carregando eventos…"
            />
          ) : events.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhum evento registrado."
            />
          ) : (
            <CfTimeline
              items={events.map((event) => ({
                id: event.event_id,
                title:
                  EVENT_LABELS[event.event_type] ?? event.event_type,
                occurredAt: event.created_at,
                timeLabel: formatDateTime(event.created_at),
                detail: `v${event.version} · ${event.actor_subject}`,
                tone: EVENT_TONES[event.event_type] ?? "default",
              }))}
              emptyMessage="Nenhum evento registrado."
              aria-label={`Eventos de ${eventsTemplate.code}`}
            />
          )}
        </CfDialog>
      ) : null}

      {itemForm ? (
        <CfDialog
          open
          title={
            itemFormIndex !== null
              ? `Editar item ${itemForm.item_key}`
              : "Adicionar item"
          }
          onClose={() => setItemForm(null)}
          closeAriaLabel="Fechar item"
        >
          <div className="cf-validation-panel__form cf-form-grid">
            <CfTextField
              label="Chave do item"
              required
              value={itemForm.item_key}
              onChange={(value) =>
                setItemForm({ ...itemForm, item_key: value })
              }
            />
            <CfTextField
              label="Entregável"
              required
              value={itemForm.name}
              onChange={(value) =>
                setItemForm({ ...itemForm, name: value })
              }
            />
            <CfTextField
              label="Ordem"
              value={itemForm.sort_order?.toString() ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  sort_order:
                    value.trim() && !Number.isNaN(Number(value))
                      ? Number(value)
                      : null,
                })
              }
            />
            <CfSelectField
              label="Folha"
              options={SHEET_OPTIONS}
              value={itemForm.sheet}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  sheet: value as EditableItem["sheet"],
                })
              }
            />
            <CfSelectField
              label="Origem"
              options={ORIGIN_OPTIONS}
              value={itemForm.origin_kind}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  origin_kind: value as EditableItem["origin_kind"],
                })
              }
            />
            <CfSelectField
              label="Destinatário"
              options={RECIPIENT_OPTIONS}
              value={itemForm.recipient_area ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  recipient_area: (value ||
                    null) as EditableItem["recipient_area"],
                })
              }
            />
            <CfSelectField
              label="Obrigatoriedade"
              options={APPLICABILITY_OPTIONS}
              value={itemForm.applicability ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  applicability:
                    value as EditableItem["applicability"],
                })
              }
            />
            <CfSelectField
              label="Escopo de filial"
              options={BRANCH_OPTIONS}
              value={itemForm.branch_scope ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  branch_scope: value as EditableItem["branch_scope"],
                })
              }
            />
            <CfSelectField
              label="Regra de validação"
              options={SCOPE_OPTIONS}
              value={itemForm.validation_scope ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  validation_scope:
                    value as EditableItem["validation_scope"],
                })
              }
            />
            <CfTextField
              label="Relatório TOTVS (referência)"
              value={itemForm.totvs_report_ref ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  totvs_report_ref: value.slice(0, 8) || null,
                })
              }
            />
            <CfTextField
              label="Finalidade"
              value={itemForm.purpose ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  purpose: value || null,
                })
              }
            />
            <CfTextAreaField
              label="Requisitos e notas"
              rows={3}
              fullWidth
              value={itemForm.requirement_notes ?? ""}
              onChange={(value) =>
                setItemForm({
                  ...itemForm,
                  requirement_notes: value || null,
                })
              }
            />
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={!itemForm.item_key.trim() || !itemForm.name.trim()}
                onClick={submitItemForm}
              >
                Aplicar
              </ActionButton>
              <ActionButton
                variant="ghost"
                onClick={() => setItemForm(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}
    </section>
  );
}
