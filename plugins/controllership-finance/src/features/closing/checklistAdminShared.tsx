/**
 * Núcleo compartilhado da administração do checklist mestre (P6/A3,
 * UX-015): constantes de estado/evento, mapeamento de erros e as
 * ações governadas de versão (revisão, publicação prospectiva,
 * devolução, inativação e descarte) usadas pela página de
 * Administração e pela página contextual de cada versão.
 *
 * O backend é a única autoridade de permissão e ciclo de vida — estes
 * componentes apenas renderizam e encaminham. Edição de DRAFT é
 * atômica com OCC `revision`; `stale_revision` pede recarga.
 */
import { useCallback, useMemo, useState } from "react";

import {
  ActionButton,
  ConfirmModalPanel,
  HelpTooltip,
} from "@delpi/plugin-ui/index";
import {
  Archive,
  Send,
  Trash2,
  Undo2,
  Upload,
} from "lucide-react";

import { ApiError } from "../../api/httpClient";
import { CatalogSaveError } from "./documentCatalog";
import {
  discardTemplateVersion,
  inactivateTemplateVersion,
  publishTemplateVersion,
  returnVersionToDraft,
  submitVersionForReview,
  type ChecklistTemplateItem,
  type ChecklistTemplateVersion,
  type DraftItemInput,
} from "../../api/adminApi";
import {
  CfDateField,
  CfDialog,
  CfSelectField,
  CfTextAreaField,
  CfTextField,
  cfConfirmModalClassNames,
} from "../../app/controllershipFinanceUi";

export type QueryError = {
  status: number;
  code: string | null;
  message: string;
};

/**
 * Rótulo de indicador com ajuda contextual — mesmo padrão do
 * `headerHint` das colunas (HelpTooltip acessível do kit).
 */
export function hintedLabel(label: string, content: string) {
  return (
    <HelpTooltip
      content={content}
      ariaLabel={`Ajuda: ${label}`}
      wrap
      placement="bottom"
    >
      <span className="delpi-ui-section-hint-label">{label}</span>
    </HelpTooltip>
  );
}

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

export function toQueryError(
  error: unknown,
  fallback: string,
): QueryError {
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

export const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Rascunho",
  REVIEW: "Em revisão",
  PUBLISHED: "Publicada",
  INACTIVE: "Inativada",
};

export const STATUS_VARIANTS: Record<
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

export const SHEET_OPTIONS = [
  { value: "ELETRONICO", label: "Eletrônico" },
  { value: "FISICO", label: "Físico" },
];

export const ORIGIN_OPTIONS = [
  { value: "TOTVS", label: "ERP TOTVS" },
  { value: "EXTERNAL", label: "Fonte externa" },
  { value: "MIXED", label: "Origem mista" },
];

export const RECIPIENT_OPTIONS = [
  { value: "", label: "A definir" },
  { value: "CONTABIL", label: "Contábil" },
  { value: "FISCAL", label: "Fiscal" },
];

export const APPLICABILITY_OPTIONS = [
  { value: "REQUIRED", label: "Obrigatório" },
  { value: "CONDITIONAL", label: "Condicional" },
  { value: "OPTIONAL", label: "Opcional" },
];

export const BRANCH_OPTIONS = [
  { value: "MATRIX", label: "Matriz" },
  { value: "BRANCH", label: "Filial" },
  { value: "BOTH", label: "Matriz e filiais" },
];

export const SCOPE_OPTIONS = [
  { value: "PER_ATTACHMENT", label: "Por anexo" },
  { value: "WHOLE_SET", label: "Conjunto" },
];

export function optionLabel(
  options: { value: string; label: string }[],
  value: string | null | undefined,
): string {
  if (value === null || value === undefined) return "A definir";
  return options.find((o) => o.value === value)?.label ?? value;
}

export type EditableItem = DraftItemInput & { item_id?: string };

export function toDraftInput(
  item: ChecklistTemplateItem,
): EditableItem {
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

export const EMPTY_ITEM: EditableItem = {
  item_key: "",
  sheet: "ELETRONICO",
  name: "",
  origin_kind: "EXTERNAL",
  recipient_area: null,
  applicability: "REQUIRED",
  branch_scope: "BOTH",
  validation_scope: "PER_ATTACHMENT",
};

export type VersionActions = {
  busy: boolean;
  actionError: QueryError | null;
  /** Executa operação administrativa com busy/error padronizados. */
  run: (work: () => Promise<unknown>, onDone?: () => void) => void;
  askSubmitReview: (row: ChecklistTemplateVersion) => void;
  askPublish: (row: ChecklistTemplateVersion) => void;
  askReturn: (row: ChecklistTemplateVersion) => void;
  askInactivate: (row: ChecklistTemplateVersion) => void;
  askDiscard: (row: ChecklistTemplateVersion) => void;
  /** Diálogos de confirmação/parâmetros — renderizar no fim da página. */
  dialogs: React.ReactNode;
};

/**
 * Ações governadas de versão compartilhadas entre a listagem da
 * Administração e a página contextual da versão. `onDone` roda após
 * cada operação bem-sucedida (recarga); `onDiscarded` roda quando a
 * versão deixa de existir (a página da versão navega de volta).
 */
export function useChecklistVersionActions(args: {
  templateId: string | null;
  onDone: () => void;
  onDiscarded?: () => void;
}): VersionActions {
  const { templateId, onDone, onDiscarded } = args;
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<QueryError | null>(
    null,
  );

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

  const run = useCallback(
    (work: () => Promise<unknown>, done?: () => void) => {
      setBusy(true);
      setActionError(null);
      work()
        .then(() => {
          setBusy(false);
          done?.();
          onDone();
        })
        .catch((err: unknown) => {
          setBusy(false);
          setActionError(
            toQueryError(err, "A ação não pôde ser concluída."),
          );
        });
    },
    [onDone],
  );

  const askSubmitReview = useCallback(
    (row: ChecklistTemplateVersion) => {
      if (!templateId) return;
      run(() => submitVersionForReview(templateId, row.version));
    },
    [templateId, run],
  );

  const askPublish = useCallback((row: ChecklistTemplateVersion) => {
    setPublishTarget(row);
    setPublishPeriod("");
  }, []);

  const askReturn = useCallback((row: ChecklistTemplateVersion) => {
    setReturnTarget(row);
    setReturnReason("");
  }, []);

  const askInactivate = useCallback((row: ChecklistTemplateVersion) => {
    setInactivateTarget(row);
  }, []);

  const askDiscard = useCallback((row: ChecklistTemplateVersion) => {
    setDiscardTarget(row);
  }, []);

  const submitPublish = useCallback(() => {
    if (!templateId || !publishTarget || !publishPeriod) return;
    run(
      () =>
        publishTemplateVersion(templateId, publishTarget.version, {
          effective_from_period: publishPeriod,
        }),
      () => setPublishTarget(null),
    );
  }, [templateId, publishTarget, publishPeriod, run]);

  const submitReturn = useCallback(() => {
    if (!templateId || !returnTarget || !returnReason.trim()) return;
    run(
      () =>
        returnVersionToDraft(templateId, returnTarget.version, {
          reason: returnReason.trim(),
        }),
      () => {
        setReturnTarget(null);
        setReturnReason("");
      },
    );
  }, [templateId, returnTarget, returnReason, run]);

  const confirmInactivate = useCallback(() => {
    if (!templateId || !inactivateTarget) return;
    run(
      () =>
        inactivateTemplateVersion(templateId, inactivateTarget.version),
      () => setInactivateTarget(null),
    );
  }, [templateId, inactivateTarget, run]);

  const confirmDiscard = useCallback(() => {
    if (!templateId || !discardTarget) return;
    run(
      () =>
        discardTemplateVersion(
          templateId,
          discardTarget.version,
          discardTarget.revision,
        ),
      () => {
        setDiscardTarget(null);
        onDiscarded?.();
      },
    );
  }, [templateId, discardTarget, run, onDiscarded]);

  const dialogs = useMemo(
    () => (
      <>
        {publishTarget ? (
          <CfDialog
            open
            title={`Publicar v${publishTarget.version}`}
            onClose={() => !busy && setPublishTarget(null)}
            closeAriaLabel="Fechar publicação"
          >
            <div className="cf-validation-panel__form">
              <p className="cf-validation-panel__doc-detail">
                A publicação é prospectiva: a versão passa a valer a
                partir da competência informada e não altera
                competências já abertas.
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
                  Inativar a versão v{inactivateTarget.version}? A ação
                  é prospectiva — competências abertas com esta versão
                  não são alteradas e o histórico é preservado.
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
                  histórico de auditoria. Versões publicadas não podem
                  ser descartadas.
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
      </>
    ),
    [
      publishTarget,
      publishPeriod,
      busy,
      submitPublish,
      returnTarget,
      returnReason,
      submitReturn,
      inactivateTarget,
      confirmInactivate,
      discardTarget,
      confirmDiscard,
    ],
  );

  return {
    busy,
    actionError,
    run,
    askSubmitReview,
    askPublish,
    askReturn,
    askInactivate,
    askDiscard,
    dialogs,
  };
}

/** Ícones semânticos das ações de ciclo de vida (UX-016, hero). */
const VERSION_ACTION_ICON_PROPS = {
  size: 15,
  strokeWidth: 1.9,
  "aria-hidden": true,
} as const;

/** Botões de estado permitidos para uma versão (detalhe da versão). */
export function VersionStatusActions(props: {
  version: ChecklistTemplateVersion;
  busy: boolean;
  actions: VersionActions;
}) {
  const { version, busy, actions } = props;
  return (
    <>
      {version.status === "DRAFT" ? (
        <>
          <ActionButton
            variant="ghost"
            disabled={busy}
            onClick={() => actions.askSubmitReview(version)}
          >
            <Send {...VERSION_ACTION_ICON_PROPS} />
            Enviar para revisão
          </ActionButton>
          <ActionButton
            variant="ghost"
            className="cf-action-btn--danger"
            disabled={busy}
            onClick={() => actions.askDiscard(version)}
          >
            <Trash2 {...VERSION_ACTION_ICON_PROPS} />
            Descartar
          </ActionButton>
        </>
      ) : null}
      {version.status === "REVIEW" ? (
        <>
          <ActionButton
            variant="ghost"
            disabled={busy}
            onClick={() => actions.askPublish(version)}
          >
            <Upload {...VERSION_ACTION_ICON_PROPS} />
            Publicar
          </ActionButton>
          <ActionButton
            variant="ghost"
            disabled={busy}
            onClick={() => actions.askReturn(version)}
          >
            <Undo2 {...VERSION_ACTION_ICON_PROPS} />
            Devolver
          </ActionButton>
        </>
      ) : null}
      {version.status === "PUBLISHED" ? (
        <ActionButton
          variant="ghost"
          className="cf-action-btn--danger"
          disabled={busy}
          onClick={() => actions.askInactivate(version)}
        >
          <Archive {...VERSION_ACTION_ICON_PROPS} />
          Inativar
        </ActionButton>
      ) : null}
    </>
  );
}

/** Diálogo de edição de item de rascunho (página da versão). */
export function ChecklistItemFormDialog(props: {
  item: EditableItem;
  isNew: boolean;
  onChange: (item: EditableItem) => void;
  onSubmit: () => void;
  onClose: () => void;
}) {
  const { item, isNew, onChange, onSubmit, onClose } = props;
  return (
    <CfDialog
      open
      title={isNew ? "Adicionar item" : `Editar item ${item.item_key}`}
      onClose={onClose}
      closeAriaLabel="Fechar item"
    >
      <div className="cf-validation-panel__form cf-form-grid">
        <CfTextField
          label="Chave do item"
          required
          value={item.item_key}
          onChange={(value) => onChange({ ...item, item_key: value })}
        />
        <CfTextField
          label="Entregável"
          required
          value={item.name}
          onChange={(value) => onChange({ ...item, name: value })}
        />
        <CfTextField
          label="Ordem"
          value={item.sort_order?.toString() ?? ""}
          onChange={(value) =>
            onChange({
              ...item,
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
          value={item.sheet}
          onChange={(value) =>
            onChange({ ...item, sheet: value as EditableItem["sheet"] })
          }
        />
        <CfSelectField
          label="Origem"
          options={ORIGIN_OPTIONS}
          value={item.origin_kind}
          onChange={(value) =>
            onChange({
              ...item,
              origin_kind: value as EditableItem["origin_kind"],
            })
          }
        />
        <CfSelectField
          label="Destinatário"
          options={RECIPIENT_OPTIONS}
          value={item.recipient_area ?? ""}
          onChange={(value) =>
            onChange({
              ...item,
              recipient_area: (value ||
                null) as EditableItem["recipient_area"],
            })
          }
        />
        <CfSelectField
          label="Obrigatoriedade"
          options={APPLICABILITY_OPTIONS}
          value={item.applicability ?? ""}
          onChange={(value) =>
            onChange({
              ...item,
              applicability: value as EditableItem["applicability"],
            })
          }
        />
        <CfSelectField
          label="Escopo de filial"
          options={BRANCH_OPTIONS}
          value={item.branch_scope ?? ""}
          onChange={(value) =>
            onChange({
              ...item,
              branch_scope: value as EditableItem["branch_scope"],
            })
          }
        />
        <CfSelectField
          label="Regra de validação"
          options={SCOPE_OPTIONS}
          value={item.validation_scope ?? ""}
          onChange={(value) =>
            onChange({
              ...item,
              validation_scope:
                value as EditableItem["validation_scope"],
            })
          }
        />
        <CfTextField
          label="Relatório TOTVS (referência)"
          value={item.totvs_report_ref ?? ""}
          onChange={(value) =>
            onChange({
              ...item,
              totvs_report_ref: value.slice(0, 8) || null,
            })
          }
        />
        <CfTextField
          label="Finalidade"
          value={item.purpose ?? ""}
          onChange={(value) =>
            onChange({ ...item, purpose: value || null })
          }
        />
        <CfTextAreaField
          label="Requisitos e notas"
          rows={3}
          fullWidth
          value={item.requirement_notes ?? ""}
          onChange={(value) =>
            onChange({ ...item, requirement_notes: value || null })
          }
        />
        <div className="cf-validation-panel__form-actions">
          <ActionButton
            variant="primary"
            disabled={!item.item_key.trim() || !item.name.trim()}
            onClick={onSubmit}
          >
            Aplicar
          </ActionButton>
          <ActionButton variant="ghost" onClick={onClose}>
            Voltar
          </ActionButton>
        </div>
      </div>
    </CfDialog>
  );
}
