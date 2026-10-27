/**
 * Página completa de cadastro/edição de documento do fechamento — UX-012.
 *
 * Reutiliza o mesmo formulário para criar (`itemKey === "new"`) e editar
 * (`itemKey` existente). A gravação orquestra o contrato versionado da
 * BFF: a configuração vira uma nova versão publicada a partir da
 * competência informada e, quando há término, uma segunda versão de
 * remoção — sempre prospectivo, nunca reescreve snapshots encerrados.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ConfirmModalPanel } from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  getTemplateVersion,
  listChecklistTemplates,
  listTemplateEvents,
  listTemplateVersions,
  type ChecklistTemplateVersion,
  type TemplateAuditEvent,
} from "../../api/adminApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
  type CfQueryError,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfDialog,
  CfEmptyState,
  CfPagePath,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfConfirmModalClassNames,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";
import {
  PERIOD_PATTERN,
  SITUATION_LABELS,
  currentPeriod,
  deriveDocumentCatalog,
  formatPeriod,
  nextPeriod,
  catalogBaseVersion,
  endDocumentRequirement,
  saveDocumentConfig,
  slugifyItemKey,
  type VersionWithItems,
} from "./documentCatalog";
import { EVENT_LABELS } from "./ChecklistAdminPage";
import {
  documentsAdminListPath,
  toQueryError,
} from "./DocumentsAdminPage";

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
  { value: "", label: "Uso interno (não enviado a outra área)" },
  { value: "CONTABIL", label: "Contabilidade / DRE" },
  { value: "FISCAL", label: "Fiscal" },
];

const APPLICABILITY_OPTIONS = [
  { value: "REQUIRED", label: "Obrigatório" },
  { value: "CONDITIONAL", label: "Condicional" },
  { value: "OPTIONAL", label: "Opcional" },
];

const BRANCH_OPTIONS = [
  { value: "BOTH", label: "Matriz e filial" },
  { value: "MATRIX", label: "Somente matriz" },
  { value: "BRANCH", label: "Somente filial" },
];

const SCOPE_OPTIONS = [
  { value: "PER_ATTACHMENT", label: "Por anexo" },
  { value: "WHOLE_SET", label: "Conjunto completo" },
];

type FormState = {
  itemKey: string;
  itemKeyEdited: boolean;
  name: string;
  purpose: string;
  requirementNotes: string;
  originKind: string;
  recipientArea: string;
  applicability: string;
  branchScope: string;
  sheet: string;
  totvsReportRef: string;
  validationScope: string;
  effectiveFrom: string;
  effectiveUntil: string;
};

const DEFAULT_FORM: FormState = {
  itemKey: "",
  itemKeyEdited: false,
  name: "",
  purpose: "",
  requirementNotes: "",
  originKind: "EXTERNAL",
  recipientArea: "",
  applicability: "REQUIRED",
  branchScope: "BOTH",
  sheet: "ELETRONICO",
  totvsReportRef: "",
  validationScope: "PER_ATTACHMENT",
  effectiveFrom: "",
  effectiveUntil: "",
};

export function DocumentConfigFormPage({
  basePath,
  itemKey,
}: {
  basePath: string;
  itemKey: string;
}) {
  const isCreate = itemKey === "new";
  const [templateId, setTemplateId] = useState<string | null>(null);
  const [versionList, setVersionList] = useState<
    ChecklistTemplateVersion[] | null
  >(null);
  const [versions, setVersions] =
    useState<VersionWithItems[] | null>(null);
  const [events, setEvents] =
    useState<TemplateAuditEvent[] | null>(null);
  const [form, setForm] = useState<FormState>(() => ({
    ...DEFAULT_FORM,
    effectiveFrom: nextPeriod(currentPeriod()),
  }));
  const [fieldErrors, setFieldErrors] = useState<string[]>([]);
  const [error, setError] = useState<CfQueryError | null>(null);
  const [actionError, setActionError] =
    useState<CfQueryError | null>(null);
  const [busy, setBusy] = useState(false);
  const [nonce, setNonce] = useState(0);
  const [confirmEnd, setConfirmEnd] = useState(false);
  const [confirmEmpty, setConfirmEmpty] = useState(false);
  const pendingEmptyRef = useRef<"save" | "end" | null>(null);
  const idempotencyKeyRef = useRef<string | null>(null);

  const backToList = useCallback(
    (saved?: string) => {
      const params = new URLSearchParams(window.location.search);
      params.delete("saved");
      if (saved) params.set("saved", saved);
      const query = params.toString();
      navigatePluginPath(
        documentsAdminListPath(basePath, query ? `?${query}` : ""),
      );
    },
    [basePath],
  );

  useEffect(() => {
    const controller = new AbortController();
    listChecklistTemplates({ signal: controller.signal })
      .then(async (templates) => {
        const first = templates[0];
        if (!first) {
          throw new ApiError(
            404,
            "template_not_found",
            "template_not_found",
          );
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
        const eventList = isCreate
          ? []
          : await listTemplateEvents(first.template_id, undefined, {
              signal: controller.signal,
            });
        if (controller.signal.aborted) return;
        setTemplateId(first.template_id);
        setVersionList(versionList);
        setVersions(details);
        setEvents(eventList);
        if (!isCreate) {
          const containing = details
            .filter((v) =>
              v.items.some((item) => item.item_key === itemKey),
            )
            .sort((a, b) => b.version - a.version);
          const latest =
            containing.find((v) => v.status === "PUBLISHED") ??
            containing[0];
          const item = latest?.items.find(
            (entry) => entry.item_key === itemKey,
          );
          if (item) {
            const row = deriveDocumentCatalog(details).find(
              (entry) => entry.itemKey === itemKey,
            );
            const lastWindow =
              row?.windows[row.windows.length - 1] ?? null;
            setForm({
              itemKey: item.item_key,
              itemKeyEdited: true,
              name: item.name,
              purpose: item.purpose ?? "",
              requirementNotes: item.requirement_notes ?? "",
              originKind: item.origin_kind,
              recipientArea: item.recipient_area ?? "",
              applicability: item.applicability,
              branchScope: item.branch_scope,
              sheet: item.sheet,
              totvsReportRef: item.totvs_report_ref ?? "",
              validationScope: item.validation_scope,
              effectiveFrom: nextPeriod(currentPeriod()),
              effectiveUntil: lastWindow?.to ?? "",
            });
          }
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          toQueryError(
            err,
            "Não foi possível carregar a configuração do documento.",
          ),
        );
      });
    return () => controller.abort();
  }, [isCreate, itemKey, nonce]);

  const reload = useCallback(() => {
    setError(null);
    setVersions(null);
    setNonce((n) => n + 1);
  }, []);

  const loading = versions === null && !error;

  const catalogRow = useMemo(
    () =>
      isCreate
        ? undefined
        : deriveDocumentCatalog(versions ?? []).find(
            (row) => row.itemKey === itemKey,
          ),
    [versions, isCreate, itemKey],
  );

  const notFound =
    !isCreate && versions !== null && catalogRow === undefined;

  const documentEvents = useMemo(() => {
    if (isCreate || !events) return [];
    const containingVersions = new Set(
      (versions ?? [])
        .filter((v) =>
          v.items.some((item) => item.item_key === itemKey),
        )
        .map((v) => v.version),
    );
    return events.filter((event) =>
      containingVersions.has(event.version),
    );
  }, [events, versions, isCreate, itemKey]);

  const validate = useCallback((): string[] => {
    const problems: string[] = [];
    const key = isCreate ? slugifyItemKey(form.name) : form.itemKey;
    if (!form.name.trim()) {
      problems.push("Informe o nome do documento.");
    }
    if (!/^[A-Z0-9-]{1,32}$/.test(key)) {
      problems.push(
        "O identificador técnico precisa ter até 32 caracteres (letras, números e hífens).",
      );
    }
    if (!PERIOD_PATTERN.test(form.effectiveFrom)) {
      problems.push(
        "Informe a competência inicial no formato AAAA-MM.",
      );
    } else if (form.effectiveFrom < currentPeriod()) {
      problems.push(
        "A vigência inicial não pode ser uma competência passada.",
      );
    }
    if (form.effectiveUntil) {
      if (!PERIOD_PATTERN.test(form.effectiveUntil)) {
        problems.push(
          "Informe a competência final no formato AAAA-MM.",
        );
      } else if (form.effectiveUntil < form.effectiveFrom) {
        problems.push(
          "A competência final não pode ser anterior à inicial.",
        );
      }
    }
    if (form.totvsReportRef.length > 8) {
      problems.push(
        "A referência do relatório TOTVS aceita no máximo 8 caracteres.",
      );
    }
    return problems;
  }, [form, isCreate]);

  const runSave = useCallback(
    (allowEmpty: boolean) => {
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = crypto.randomUUID();
      }
      const key = isCreate ? slugifyItemKey(form.name) : form.itemKey;
      saveDocumentConfig(
        templateId!,
        {
          itemKey: key,
          name: form.name.trim(),
          purpose: form.purpose.trim() || null,
          originKind: form.originKind as never,
          recipientArea: (form.recipientArea || null) as never,
          applicability: form.applicability as never,
          sheet: form.sheet as never,
          branchScope: form.branchScope as never,
          totvsReportRef: form.totvsReportRef.trim() || null,
          requirementNotes: form.requirementNotes.trim() || null,
          validationScope: form.validationScope as never,
        },
        form.effectiveFrom,
        form.effectiveUntil || null,
        {
          baseVersion: catalogBaseVersion(versionList ?? []),
          idempotencyKey: idempotencyKeyRef.current,
          allowEmpty,
        },
      )
        .then(() => {
          idempotencyKeyRef.current = null;
          backToList(key);
        })
        .catch((err: unknown) => {
          if (
            !allowEmpty &&
            err instanceof ApiError &&
            err.code === "empty_resulting_checklist"
          ) {
            // DR-2 — esvaziar o checklist exige confirmação explícita.
            // A intenção muda o payload: retry usa NOVA chave (a anterior
            // divergiria em idempotency_conflict).
            pendingEmptyRef.current = "save";
            idempotencyKeyRef.current = null;
            setConfirmEmpty(true);
            setBusy(false);
            return;
          }
          setActionError(
            toQueryError(
              err,
              "Não foi possível salvar a configuração do documento.",
            ),
          );
          setBusy(false);
        });
    },
    [isCreate, form, templateId, versionList, backToList],
  );

  const submit = useCallback(() => {
    const problems = validate();
    setFieldErrors(problems);
    if (problems.length > 0 || !templateId || busy) return;
    setBusy(true);
    setActionError(null);
    runSave(false);
  }, [validate, templateId, busy, runSave]);

  const runEndRequirement = useCallback(
    (allowEmpty: boolean) => {
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = crypto.randomUUID();
      }
      endDocumentRequirement(
        templateId!,
        itemKey,
        nextPeriod(currentPeriod()),
        {
          baseVersion: catalogBaseVersion(versionList ?? []),
          idempotencyKey: idempotencyKeyRef.current,
          allowEmpty,
        },
      )
        .then(() => {
          idempotencyKeyRef.current = null;
          setConfirmEnd(false);
          backToList(itemKey);
        })
        .catch((err: unknown) => {
          if (
            !allowEmpty &&
            err instanceof ApiError &&
            err.code === "empty_resulting_checklist"
          ) {
            pendingEmptyRef.current = "end";
            idempotencyKeyRef.current = null;
            setConfirmEnd(false);
            setConfirmEmpty(true);
            setBusy(false);
            return;
          }
          setActionError(
            toQueryError(
              err,
              "Não foi possível encerrar a exigência do documento.",
            ),
          );
          setBusy(false);
        });
    },
    [templateId, itemKey, versionList, backToList],
  );

  const confirmEndRequirement = useCallback(() => {
    if (!templateId || busy) return;
    setBusy(true);
    setActionError(null);
    runEndRequirement(false);
  }, [templateId, busy, runEndRequirement]);

  const confirmEmptyChecklist = useCallback(() => {
    const kind = pendingEmptyRef.current;
    pendingEmptyRef.current = null;
    setConfirmEmpty(false);
    if (kind) {
      setBusy(true);
      setActionError(null);
      if (kind === "save") runSave(true);
      else runEndRequirement(true);
    }
  }, [runSave, runEndRequirement]);

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label={
        isCreate ? "Novo documento" : `Editar documento ${itemKey}`
      }
    >
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={{
          label: "Documentos do fechamento",
          href: documentsAdminListPath(
            basePath,
            window.location.search,
          ),
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            backToList();
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
          {
            id: "documents",
            label: "Documentos do fechamento",
            href: documentsAdminListPath(basePath),
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              backToList();
            },
          },
        ]}
        current={isCreate ? "Novo documento" : `Editar — ${itemKey}`}
      />

      <div className="cf-checklist-page__content">
        <CfTitleWithHelp
          title={isCreate ? "Novo documento" : "Editar documento"}
          hint={
            isCreate
              ? CF_HELP.documentsAdmin.formNew
              : CF_HELP.documentsAdmin.formEdit
          }
        />

        {actionError ? (
          <CfFeedbackMessage intent="error" title="Ação não concluída">
            {actionError.message}
            {actionError.code === "stale_revision" ? (
              <>
                {" "}
                <button
                  type="button"
                  className="cf-link-button"
                  onClick={() => {
                    setActionError(null);
                    reload();
                  }}
                >
                  Recarregar configuração
                </button>
              </>
            ) : null}
          </CfFeedbackMessage>
        ) : null}

        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="a configuração do documento"
            onRetry={() => reload()}
          />
        ) : loading ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Carregando configuração…"
          />
        ) : notFound ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Documento não encontrado no catálogo — ele pode ter sido removido ou a chave está incorreta."
          />
        ) : (
          <>
            {catalogRow?.pendingInDraft ? (
              <CfFeedbackMessage
                intent="warning"
                title="Rascunho aberto"
              >
                Existe uma versão em rascunho ou revisão contendo este
                documento. O salvamento só é aceito depois que ela for
                publicada ou descartada na Administração do checklist.
              </CfFeedbackMessage>
            ) : null}

            {!isCreate && catalogRow ? (
              <CfSectionCard title="Situação atual">
                <ul className="cf-validation-panel__docs">
                  <li className="cf-validation-panel__doc">
                    <div>
                      <p className="cf-validation-panel__doc-name">
                        {catalogRow.itemKey}
                        {" · "}
                        <CfStatusBadge
                          variant={
                            catalogRow.situation === "vigente"
                              ? "success"
                              : catalogRow.situation === "futuro"
                                ? "info"
                                : "neutral"
                          }
                          label={SITUATION_LABELS[catalogRow.situation]}
                        />
                      </p>
                      <p className="cf-validation-panel__doc-detail">
                        {catalogRow.windows.length === 0
                          ? "Ainda não publicado em nenhuma versão."
                          : catalogRow.windows
                              .map(
                                (window) =>
                                  `${formatPeriod(window.from)} → ${
                                    window.to
                                      ? formatPeriod(window.to)
                                      : "sem término"
                                  }`,
                              )
                              .join(" · ")}
                      </p>
                    </div>
                  </li>
                </ul>
              </CfSectionCard>
            ) : null}

            <CfSectionCard title="Identificação">
              <div className="cf-validation-panel__form">
                <label>
                  Nome do documento *
                  <input
                    value={form.name}
                    disabled={busy}
                    onChange={(event) => {
                      const name = event.target.value;
                      setForm({
                        ...form,
                        name,
                        itemKey: form.itemKeyEdited
                          ? form.itemKey
                          : slugifyItemKey(name),
                      });
                    }}
                  />
                </label>
                <label>
                  Descrição / finalidade
                  <textarea
                    rows={2}
                    value={form.purpose}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({ ...form, purpose: event.target.value })
                    }
                  />
                </label>
                <label>
                  Orientações de preparação
                  <textarea
                    rows={2}
                    value={form.requirementNotes}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        requirementNotes: event.target.value,
                      })
                    }
                  />
                </label>
                {isCreate ? (
                  <label>
                    Identificador técnico
                    <input
                      value={form.itemKey}
                      disabled={busy}
                      maxLength={32}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          itemKey: event.target.value.toUpperCase(),
                          itemKeyEdited: true,
                        })
                      }
                    />
                  </label>
                ) : null}
              </div>
            </CfSectionCard>

            <CfSectionCard title="Exigência">
              <div className="cf-validation-panel__form">
                <label>
                  Obrigatoriedade
                  <select
                    value={form.applicability}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        applicability: event.target.value,
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
                  Destino
                  <select
                    value={form.recipientArea}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        recipientArea: event.target.value,
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
                  Origem
                  <select
                    value={form.originKind}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        originKind: event.target.value,
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
                  Via
                  <select
                    value={form.sheet}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({ ...form, sheet: event.target.value })
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
                  Escopo de filial
                  <select
                    value={form.branchScope}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        branchScope: event.target.value,
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
                    value={form.validationScope}
                    disabled={busy}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        validationScope: event.target.value,
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
                  Referência do relatório TOTVS (R-ID)
                  <input
                    value={form.totvsReportRef}
                    disabled={busy}
                    maxLength={8}
                    placeholder="Ex.: FINR190"
                    onChange={(event) =>
                      setForm({
                        ...form,
                        totvsReportRef: event.target.value,
                      })
                    }
                  />
                </label>
              </div>
            </CfSectionCard>

            <CfSectionCard
              title="Vigência"
              hint={CF_HELP.documentsAdmin.validity}
            >
              <div className="cf-validation-panel__form">
                <p className="cf-validation-panel__doc-detail">
                  A vigência é prospectiva: a exigência passa a valer para
                  competências abertas a partir da competência inicial.
                  Fechamentos já abertos ou encerrados não são alterados —
                  se a janela alcançar uma competência aberta, a publicação
                  é recusada.
                </p>
                <label>
                  Exigido a partir de (AAAA-MM) *
                  <input
                    type="month"
                    value={form.effectiveFrom}
                    disabled={busy}
                    min={currentPeriod()}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        effectiveFrom: event.target.value,
                      })
                    }
                  />
                </label>
                <label>
                  Exigido até (AAAA-MM, opcional)
                  <input
                    type="month"
                    value={form.effectiveUntil}
                    disabled={busy}
                    min={form.effectiveFrom || currentPeriod()}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        effectiveUntil: event.target.value,
                      })
                    }
                  />
                </label>
                {form.effectiveUntil ? (
                  <p className="cf-validation-panel__doc-detail">
                    Exigência temporária: o documento deixa de ser
                    exigido a partir de{" "}
                    {formatPeriod(nextPeriod(form.effectiveUntil))}.
                  </p>
                ) : null}
              </div>
            </CfSectionCard>

            {fieldErrors.length > 0 ? (
              <CfFeedbackMessage
                intent="warning"
                title="Revise os campos"
              >
                {fieldErrors.join(" ")}
              </CfFeedbackMessage>
            ) : null}

            <div className="cf-validation-panel__item-actions">
              <CfActionButton
                type="button"
                disabled={busy}
                onClick={submit}
              >
                {busy
                  ? "Salvando…"
                  : isCreate
                    ? "Salvar documento"
                    : "Salvar alterações"}
              </CfActionButton>
              <CfActionButton
                type="button"
                variant="ghost"
                disabled={busy}
                onClick={() => backToList()}
              >
                Cancelar e voltar
              </CfActionButton>
              {!isCreate &&
              catalogRow &&
              catalogRow.situation !== "encerrado" ? (
                <CfActionButton
                  type="button"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => setConfirmEnd(true)}
                >
                  Encerrar exigência
                </CfActionButton>
              ) : null}
            </div>

            {!isCreate ? (
              <CfSectionCard
                title="Histórico de alterações"
                hint={CF_HELP.documentsAdmin.history}
              >
                {events === null ? (
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Carregando histórico…"
                  />
                ) : documentEvents.length === 0 ? (
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Nenhum evento registrado para este documento."
                  />
                ) : (
                  <ul className="cf-validation-panel__docs">
                    {documentEvents.map((event) => (
                      <li
                        key={event.event_id}
                        className="cf-validation-panel__doc"
                      >
                        <div>
                          <p className="cf-validation-panel__doc-name">
                            {EVENT_LABELS[event.event_type] ??
                              event.event_type}
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
              </CfSectionCard>
            ) : null}
          </>
        )}
      </div>

      {confirmEnd ? (
        <CfDialog
          open
          title="Encerrar exigência"
          onClose={() => !busy && setConfirmEnd(false)}
          closeAriaLabel="Fechar confirmação"
        >
          <ConfirmModalPanel
            message={
              <>
                Encerrar a exigência de «{form.name || itemKey}» a partir
                da próxima competência? A ação é prospectiva: fechamentos
                abertos e encerrados não são alterados, e o histórico é
                preservado — o documento não é excluído.
              </>
            }
            confirmLabel="Encerrar exigência"
            cancelLabel="Voltar"
            variant="danger"
            confirmBusy={busy}
            confirmBusyLabel="Encerrando…"
            onConfirm={confirmEndRequirement}
            onCancel={() => setConfirmEnd(false)}
            classNames={cfConfirmModalClassNames}
          />
        </CfDialog>
      ) : null}

      {confirmEmpty ? (
        <CfDialog
          open
          title="Checklist sem documentos"
          onClose={() => !busy && setConfirmEmpty(false)}
          closeAriaLabel="Fechar confirmação"
        >
          <ConfirmModalPanel
            message={
              <>
                Esta alteração deixará o checklist de fechamento sem
                nenhum documento exigido nas competências futuras.
                Fechamentos já abertos não são alterados. Confirmar a
                publicação do checklist vazio?
              </>
            }
            confirmLabel="Publicar checklist vazio"
            cancelLabel="Voltar"
            variant="danger"
            confirmBusy={busy}
            confirmBusyLabel="Publicando…"
            onConfirm={confirmEmptyChecklist}
            onCancel={() => setConfirmEmpty(false)}
            classNames={cfConfirmModalClassNames}
          />
        </CfDialog>
      ) : null}
    </section>
  );
}
