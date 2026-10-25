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
import {
  createTemplateDraft,
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
  CfDialog,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfConfirmModalClassNames,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { DataTableSection, type DataTableColumn } from "../../app/cfDataTableUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

type QueryError = { status: number; code: string | null; message: string };

const ERROR_MESSAGES: Record<string, string> = {
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
};

const EVENT_LABELS: Record<string, string> = {
  DRAFT_CREATED: "Rascunho criado",
  DRAFT_UPDATED: "Rascunho atualizado",
  VERSION_SUBMITTED_FOR_REVIEW: "Enviada a revisão",
  VERSION_RETURNED_TO_DRAFT: "Devolvida a rascunho",
  VERSION_PUBLISHED: "Versão publicada",
  VERSION_INACTIVATED: "Versão inativada",
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
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => confirmSubmitReview(row)}
              >
                Enviar para revisão
              </ActionButton>
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
              <div className="cf-validation-panel__item-actions">
                <CfActionButton
                  type="button"
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
            </CfSectionCard>

            {detailData ? (
              <CfSectionCard
                title={`Itens — v${detailData.version} (${STATUS_LABELS[detailData.status] ?? detailData.status})`}
                hint={
                  editing ? CF_HELP.admin.editDraft : CF_HELP.admin.items
                }
              >
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
            <label>
              Vigente a partir de (AAAA-MM)
              <input
                value={publishPeriod}
                disabled={busy}
                placeholder="2026-06"
                onChange={(event) => setPublishPeriod(event.target.value)}
              />
            </label>
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
            <label>
              Motivo da devolução
              <textarea
                rows={3}
                value={returnReason}
                disabled={busy}
                onChange={(event) =>
                  setReturnReason(event.target.value)
                }
              />
            </label>
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
            <ul className="cf-validation-panel__docs">
              {events.map((event) => (
                <li
                  key={event.event_id}
                  className="cf-validation-panel__doc"
                >
                  <div>
                    <p className="cf-validation-panel__doc-name">
                      {EVENT_LABELS[event.event_type] ?? event.event_type}
                      {" · "}
                      v{event.version}
                    </p>
                    <p className="cf-validation-panel__doc-detail">
                      {event.actor_subject} ·{" "}
                      {formatDateTime(event.created_at)}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
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
          <div className="cf-validation-panel__form">
            <label>
              Chave do item
              <input
                value={itemForm.item_key}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    item_key: event.target.value,
                  })
                }
              />
            </label>
            <label>
              Entregável
              <input
                value={itemForm.name}
                onChange={(event) =>
                  setItemForm({ ...itemForm, name: event.target.value })
                }
              />
            </label>
            <label>
              Ordem
              <input
                value={itemForm.sort_order ?? ""}
                type="number"
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    sort_order: event.target.value
                      ? Number(event.target.value)
                      : null,
                  })
                }
              />
            </label>
            <label>
              Folha
              <select
                value={itemForm.sheet}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    sheet: event.target.value as EditableItem["sheet"],
                  })
                }
              >
                {SHEET_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Origem
              <select
                value={itemForm.origin_kind}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    origin_kind:
                      event.target.value as EditableItem["origin_kind"],
                  })
                }
              >
                {ORIGIN_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Destinatário
              <select
                value={itemForm.recipient_area ?? ""}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    recipient_area: (event.target.value ||
                      null) as EditableItem["recipient_area"],
                  })
                }
              >
                {RECIPIENT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Obrigatoriedade
              <select
                value={itemForm.applicability}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    applicability:
                      event.target.value as EditableItem["applicability"],
                  })
                }
              >
                {APPLICABILITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Escopo de filial
              <select
                value={itemForm.branch_scope}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    branch_scope:
                      event.target.value as EditableItem["branch_scope"],
                  })
                }
              >
                {BRANCH_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Regra de validação
              <select
                value={itemForm.validation_scope}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    validation_scope:
                      event.target.value as EditableItem["validation_scope"],
                  })
                }
              >
                {SCOPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Relatório TOTVS (referência)
              <input
                value={itemForm.totvs_report_ref ?? ""}
                maxLength={8}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    totvs_report_ref: event.target.value || null,
                  })
                }
              />
            </label>
            <label>
              Finalidade
              <input
                value={itemForm.purpose ?? ""}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    purpose: event.target.value || null,
                  })
                }
              />
            </label>
            <label>
              Requisitos e notas
              <textarea
                value={itemForm.requirement_notes ?? ""}
                rows={3}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    requirement_notes: event.target.value || null,
                  })
                }
              />
            </label>
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
