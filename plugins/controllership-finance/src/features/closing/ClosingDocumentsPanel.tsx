/**
 * Evidências documentais da competência — P2-Upload (SLICE-1 + SLICE-2).
 *
 * Consome `POST|GET /closing/competences/{period}/documents*` da BFF.
 * «Anexado» é estado documental — não é documento validado nem item
 * entregue: o checklist permanece «Esperado». Upload usa
 * `idempotency_key` por tentativa do usuário (retry reutiliza a mesma
 * chave — D-U7=A, sem dedup por conteúdo). Substituir cria uma versão
 * nova (`SUPERSEDED` permanece referenciável); cancelar é lógico
 * (`CANCELLED` sai da listagem, histórico e arquivos ficam íntegros).
 * Mutações levam a `revision` do documento (OCC) — quem segurou uma
 * visão velha recebe «atualize e tente de novo», nunca sobrescreve.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
} from "react";

import {
  ActionButton,
  attachmentFileListBemClasses,
  AttachmentFileList,
  ConfirmModalPanel,
  fileDropzoneBemClasses,
  FileDropzone,
} from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  decideDocumentEvidence,
  type RejectionReason,
} from "../../api/competencesApi";
import { REJECTION_REASON_LABELS } from "./ItemValidationPanel";
import {
  cancelClosingDocument,
  CLOSING_DOCUMENT_ACCEPT,
  downloadClosingDocument,
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
  CfDialog,
  CfEmptyState,
  cfConfirmModalClassNames,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { formatDateTime } from "../../utils/formatters";

const DROPZONE_CLASSES = fileDropzoneBemClasses("cf", "evidence-dropzone");
const FILE_LIST_CLASSES = attachmentFileListBemClasses("cf");
const FILE_LIST_LABELS = {
  open: "Abrir",
  download: "Baixar",
  remove: "Remover",
  empty: "Nenhuma evidência anexada.",
};

type PanelError = {
  status: number;
  code: string | null;
  message: string;
};

const PANEL_ERROR_MESSAGES: Record<string, string> = {
  file_too_large: "O arquivo excede o limite de 25 MB.",
  unsupported_media_type:
    "Formato não permitido. Use PDF, imagem, XLS, XLSX ou CSV.",
  empty_file: "O arquivo enviado está vazio.",
  invalid_file_content:
    "O conteúdo do arquivo não é válido para o formato informado.",
  content_type_mismatch:
    "O conteúdo do arquivo não corresponde à extensão informada.",
  idempotency_conflict:
    "Esta chave de envio já foi utilizada com outro arquivo.",
  item_not_found: "Item do checklist não encontrado nesta competência.",
  competence_not_opened: "A competência ainda não foi aberta.",
  persistence_unavailable:
    "Serviço de persistência indisponível. Tente novamente.",
  rbac_unavailable:
    "Serviço de permissões indisponível. Tente novamente.",
  forbidden:
    "Somente quem anexou a evidência ou um gestor pode alterá-la.",
  document_not_found:
    "Documento não encontrado ou fora do escopo solicitado.",
  document_cancelled: "Este documento já foi cancelado.",
  document_not_attached:
    "Este documento não pode ser alterado no estado atual.",
  stale_revision:
    "O documento foi alterado por outra pessoa. A lista foi atualizada.",
  file_missing:
    "O arquivo não está disponível no armazenamento. Tente novamente mais tarde.",
};

const EVENT_LABELS: Record<string, string> = {
  DOCUMENT_UPLOADED: "Documento anexado",
  VERSION_ADDED: "Documento substituído",
  DOCUMENT_CANCELLED: "Documento cancelado",
  DOCUMENT_DOWNLOADED: "Download",
};

const VERSION_STATE_LABELS: Record<string, string> = {
  ATTACHED: "Atual",
  SUPERSEDED: "Substituída",
};

function toPanelError(error: unknown, fallback: string): PanelError {
  if (error instanceof ApiError) {
    const message =
      (error.code && PANEL_ERROR_MESSAGES[error.code]) || error.message;
    return { status: error.status, code: error.code, message };
  }
  return { status: 0, code: null, message: fallback };
}

/** Classifica a falha de download em feedback honesto por causa. */
function toDownloadError(error: unknown): PanelError {
  if (error instanceof ApiError) {
    if (error.status === 401 || error.status === 403) {
      return {
        status: error.status,
        code: error.code,
        message:
          "Você não tem autorização para baixar esta evidência.",
      };
    }
    if (error.status === 404 || error.code === "document_not_found") {
      return {
        status: error.status,
        code: error.code,
        message:
          "Documento não encontrado ou fora do escopo solicitado.",
      };
    }
    if (error.code === "file_missing" || error.status === 503) {
      return {
        status: error.status,
        code: error.code,
        message:
          "O arquivo não está disponível no armazenamento. Tente novamente mais tarde.",
      };
    }
    return {
      status: error.status,
      code: error.code,
      message: `Falha ao baixar o arquivo (HTTP ${error.status}).`,
    };
  }
  return {
    status: 0,
    code: null,
    message: "Falha de comunicação ao baixar o arquivo. Tente novamente.",
  };
}

function formatBytes(value: number | null): string {
  if (value === null || value <= 0) return "";
  if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.ceil(value / 1024)} KB`;
}

function formatDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString("pt-BR") : "";
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

type PendingUpload = {
  file: File;
  idempotencyKey: string;
};

type PendingReplace = {
  documentId: string;
  file: File;
  idempotencyKey: string;
};

export function ClosingDocumentsPanel({
  period,
  snapshotItemId,
  onUploaded,
}: {
  period: string;
  snapshotItemId?: string | null;
  onUploaded?: () => void;
}) {
  const [documents, setDocuments] = useState<{
    key: string;
    items: ClosingDocument[];
  } | null>(null);
  const [listError, setListError] = useState<{
    key: string;
    error: PanelError;
  } | null>(null);
  const [pending, setPending] = useState<PendingUpload | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<PanelError | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<{
    documentId: string;
    error: PanelError;
  } | null>(null);
  const [mutating, setMutating] = useState(false);
  const [mutationError, setMutationError] = useState<PanelError | null>(null);
  const [pendingReplace, setPendingReplace] = useState<PendingReplace | null>(
    null,
  );
  const [replaceTarget, setReplaceTarget] = useState<ClosingDocument | null>(
    null,
  );
  const [cancelTarget, setCancelTarget] = useState<ClosingDocument | null>(
    null,
  );
  const [rejectDocTarget, setRejectDocTarget] =
    useState<ClosingDocument | null>(null);
  const [rejectDocReason, setRejectDocReason] = useState<
    RejectionReason | ""
  >("");
  const [rejectDocComment, setRejectDocComment] = useState("");
  const [versionsDoc, setVersionsDoc] = useState<ClosingDocument | null>(
    null,
  );
  const [versions, setVersions] = useState<DocumentVersion[] | null>(null);
  const [versionsError, setVersionsError] = useState<PanelError | null>(
    null,
  );
  const [eventsDoc, setEventsDoc] = useState<ClosingDocument | null>(null);
  const [events, setEvents] = useState<DocumentAuditEvent[] | null>(null);
  const [eventsError, setEventsError] = useState<PanelError | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const requestId = useRef(0);
  const replaceInputRef = useRef<HTMLInputElement>(null);

  const listKey = `${period}:${snapshotItemId ?? "competence"}:${retryNonce}`;
  const currentDocs = documents?.key === listKey ? documents.items : null;
  const currentError = listError?.key === listKey ? listError.error : null;
  const loading = currentDocs === null && !currentError;

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listClosingDocuments(
      period,
      snapshotItemId ? { snapshotItemId } : {},
      { signal: controller.signal },
    )
      .then((result) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setDocuments({ key: listKey, items: result.documents });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setListError({
          key: listKey,
          error: toPanelError(err, "Falha ao listar evidências."),
        });
      });
    return () => controller.abort();
  }, [period, snapshotItemId, listKey]);

  const refresh = useCallback(() => setRetryNonce((n) => n + 1), []);

  const doUpload = useCallback(
    (upload: PendingUpload) => {
      setPending(upload);
      setUploading(true);
      setUploadError(null);
      uploadClosingDocument(
        period,
        {
          file: upload.file,
          idempotencyKey: upload.idempotencyKey,
          snapshotItemId: snapshotItemId ?? null,
        },
      )
        .then(() => {
          setUploading(false);
          setPending(null);
          refresh();
          onUploaded?.();
        })
        .catch((err: unknown) => {
          setUploading(false);
          // A mesma chave é preservada — retry nunca duplica a evidência.
          setUploadError(
            toPanelError(err, "Falha ao enviar o arquivo."),
          );
        });
    },
    [period, snapshotItemId, onUploaded, refresh],
  );

  const handleFiles = useCallback(
    (files: File[]) => {
      const file = files[0];
      if (!file) return;
      const upload = { file, idempotencyKey: crypto.randomUUID() };
      doUpload(upload);
    },
    [doUpload],
  );

  const retryUpload = useCallback(() => {
    if (pending && !uploading) {
      doUpload(pending);
    }
  }, [pending, uploading, doUpload]);

  const discardPending = useCallback(() => {
    if (!uploading) {
      setPending(null);
      setUploadError(null);
    }
  }, [uploading]);

  const handleDownload = useCallback(
    (documentId: string, versionNo: number, fileName: string) => {
      setDownloadingId(documentId);
      setDownloadError(null);
      downloadClosingDocument(period, documentId, versionNo)
        .then((blob) => saveDocumentBlob(blob, fileName))
        .catch((err: unknown) => {
          setDownloadError({
            documentId,
            error: toDownloadError(err),
          });
        })
        .finally(() => setDownloadingId(null));
    },
    [period],
  );

  // U5 — substituição: o usuário escolhe o arquivo novo; a `revision`
  // vista na lista viaja junto (OCC) — stale_revision ⇒ refresh honesto.
  // A `idempotency_key` identifica ESTA tentativa (D-U7=A na mutação):
  // retry reutiliza a mesma chave e o servidor deduplica — nunca cria
  // duas versões para a mesma ação do usuário.
  const startReplace = useCallback((doc: ClosingDocument) => {
    setReplaceTarget(doc);
    setMutationError(null);
    replaceInputRef.current?.click();
  }, []);

  const doReplace = useCallback(
    (pendingMutation: PendingReplace, revision: number) => {
      setMutating(true);
      setMutationError(null);
      replaceClosingDocument(period, pendingMutation.documentId, {
        file: pendingMutation.file,
        revision,
        idempotencyKey: pendingMutation.idempotencyKey,
      })
        .then(() => {
          setPendingReplace(null);
          refresh();
          onUploaded?.();
        })
        .catch((err: unknown) => {
          const panelError = toPanelError(
            err,
            "Falha ao substituir o arquivo.",
          );
          setMutationError(panelError);
          if (
            panelError.code === "stale_revision" ||
            panelError.code === "document_cancelled"
          ) {
            refresh();
          }
        })
        .finally(() => setMutating(false));
    },
    [period, onUploaded, refresh],
  );

  const handleReplaceFile = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0] ?? null;
      event.target.value = "";
      const doc = replaceTarget;
      setReplaceTarget(null);
      if (!file || !doc) return;
      const pendingMutation = {
        documentId: doc.document_id,
        file,
        idempotencyKey: crypto.randomUUID(),
      };
      setPendingReplace(pendingMutation);
      doReplace(pendingMutation, doc.revision);
    },
    [replaceTarget, doReplace],
  );

  const retryReplace = useCallback(() => {
    if (!pendingReplace || mutating) return;
    // Revision fresca da lista: se a mutação já venceu no servidor o
    // backend deduplica pela key; se perdeu por stale, o retry compete
    // honestamente com a revisão atual.
    const doc = (currentDocs ?? []).find(
      (d) => d.document_id === pendingReplace.documentId,
    );
    if (!doc || doc.state !== "ATTACHED") {
      setPendingReplace(null);
      setMutationError(null);
      refresh();
      return;
    }
    doReplace(pendingReplace, doc.revision);
  }, [pendingReplace, mutating, currentDocs, doReplace, refresh]);

  // U7 — cancelamento lógico com confirmação explícita.
  const confirmCancel = useCallback(() => {
    const doc = cancelTarget;
    if (!doc || mutating) return;
    setMutating(true);
    setMutationError(null);
    cancelClosingDocument(period, doc.document_id, {
      revision: doc.revision,
    })
      .then(() => {
        setCancelTarget(null);
        refresh();
        onUploaded?.();
      })
      .catch((err: unknown) => {
        const panelError = toPanelError(
          err,
          "Falha ao cancelar o documento.",
        );
        setMutationError(panelError);
        if (
          panelError.code === "stale_revision" ||
          panelError.code === "document_cancelled"
        ) {
          setCancelTarget(null);
          refresh();
        }
      })
      .finally(() => setMutating(false));
  }, [period, cancelTarget, mutating, onUploaded, refresh]);

  // Validação de evidência de competência (sem item) — A2.
  const decideEvidence = useCallback(
    (
      documentId: string,
      decision: "ACCEPTED" | "REJECTED",
      payload: { reason_code?: RejectionReason; comment?: string } = {},
    ) => {
      if (mutating) return;
      setMutating(true);
      setMutationError(null);
      decideDocumentEvidence(period, documentId, { decision, ...payload })
        .then(() => {
          setRejectDocTarget(null);
          setRejectDocReason("");
          setRejectDocComment("");
          refresh();
        })
        .catch((err: unknown) => {
          setMutationError(
            toPanelError(err, "Falha ao registrar a decisão."),
          );
        })
        .finally(() => setMutating(false));
    },
    [period, mutating, refresh],
  );

  const submitDocReject = useCallback(() => {
    const doc = rejectDocTarget;
    if (!doc || !rejectDocReason) return;
    decideEvidence(doc.document_id, "REJECTED", {
      reason_code: rejectDocReason,
      ...(rejectDocReason === "OTHER"
        ? { comment: rejectDocComment }
        : {}),
    });
  }, [rejectDocTarget, rejectDocReason, rejectDocComment, decideEvidence]);

  // U6 — histórico de versões; versões antigas baixam pelo mesmo U4.
  const openVersions = useCallback(
    (doc: ClosingDocument) => {
      setVersionsDoc(doc);
      setVersions(null);
      setVersionsError(null);
      listDocumentVersions(period, doc.document_id)
        .then(setVersions)
        .catch((err: unknown) => {
          setVersionsError(
            toPanelError(err, "Falha ao listar as versões."),
          );
        });
    },
    [period],
  );

  // U8 — eventos de auditoria do documento.
  const openEvents = useCallback(
    (doc: ClosingDocument) => {
      setEventsDoc(doc);
      setEvents(null);
      setEventsError(null);
      listDocumentEvents(period, doc.document_id)
        .then((result) => setEvents(result.events))
        .catch((err: unknown) => {
          setEventsError(
            toPanelError(err, "Falha ao listar os eventos."),
          );
        });
    },
    [period],
  );

  const listItems = useMemo(
    () =>
      (currentDocs ?? []).map((doc) => ({
        id: doc.document_id,
        fileName: doc.original_name ?? doc.title ?? "Documento",
        detail: [
          `v${doc.current_version_no}`,
          doc.title && doc.original_name ? doc.title : null,
          formatBytes(doc.size_bytes),
          formatDate(doc.created_at),
        ]
          .filter(Boolean)
          .join(" · "),
        busy: downloadingId === doc.document_id || mutating,
      })),
    [currentDocs, downloadingId, mutating],
  );

  const docName = (doc: ClosingDocument) =>
    doc.original_name ?? doc.title ?? "Documento";

  return (
    <div className="cf-documents-panel">
      <FileDropzone
        classNames={DROPZONE_CLASSES}
        labels={{
          title: "Arraste o arquivo ou clique para selecionar",
          hint: "PDF, imagem, XLS, XLSX ou CSV · máx. 25 MB",
        }}
        accept={CLOSING_DOCUMENT_ACCEPT}
        multiple={false}
        busy={uploading}
        disabled={Boolean(currentError && currentError.status === 403)}
        onFilesSelected={handleFiles}
        ariaLabel="Enviar evidência documental"
      />

      <input
        ref={replaceInputRef}
        type="file"
        accept={CLOSING_DOCUMENT_ACCEPT}
        style={{ display: "none" }}
        tabIndex={-1}
        aria-hidden="true"
        onChange={handleReplaceFile}
      />

      {uploading && pending ? (
        <CfFeedbackMessage intent="info" title="Enviando evidência">
          Enviando «{pending.file.name}»…
        </CfFeedbackMessage>
      ) : null}

      {uploadError ? (
        <div className="cf-documents-panel__upload-error">
          <CfFeedbackMessage
            intent="error"
            title="Falha no envio"
          >
            {uploadError.message}
          </CfFeedbackMessage>
          <div className="cf-documents-panel__upload-actions">
            <button
              type="button"
              className="cf-documents-panel__retry"
              onClick={retryUpload}
              disabled={uploading}
            >
              Tentar novamente
            </button>
            <button
              type="button"
              className="cf-documents-panel__discard"
              onClick={discardPending}
              disabled={uploading}
            >
              Descartar
            </button>
          </div>
        </div>
      ) : null}

      {mutationError ? (
        <CfFeedbackMessage
          intent="error"
          title="Ação não concluída"
          action={
            pendingReplace ? (
              <button
                type="button"
                className="cf-documents-panel__retry"
                disabled={mutating}
                onClick={retryReplace}
              >
                Tentar novamente
              </button>
            ) : undefined
          }
        >
          {mutationError.message}
        </CfFeedbackMessage>
      ) : null}

      {currentError ? (
        <CfQueryErrorBanner
          error={currentError}
          dataset="as evidências documentais"
          onRetry={() => setRetryNonce((n) => n + 1)}
        />
      ) : loading ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Carregando evidências…"
        />
      ) : (
        <>
        {downloadError ? (
          <CfFeedbackMessage
            intent="error"
            title="Falha no download"
            action={
              <button
                type="button"
                className="cf-documents-panel__retry"
                disabled={downloadingId !== null}
                onClick={() => {
                  const doc = (currentDocs ?? []).find(
                    (d) => d.document_id === downloadError.documentId,
                  );
                  if (doc) {
                    handleDownload(
                      doc.document_id,
                      doc.current_version_no,
                      doc.original_name ?? doc.title ?? "documento",
                    );
                  }
                }}
              >
                Tentar novamente
              </button>
            }
          >
            {downloadError.error.message}
          </CfFeedbackMessage>
        ) : null}
        <AttachmentFileList
          classNames={FILE_LIST_CLASSES}
          labels={FILE_LIST_LABELS}
          items={listItems}
          emptyMessage="Nenhuma evidência anexada nesta competência."
          canRemove={false}
          onDownload={(item) => {
            const doc = (currentDocs ?? []).find(
              (d) => d.document_id === item.id,
            );
            if (doc) {
              handleDownload(
                doc.document_id,
                doc.current_version_no,
                item.fileName,
              );
            }
          }}
          itemActions={(item) => {
            const doc = (currentDocs ?? []).find(
              (d) => d.document_id === item.id,
            );
            if (!doc) return null;
            return (
              <>
                <ActionButton
                  variant="ghost"
                  disabled={item.busy}
                  onClick={() => startReplace(doc)}
                >
                  Substituir
                </ActionButton>
                <ActionButton
                  variant="ghost"
                  disabled={item.busy}
                  onClick={() => openVersions(doc)}
                >
                  Versões
                </ActionButton>
                <ActionButton
                  variant="ghost"
                  disabled={item.busy}
                  onClick={() => openEvents(doc)}
                >
                  Eventos
                </ActionButton>
                <ActionButton
                  variant="ghost"
                  disabled={item.busy}
                  onClick={() => {
                    setCancelTarget(doc);
                    setMutationError(null);
                  }}
                >
                  Cancelar
                </ActionButton>
                {!snapshotItemId && !doc.snapshot_item_id ? (
                  <>
                    <ActionButton
                      variant="ghost"
                      disabled={item.busy}
                      onClick={() =>
                        decideEvidence(doc.document_id, "ACCEPTED")
                      }
                    >
                      Aceitar
                    </ActionButton>
                    <ActionButton
                      variant="ghost"
                      disabled={item.busy}
                      onClick={() => {
                        setRejectDocTarget(doc);
                        setRejectDocReason("");
                        setRejectDocComment("");
                        setMutationError(null);
                      }}
                    >
                      Rejeitar
                    </ActionButton>
                  </>
                ) : null}
              </>
            );
          }}
        />
        </>
      )}

      {versionsDoc ? (
        <CfDialog
          open
          title={`Versões — ${docName(versionsDoc)}`}
          onClose={() => setVersionsDoc(null)}
          closeAriaLabel="Fechar versões"
        >
          {versionsError ? (
            <CfFeedbackMessage
              intent="error"
              title="Falha ao listar versões"
            >
              {versionsError.message}
            </CfFeedbackMessage>
          ) : versions === null ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Carregando versões…"
            />
          ) : versions.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhuma versão registrada."
            />
          ) : (
            <ul className="cf-documents-panel__versions">
              {versions.map((version) => (
                <li
                  key={version.document_version_id}
                  className="cf-documents-panel__version"
                >
                  <div className="cf-documents-panel__version-meta">
                    <p className="cf-documents-panel__version-name">
                      v{version.version_no} ·{" "}
                      {VERSION_STATE_LABELS[version.state] ??
                        version.state}
                      {" — "}
                      {version.original_name}
                    </p>
                    <p className="cf-documents-panel__version-detail">
                      {[
                        formatBytes(version.size_bytes),
                        formatDateTime(version.created_at),
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  </div>
                  <ActionButton
                    variant="ghost"
                    disabled={downloadingId === versionsDoc.document_id}
                    onClick={() =>
                      handleDownload(
                        versionsDoc.document_id,
                        version.version_no,
                        version.original_name,
                      )
                    }
                  >
                    Baixar
                  </ActionButton>
                </li>
              ))}
            </ul>
          )}
        </CfDialog>
      ) : null}

      {eventsDoc ? (
        <CfDialog
          open
          title={`Eventos — ${docName(eventsDoc)}`}
          onClose={() => setEventsDoc(null)}
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
            <ul className="cf-documents-panel__events">
              {events.map((event) => (
                <li
                  key={event.event_id}
                  className="cf-documents-panel__event"
                >
                  <p className="cf-documents-panel__event-name">
                    {EVENT_LABELS[event.event_type] ?? event.event_type}
                    {eventNote(event) ? ` · ${eventNote(event)}` : ""}
                  </p>
                  <p className="cf-documents-panel__event-detail">
                    {formatDateTime(event.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </CfDialog>
      ) : null}

      {cancelTarget ? (
        <CfDialog
          open
          title="Cancelar documento"
          onClose={() => {
            if (!mutating) setCancelTarget(null);
          }}
          closeAriaLabel="Fechar confirmação de cancelamento"
        >
          <ConfirmModalPanel
            message={
              <>
                Cancelar «{docName(cancelTarget)}»? O documento sai da
                lista, mas as versões e o histórico são preservados.
              </>
            }
            confirmLabel="Cancelar documento"
            cancelLabel="Voltar"
            variant="danger"
            confirmBusy={mutating}
            confirmBusyLabel="Cancelando…"
            onConfirm={confirmCancel}
            onCancel={() => setCancelTarget(null)}
            classNames={cfConfirmModalClassNames}
          />
        </CfDialog>
      ) : null}

      {rejectDocTarget ? (
        <CfDialog
          open
          title={`Rejeitar evidência — ${docName(rejectDocTarget)}`}
          onClose={() => !mutating && setRejectDocTarget(null)}
          closeAriaLabel="Fechar rejeição"
        >
          <div className="cf-validation-panel__form">
            <label>
              Motivo da rejeição
              <select
                value={rejectDocReason}
                disabled={mutating}
                onChange={(event) =>
                  setRejectDocReason(
                    event.target.value as RejectionReason,
                  )
                }
              >
                <option value="">Selecione…</option>
                {Object.entries(REJECTION_REASON_LABELS).map(
                  ([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ),
                )}
              </select>
            </label>
            {rejectDocReason === "OTHER" ? (
              <label>
                Comentário (obrigatório para «Outro»)
                <textarea
                  value={rejectDocComment}
                  disabled={mutating}
                  rows={3}
                  onChange={(event) =>
                    setRejectDocComment(event.target.value)
                  }
                />
              </label>
            ) : null}
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={
                  mutating ||
                  !rejectDocReason ||
                  (rejectDocReason === "OTHER" &&
                    !rejectDocComment.trim())
                }
                onClick={submitDocReject}
              >
                Confirmar rejeição
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={mutating}
                onClick={() => setRejectDocTarget(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}

      <p className="cf-documents-panel__honesty">
        Evidência anexada não é documento validado — o item do checklist
        permanece «Esperado» até a conferência.
      </p>
    </div>
  );
}
