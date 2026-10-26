/**
 * Página de detalhe do documento — deep route contextual da aba
 * «Documentos e interações» (doc 112 §38 / Plano 113 §17.2).
 *
 * Três referências possíveis:
 * - `item:{item_key}` — documento exigido (slot do checklist): mostra o
 *   item, seus anexos (scope PER_ATTACHMENT permite vários), versões,
 *   decisões de validação reais («solicitações de ajuste») e histórico.
 * - `{document_id}` — documento adicional (`link_kind=competence`):
 *   prévia, versões, download e histórico do documento.
 * - `new` — anexação contextual de documento adicional (U1 sem
 *   `snapshot_item_id`): não cria exigência geral nem item fictício.
 *
 * Não existe contrato de conversa livre por documento — a coluna
 * «Interações» mostra decisões/correções reais ou estado vazio honesto;
 * nunca mensagens simuladas. `ATTACHED != VALIDATED`; uma resposta não
 * encerra solicitação automaticamente.
 */
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
} from "react";

import {
  FileDropzone,
  fileDropzoneBemClasses,
  FilePreviewView,
  useFilePreviewLoader,
} from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  getCompetenceItem,
  getItemValidation,
  type CompetenceChecklistItemDetail,
  type ItemValidation,
} from "../../api/competencesApi";
import {
  CLOSING_DOCUMENT_ACCEPT,
  downloadClosingDocument,
  getClosingDocument,
  listClosingDocuments,
  listDocumentEvents,
  listDocumentVersions,
  replaceClosingDocument,
  saveDocumentBlob,
  uploadClosingDocument,
  type ClosingDocument,
  type DocumentAuditEvent,
  type DocumentVersion,
} from "../../api/documentsApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  FilterInputField,
} from "../../app/cfFiltersUi";
import {
  CfActionButton,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";
import { REJECTION_REASON_LABELS } from "./ItemValidationPanel";

type PanelError = { status: number; code: string | null; message: string };

const DETAIL_ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para este documento.",
  document_not_found: "Documento não encontrado ou fora do escopo.",
  item_not_found: "Documento exigido não encontrado neste fechamento.",
  competence_not_opened: "O fechamento deste mês ainda não foi aberto.",
  file_too_large: "O arquivo excede o limite de 25 MB.",
  unsupported_media_type:
    "Formato não permitido. Use PDF, imagem, XLS, XLSX ou CSV.",
  empty_file: "O arquivo enviado está vazio.",
  invalid_file_content: "O conteúdo do arquivo não é válido.",
  stale_revision:
    "O documento foi alterado por outra pessoa. Os dados foram atualizados.",
  document_cancelled: "Este documento foi cancelado.",
};

function toPanelError(error: unknown, fallback: string): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code,
      message:
        (error.code && DETAIL_ERROR_MESSAGES[error.code]) || error.message,
    };
  }
  return { status: 0, code: null, message: fallback };
}

const EVENT_LABELS: Record<string, string> = {
  DOCUMENT_UPLOADED: "Arquivo anexado",
  VERSION_ADDED: "Nova versão enviada",
  DOCUMENT_CANCELLED: "Documento cancelado",
  DOCUMENT_DOWNLOADED: "Download",
};

const ITEM_STATE_LABELS: Record<string, string> = {
  EXPECTED: "Aguardando documento",
  ACCEPTED: "Conferido",
  NOT_APPLICABLE: "Não se aplica",
  CANCELLED: "Cancelado",
};

const ITEM_STATE_VARIANTS: Record<string, "warning" | "success" | "neutral"> =
  {
    EXPECTED: "warning",
    ACCEPTED: "success",
    NOT_APPLICABLE: "neutral",
    CANCELLED: "neutral",
  };

const DROPZONE_CLASSES = fileDropzoneBemClasses("cf", "detail-dropzone");

function formatBytes(value: number | null): string {
  if (value === null || value <= 0) return "";
  if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.ceil(value / 1024)} KB`;
}

function eventNote(event: DocumentAuditEvent): string {
  const parts: string[] = [];
  if (typeof event.detail.version_no === "number") {
    parts.push(`v${event.detail.version_no}`);
  }
  if (event.event_type === "DOCUMENT_DOWNLOADED") {
    const result = event.detail.result;
    parts.push(
      result === "AUTHORIZED"
        ? "autorizado"
        : result === "DENIED"
          ? "negado"
          : result === "FAILED"
            ? "falhou"
            : "",
    );
  }
  return parts.filter(Boolean).join(" · ");
}

type DetailResult =
  | {
      kind: "item";
      item: CompetenceChecklistItemDetail;
      documents: ClosingDocument[];
      validation: ItemValidation;
    }
  | { kind: "document"; document: ClosingDocument };

export function DocumentDetailPanel({
  period,
  documentRef,
  onBack,
  onOpenRef,
}: {
  period: string;
  documentRef: string;
  /** Volta à aba Documentos preservando contexto. */
  onBack: () => void;
  /** Navega a outra referência do detalhe (ex.: doc criado). */
  onOpenRef: (ref: string) => void;
}) {
  const [result, setResult] = useState<{
    key: string;
    data: DetailResult;
  } | null>(null);
  const [error, setError] = useState<{
    key: string;
    error: PanelError;
  } | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [versions, setVersions] = useState<{
    key: string;
    items: DocumentVersion[];
  } | null>(null);
  const [events, setEvents] = useState<{
    key: string;
    items: DocumentAuditEvent[];
  } | null>(null);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<{
    intent: "info" | "error" | "success";
    message: string;
  } | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const requestId = useRef(0);
  const replaceInputRef = useRef<HTMLInputElement>(null);

  const key = `detail:${period}:${documentRef}:${retryNonce}`;
  const isNew = documentRef === "new";
  const itemKey = documentRef.startsWith("item:")
    ? documentRef.slice(5)
    : null;

  const data = result?.key === key ? result.data : null;
  const currentError = error?.key === key ? error.error : null;
  const loading = !isNew && data === null && !currentError;

  // Documento selecionado (primeiro da lista quando não escolhido).
  const selectedDoc =
    data?.kind === "item"
      ? (data.documents.find((d) => d.document_id === selectedDocId) ??
        data.documents[0] ??
        null)
      : data?.kind === "document"
        ? data.document
        : null;

  const versionList =
    selectedDoc && versions?.key === selectedDoc.document_id
      ? versions.items
      : null;
  const eventList =
    selectedDoc && events?.key === selectedDoc.document_id
      ? events.items
      : null;

  const refresh = useCallback(() => setRetryNonce((n) => n + 1), []);

  useEffect(() => {
    if (isNew) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    const alive = () =>
      !controller.signal.aborted && requestId.current === id;

    async function load() {
      try {
        if (itemKey) {
          const item = await getCompetenceItem(period, itemKey, {
            signal: controller.signal,
          });
          const [docs, validation] = await Promise.all([
            listClosingDocuments(
              period,
              { snapshotItemId: item.snapshot_item_id },
              { signal: controller.signal },
            ),
            getItemValidation(period, itemKey, {
              signal: controller.signal,
            }),
          ]);
          if (!alive()) return;
          setResult({
            key,
            data: {
              kind: "item",
              item,
              documents: docs.documents.filter(
                (d) => d.state !== "CANCELLED",
              ),
              validation,
            },
          });
          setError(null);
        } else {
          const document = await getClosingDocument(period, documentRef, {
            signal: controller.signal,
          });
          if (!alive()) return;
          setResult({ key, data: { kind: "document", document } });
          setError(null);
        }
      } catch (err) {
        if (!alive()) return;
        setError({
          key,
          error: toPanelError(err, "Falha ao carregar o documento."),
        });
      }
    }
    void load();
    return () => controller.abort();
  }, [period, documentRef, itemKey, isNew, key]);

  // Versões e eventos do documento selecionado — a renderização confere
  // `key === document_id`, então dados do doc anterior nunca vazam.
  useEffect(() => {
    if (!selectedDoc) return;
    const docId = selectedDoc.document_id;
    const controller = new AbortController();
    Promise.all([
      listDocumentVersions(period, docId, { signal: controller.signal }),
      listDocumentEvents(period, docId, {}, { signal: controller.signal }),
    ])
      .then(([v, e]) => {
        if (controller.signal.aborted) return;
        setVersions({ key: docId, items: v });
        setEvents({ key: docId, items: e.events });
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setVersions({ key: docId, items: [] });
        setEvents({ key: docId, items: [] });
      });
    return () => controller.abort();
  }, [period, selectedDoc]);

  // Prévia via contrato de download autenticado (falha de prévia nunca
  // bloqueia o download).
  const preview = useFilePreviewLoader({
    source: selectedDoc
      ? () =>
          downloadClosingDocument(
            period,
            selectedDoc.document_id,
            selectedDoc.current_version_no,
          )
      : null,
    mimeType: selectedDoc?.mime_type ?? null,
    fileName: selectedDoc?.original_name ?? null,
    enabled: Boolean(selectedDoc),
  });

  const handleAttachFiles = useCallback(
    (files: File[]) => {
      const file = files[0];
      if (!file || uploading) return;
      setUploading(true);
      setFeedback(null);
      const idempotencyKey = crypto.randomUUID();
      uploadClosingDocument(period, {
        file,
        idempotencyKey,
        snapshotItemId:
          data?.kind === "item" ? data.item.snapshot_item_id : null,
        title:
          isNew
            ? newTitle || file.name
            : data?.kind === "item"
              ? data.item.name
              : null,
      })
        .then((document) => {
          setUploading(false);
          if (isNew) {
            onOpenRef(document.document_id);
          } else {
            setFeedback({
              intent: "success",
              message: "Arquivo anexado.",
            });
            refresh();
          }
        })
        .catch((err: unknown) => {
          setUploading(false);
          setFeedback({
            intent: "error",
            message: toPanelError(err, "Falha ao enviar o arquivo.")
              .message,
          });
        });
    },
    [period, uploading, data, isNew, newTitle, onOpenRef, refresh],
  );

  const handleReplaceFile = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0] ?? null;
      event.target.value = "";
      const doc = selectedDoc;
      if (!file || !doc) return;
      setUploading(true);
      setFeedback(null);
      replaceClosingDocument(period, doc.document_id, {
        file,
        revision: doc.revision,
        idempotencyKey: crypto.randomUUID(),
      })
        .then(() => {
          setUploading(false);
          setFeedback({
            intent: "success",
            message:
              "Nova versão enviada. A versão anterior foi preservada.",
          });
          refresh();
        })
        .catch((err: unknown) => {
          setUploading(false);
          setFeedback({
            intent: "error",
            message: toPanelError(err, "Falha ao enviar a nova versão.")
              .message,
          });
          if (err instanceof ApiError && err.code === "stale_revision") {
            refresh();
          }
        });
    },
    [period, selectedDoc, refresh],
  );

  const handleDownload = useCallback(() => {
    const doc = selectedDoc;
    if (!doc) return;
    downloadClosingDocument(period, doc.document_id, doc.current_version_no)
      .then((blob) =>
        saveDocumentBlob(blob, doc.original_name ?? "documento"),
      )
      .catch((err: unknown) => {
        setFeedback({
          intent: "error",
          message: toPanelError(err, "Falha ao baixar o arquivo.").message,
        });
      });
  }, [period, selectedDoc]);

  const title =
    isNew
      ? "Novo documento"
      : data?.kind === "item"
        ? data.item.name
        : (data?.document.title ?? data?.document.original_name ??
          "Documento");

  const statusBadge =
    data?.kind === "item" ? (
      <CfStatusBadge
        variant={ITEM_STATE_VARIANTS[data.item.state] ?? "neutral"}
        label={ITEM_STATE_LABELS[data.item.state] ?? data.item.state}
      />
    ) : data?.kind === "document" ? (
      <CfStatusBadge
        variant="info"
        label={
          data.document.state === "ATTACHED"
            ? "Arquivo enviado"
            : data.document.state === "SUPERSEDED"
              ? "Substituído"
              : data.document.state
        }
      />
    ) : null;

  const decisions =
    data?.kind === "item" ? data.validation.decisions : [];

  return (
    <div className="cf-document-detail">
      <div className="cf-document-detail__head">
        <CfActionButton variant="ghost" onClick={onBack}>
          ← Voltar aos documentos
        </CfActionButton>
        <div className="cf-document-detail__title">
          <strong>{title}</strong>
          <span className="cf-document-detail__meta">
            Referência {period}
            {data?.kind === "item" ? " · Exigido" : ""}
            {data?.kind === "document" ? " · Adicional" : ""}
          </span>
        </div>
        {statusBadge}
      </div>

      {currentError ? (
        <CfQueryErrorBanner
          error={currentError}
          dataset="o documento"
          onRetry={refresh}
        />
      ) : null}

      {loading ? <p aria-live="polite">Carregando documento…</p> : null}

      {feedback ? (
        <CfFeedbackMessage
          intent={feedback.intent}
          title={feedback.intent === "error" ? "Erro" : "Documento"}
        >
          {feedback.message}
        </CfFeedbackMessage>
      ) : null}

      {isNew ? (
        <CfSectionCard
          title="Documento adicional"
          hint={CF_HELP.monthlyClosing.additionalDocument}
        >
          <p>
            Anexado apenas a este fechamento — não cria exigência para
            outros meses.
          </p>
          <FilterInputField
            id="cf-new-document-title"
            label="Nome do documento"
            type="text"
            value={newTitle}
            onChange={setNewTitle}
          />
          <FileDropzone
            classNames={DROPZONE_CLASSES}
            labels={{
              title: "Arraste o arquivo ou clique para selecionar",
              hint: "PDF, imagem, XLS, XLSX ou CSV · máx. 25 MB",
            }}
            accept={CLOSING_DOCUMENT_ACCEPT}
            multiple={false}
            busy={uploading}
            onFilesSelected={handleAttachFiles}
            ariaLabel="Anexar documento adicional"
          />
        </CfSectionCard>
      ) : data ? (
        <>
          <div className="cf-document-detail__columns">
            <CfSectionCard
              title="Documento"
              hint={CF_HELP.monthlyClosing.detailFile}
            >
              {data.kind === "item" && data.documents.length > 1 ? (
                <ul className="cf-document-detail__doclist">
                  {data.documents.map((doc) => (
                    <li key={doc.document_id}>
                      <button
                        type="button"
                        className="cf-document-detail__docpick"
                        aria-pressed={
                          doc.document_id === selectedDoc?.document_id
                        }
                        onClick={() =>
                          setSelectedDocId(doc.document_id)
                        }
                      >
                        {doc.original_name ?? doc.title ?? "Anexo"}
                        {` · v${doc.current_version_no}`}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}

              {selectedDoc ? (
                <>
                  <FilePreviewView
                    state={preview}
                    title={selectedDoc.original_name ?? title}
                  />
                  <p className="cf-document-detail__meta">
                    {selectedDoc.original_name ?? "arquivo"}
                    {selectedDoc.size_bytes
                      ? ` · ${formatBytes(selectedDoc.size_bytes)}`
                      : ""}
                    {` · v${selectedDoc.current_version_no}`}
                    {selectedDoc.uploaded_by
                      ? ` · ${selectedDoc.uploaded_by}`
                      : ""}
                  </p>
                  {versionList && versionList.length > 1 ? (
                    <ul className="cf-document-detail__versions">
                      {versionList.map((version) => (
                        <li key={version.document_version_id}>
                          v{version.version_no} —{" "}
                          {version.state === "ATTACHED"
                            ? "atual"
                            : "substituída"}
                          {version.created_at
                            ? ` · ${formatDateTime(version.created_at)}`
                            : ""}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  <div className="cf-settlements-actions">
                    <CfActionButton
                      variant="ghost"
                      onClick={handleDownload}
                    >
                      Baixar
                    </CfActionButton>
                    <CfActionButton
                      variant="ghost"
                      disabled={uploading}
                      onClick={() => replaceInputRef.current?.click()}
                    >
                      {uploading ? "Enviando…" : "Enviar nova versão"}
                    </CfActionButton>
                  </div>
                  <input
                    ref={replaceInputRef}
                    type="file"
                    accept={CLOSING_DOCUMENT_ACCEPT}
                    style={{ display: "none" }}
                    tabIndex={-1}
                    aria-hidden="true"
                    onChange={handleReplaceFile}
                  />
                </>
              ) : (
                <>
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Nenhum arquivo anexado ainda."
                  />
                  <FileDropzone
                    classNames={DROPZONE_CLASSES}
                    labels={{
                      title:
                        "Arraste o arquivo ou clique para selecionar",
                      hint: "PDF, imagem, XLS, XLSX ou CSV · máx. 25 MB",
                    }}
                    accept={CLOSING_DOCUMENT_ACCEPT}
                    multiple={false}
                    busy={uploading}
                    onFilesSelected={handleAttachFiles}
                    ariaLabel="Anexar arquivo ao documento"
                  />
                </>
              )}
            </CfSectionCard>

            <CfSectionCard
              title="Interações"
              hint={CF_HELP.monthlyClosing.detailInteractions}
            >
              {decisions.length === 0 ? (
                <CfEmptyState
                  classNames={cfEmptyStateClassNames}
                  defaultMessage="Nenhuma solicitação registrada neste documento."
                />
              ) : (
                <ul
                  className="cf-document-detail__interactions"
                  aria-label="Solicitações e decisões"
                >
                  {decisions.map((decision) => (
                    <li key={decision.decision_id}>
                      <strong>
                        {decision.decision === "REJECTED"
                          ? "Ajuste solicitado"
                          : decision.decision === "ACCEPTED"
                            ? "Documento conferido"
                            : "Decisão revertida"}
                      </strong>
                      {decision.reason_code
                        ? ` — ${
                            REJECTION_REASON_LABELS[decision.reason_code] ??
                            decision.reason_code
                          }`
                        : ""}
                      {decision.comment ? ` · ${decision.comment}` : ""}
                      <span className="cf-request-list__meta">
                        {" "}
                        · {decision.decided_by}
                        {decision.created_at
                          ? ` · ${formatDateTime(decision.created_at)}`
                          : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <p className="cf-document-detail__meta">
                A conversa livre por documento ainda não está disponível —
                as decisões registradas aparecem acima.
              </p>
            </CfSectionCard>
          </div>

          <CfSectionCard
            title="Histórico"
            hint={CF_HELP.monthlyClosing.detailHistory}
          >
            {selectedDoc && eventList && eventList.length > 0 ? (
              <ul
                className="cf-document-detail__history"
                aria-label="Histórico do documento"
              >
                {eventList.map((event) => (
                  <li key={event.event_id}>
                    <strong>
                      {EVENT_LABELS[event.event_type] ?? event.event_type}
                    </strong>
                    {eventNote(event) ? ` — ${eventNote(event)}` : ""}
                    <span className="cf-request-list__meta">
                      {" "}
                      · {event.actor_subject}
                      {event.created_at
                        ? ` · ${formatDateTime(event.created_at)}`
                        : ""}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <CfEmptyState
                classNames={cfEmptyStateClassNames}
                defaultMessage="Nenhum registro de histórico neste documento."
              />
            )}
          </CfSectionCard>
        </>
      ) : null}
    </div>
  );
}
