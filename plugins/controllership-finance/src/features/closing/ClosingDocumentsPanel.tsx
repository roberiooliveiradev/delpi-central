/**
 * Evidências documentais da competência — P2-Upload SLICE-1.
 *
 * Consome `POST|GET /closing/competences/{period}/documents*` da BFF.
 * «Anexado» é estado documental — não é documento validado nem item
 * entregue: o checklist permanece «Esperado». Upload usa
 * `idempotency_key` por tentativa do usuário (retry reutiliza a mesma
 * chave — D-U7=A, sem dedup por conteúdo).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  attachmentFileListBemClasses,
  AttachmentFileList,
  fileDropzoneBemClasses,
  FileDropzone,
} from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  CLOSING_DOCUMENT_ACCEPT,
  downloadClosingDocument,
  listClosingDocuments,
  saveDocumentBlob,
  uploadClosingDocument,
  type ClosingDocument,
} from "../../api/documentsApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfEmptyState,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";

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

const UPLOAD_ERROR_MESSAGES: Record<string, string> = {
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
};

function toPanelError(error: unknown, fallback: string): PanelError {
  if (error instanceof ApiError) {
    const message =
      (error.code && UPLOAD_ERROR_MESSAGES[error.code]) || error.message;
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

type PendingUpload = {
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
  const [retryNonce, setRetryNonce] = useState(0);
  const requestId = useRef(0);

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
          setRetryNonce((n) => n + 1);
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
    [period, snapshotItemId, onUploaded],
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

  const listItems = useMemo(
    () =>
      (currentDocs ?? []).map((doc) => ({
        id: doc.document_id,
        fileName: doc.original_name ?? doc.title ?? "Documento",
        detail: [
          doc.title && doc.original_name ? doc.title : null,
          formatBytes(doc.size_bytes),
          doc.created_at
            ? new Date(doc.created_at).toLocaleDateString("pt-BR")
            : null,
        ]
          .filter(Boolean)
          .join(" · "),
        busy: downloadingId === doc.document_id,
      })),
    [currentDocs, downloadingId],
  );

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
        />
        </>
      )}

      <p className="cf-documents-panel__honesty">
        Evidência anexada não é documento validado — o item do checklist
        permanece «Esperado» até a conferência.
      </p>
    </div>
  );
}
