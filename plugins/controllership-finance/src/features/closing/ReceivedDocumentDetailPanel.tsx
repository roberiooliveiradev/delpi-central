/**
 * Detalhe do documento recebido — experiência do destinatário externo
 * (DRE-019, doc 112 §54 N3).
 *
 * Mesma composição visual do detalhe interno (`DocumentDetailPanel`):
 * prévia do arquivo, metadados, versões, download, solicitações de
 * esclarecimento/revisão e conversa — mas cada dado vem da projeção
 * autorizada `/closing/received-documents/*`:
 * - somente versões pinadas em pacote SUBMITTED são listadas/baixáveis;
 * - download passa pelo stream autenticado e auditado da BFF — nunca
 *   URL pública nem storage key;
 * - sem ações internas (upload, substituir, cancelar, validar);
 * - solicitações seguem OPEN → ANSWERED → CONFIRMED: responder não
 *   encerra — a conclusão é ato exclusivo do requerente.
 */
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  FilePreviewView,
  useFilePreviewLoader,
} from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  confirmReceivedAdjustmentRequest,
  createReceivedAdjustmentRequest,
  downloadReceivedDocumentVersion,
  getReceivedDocument,
  listReceivedAdjustmentRequests,
  saveDocumentBlob,
  type ReceivedAdjustmentRequest,
  type ReceivedDocumentDetail,
} from "../../api/receivedDocumentsApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import { FilterInputField } from "../../app/cfFiltersUi";
import {
  CfActionButton,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";
import { ReceivedConversationPanel } from "./ReceivedConversationPanel";

type PanelError = { status: number; code: string | null; message: string };

const DETAIL_ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para este documento.",
  document_not_found:
    "Documento não encontrado ou não liberado para você.",
  adjustment_request_not_found: "Solicitação não encontrada.",
  invalid_adjustment_request_state:
    "A solicitação mudou de estado — atualize e tente novamente.",
  invalid_message:
    "O texto deve ter entre 1 e 4000 caracteres.",
  idempotency_conflict:
    "Esta solicitação mudou desde a primeira tentativa — revise e envie novamente.",
  file_missing:
    "O arquivo não está disponível no armazenamento — avise o suporte.",
};

function toPanelError(error: unknown, fallback: string): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code,
      message:
        (error.code && DETAIL_ERROR_MESSAGES[error.code]) ||
        error.message,
    };
  }
  return { status: 0, code: null, message: fallback };
}

function formatBytes(value: number | null): string {
  if (value === null || value <= 0) return "";
  if (value >= 1024 * 1024)
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.ceil(value / 1024)} KB`;
}

const REQUEST_STATE_LABELS: Record<string, string> = {
  OPEN: "Aguardando resposta",
  ANSWERED: "Respondida",
  CONFIRMED: "Concluída",
};

const REQUEST_STATE_VARIANTS: Record<
  string,
  "warning" | "info" | "success" | "neutral"
> = {
  OPEN: "warning",
  ANSWERED: "info",
  CONFIRMED: "success",
};

export function ReceivedDocumentDetailPanel({
  period,
  documentId,
  onBack,
}: {
  period: string;
  documentId: string;
  /** Volta à entrega da competência preservando o contexto. */
  onBack: () => void;
}) {
  const [result, setResult] = useState<{
    key: string;
    data: ReceivedDocumentDetail;
  } | null>(null);
  const [error, setError] = useState<{
    key: string;
    error: PanelError;
  } | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [requests, setRequests] = useState<{
    key: string;
    items: ReceivedAdjustmentRequest[];
  } | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(
    null,
  );
  const [previewNonce, setPreviewNonce] = useState(0);
  const [requestDraft, setRequestDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{
    intent: "info" | "error" | "success";
    message: string;
  } | null>(null);
  const requestId = useRef(0);
  /** Chave idempotente da solicitação em andamento — retry do mesmo
   * texto reutiliza a chave (deduplica no backend). */
  const requestAttemptRef = useRef<{ key: string; text: string } | null>(
    null,
  );

  const key = `received:${period}:${documentId}:${retryNonce}`;
  const data = result?.key === key ? result.data : null;
  const currentError = error?.key === key ? error.error : null;
  const loading = data === null && !currentError;

  const document = data?.document ?? null;
  const versionList = data?.versions ?? [];
  const requestList =
    requests?.key === documentId ? requests.items : null;

  const effectiveVersionNo =
    selectedVersion ?? document?.version_no ?? 0;

  const refresh = useCallback(() => setRetryNonce((n) => n + 1), []);

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    const alive = () =>
      !controller.signal.aborted && requestId.current === id;
    getReceivedDocument(period, documentId, {
      signal: controller.signal,
    })
      .then((detail) => {
        if (!alive()) return;
        setResult({ key, data: detail });
        setError(null);
      })
      .catch((err: unknown) => {
        if (!alive()) return;
        setError({
          key,
          error: toPanelError(err, "Falha ao carregar o documento."),
        });
      });
    return () => controller.abort();
  }, [period, documentId, key]);

  useEffect(() => {
    const controller = new AbortController();
    listReceivedAdjustmentRequests(period, documentId, {
      signal: controller.signal,
    })
      .then((items) => {
        if (controller.signal.aborted) return;
        setRequests({ key: documentId, items });
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setRequests({ key: documentId, items: [] });
      });
    return () => controller.abort();
  }, [period, documentId, retryNonce]);

  // Prévia via contrato de download autenticado — falha de prévia nunca
  // bloqueia o download. `source` tem identidade estável: só muda com
  // período/documento/versão ou retry explícito (nonce).
  const previewSource = useCallback(() => {
    void previewNonce;
    return downloadReceivedDocumentVersion(
      period,
      documentId,
      effectiveVersionNo,
    );
  }, [period, documentId, effectiveVersionNo, previewNonce]);
  const preview = useFilePreviewLoader({
    source: document ? previewSource : null,
    mimeType: document?.mime_type ?? null,
    fileName: document?.original_name ?? null,
    enabled: Boolean(document),
  });
  const retryPreview = useCallback(
    () => setPreviewNonce((n) => n + 1),
    [],
  );

  const handleDownload = useCallback(() => {
    if (!document) return;
    downloadReceivedDocumentVersion(
      period,
      document.document_id,
      effectiveVersionNo,
    )
      .then((blob) =>
        saveDocumentBlob(blob, document.original_name ?? "documento"),
      )
      .catch((err: unknown) => {
        setFeedback({
          intent: "error",
          message: toPanelError(err, "Falha ao baixar o arquivo.")
            .message,
        });
      });
  }, [period, document, effectiveVersionNo]);

  const handleSubmitRequest = useCallback(() => {
    const text = requestDraft.trim();
    if (!text || submitting) return;
    const attempt =
      requestAttemptRef.current && requestAttemptRef.current.text === text
        ? requestAttemptRef.current
        : { key: crypto.randomUUID(), text };
    requestAttemptRef.current = attempt;
    setSubmitting(true);
    setFeedback(null);
    createReceivedAdjustmentRequest(period, documentId, {
      body: text,
      idempotencyKey: attempt.key,
    })
      .then(() => {
        setSubmitting(false);
        requestAttemptRef.current = null;
        setRequestDraft("");
        setFeedback({
          intent: "success",
          message: "Solicitação registrada.",
        });
        refresh();
      })
      .catch((err: unknown) => {
        setSubmitting(false);
        setFeedback({
          intent: "error",
          message: toPanelError(
            err,
            "Falha ao registrar a solicitação.",
          ).message,
        });
      });
  }, [period, documentId, requestDraft, submitting, refresh]);

  const handleConfirmRequest = useCallback(
    (request: ReceivedAdjustmentRequest) => {
      if (confirmingId) return;
      setConfirmingId(request.request_id);
      setFeedback(null);
      confirmReceivedAdjustmentRequest(
        period,
        documentId,
        request.request_id,
      )
        .then(() => {
          setConfirmingId(null);
          setFeedback({
            intent: "success",
            message: "Solicitação concluída.",
          });
          refresh();
        })
        .catch((err: unknown) => {
          setConfirmingId(null);
          setFeedback({
            intent: "error",
            message: toPanelError(
              err,
              "Falha ao concluir a solicitação.",
            ).message,
          });
        });
    },
    [period, documentId, confirmingId, refresh],
  );

  const title =
    document?.title ??
    document?.item_name ??
    document?.original_name ??
    "Documento";

  return (
    <div className="cf-document-detail">
      <div className="cf-document-detail__head">
        <CfActionButton variant="ghost" onClick={onBack}>
          ← Voltar aos documentos recebidos
        </CfActionButton>
        <div className="cf-document-detail__title">
          <strong>{title}</strong>
          <span className="cf-document-detail__meta">
            Referência {period}
            {document?.item_name ? " · Exigido" : ""}
          </span>
        </div>
        {document ? (
          <CfStatusBadge variant="info" label="Documento liberado" />
        ) : null}
      </div>

      {currentError ? (
        <CfQueryErrorBanner
          error={currentError}
          dataset="o documento"
          onRetry={refresh}
        />
      ) : null}

      {loading ? (
        <p aria-live="polite">Carregando documento…</p>
      ) : null}

      {feedback ? (
        <CfFeedbackMessage
          intent={feedback.intent}
          title={feedback.intent === "error" ? "Erro" : "Documento"}
        >
          {feedback.message}
        </CfFeedbackMessage>
      ) : null}

      {data && document ? (
        <>
          <div className="cf-document-detail__columns">
            <CfSectionCard
              title="Documento"
              hint={CF_HELP.receivedDocuments.detailFile}
            >
              <FilePreviewView
                state={preview}
                title={document.original_name ?? title}
              />
              {preview.error ? (
                <CfActionButton variant="ghost" onClick={retryPreview}>
                  Tentar novamente
                </CfActionButton>
              ) : null}
              <p className="cf-document-detail__meta">
                {document.original_name ?? "arquivo"}
                {document.size_bytes
                  ? ` · ${formatBytes(document.size_bytes)}`
                  : ""}
                {` · v${effectiveVersionNo}`}
                {effectiveVersionNo !== document.version_no
                  ? " (versão anterior)"
                  : ""}
              </p>
              {versionList.length > 0 ? (
                <ul className="cf-document-detail__versions">
                  {versionList.map((version) => (
                    <li key={version.version_no}>
                      <button
                        type="button"
                        className="cf-document-detail__docpick"
                        aria-pressed={
                          version.version_no === effectiveVersionNo
                        }
                        onClick={() =>
                          setSelectedVersion(version.version_no)
                        }
                      >
                        v{version.version_no}
                        {version.version_no === document.version_no
                          ? " — versão liberada"
                          : " — versão anterior"}
                        {version.created_at
                          ? ` · ${formatDateTime(version.created_at)}`
                          : ""}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
              <div className="cf-settlements-actions">
                <CfActionButton variant="ghost" onClick={handleDownload}>
                  Baixar
                </CfActionButton>
              </div>
            </CfSectionCard>

            <div className="cf-document-detail__side">
              <CfSectionCard
                title="Solicitações de esclarecimento"
                hint={CF_HELP.receivedDocuments.requests}
              >
                {requestList === null ? (
                  <p aria-live="polite">Carregando solicitações…</p>
                ) : requestList.length === 0 ? (
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Nenhuma solicitação registrada neste documento."
                  />
                ) : (
                  <ul className="cf-document-detail__doclist">
                    {requestList.map((request) => (
                      <li key={request.request_id}>
                        <div>
                          <CfStatusBadge
                            variant={
                              REQUEST_STATE_VARIANTS[request.state] ??
                              "neutral"
                            }
                            label={
                              REQUEST_STATE_LABELS[request.state] ??
                              request.state
                            }
                          />{" "}
                          {request.body}
                          <p className="cf-document-detail__meta">
                            {request.created_at
                              ? formatDateTime(request.created_at)
                              : ""}
                            {request.version_no
                              ? ` · v${request.version_no}`
                              : ""}
                          </p>
                          {request.answer_body ? (
                            <p className="cf-document-detail__meta">
                              Resposta
                              {request.answered_name
                                ? ` de ${request.answered_name}`
                                : ""}
                              {request.answered_at
                                ? ` em ${formatDateTime(request.answered_at)}`
                                : ""}
                              : {request.answer_body}
                            </p>
                          ) : null}
                          {request.state === "ANSWERED" ? (
                            <CfActionButton
                              variant="ghost"
                              disabled={
                                confirmingId === request.request_id
                              }
                              onClick={() =>
                                handleConfirmRequest(request)
                              }
                            >
                              {confirmingId === request.request_id
                                ? "Concluindo…"
                                : "Concluir solicitação"}
                            </CfActionButton>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
                <FilterInputField
                  id="cf-received-request-draft"
                  label="Nova solicitação"
                  type="text"
                  value={requestDraft}
                  onChange={setRequestDraft}
                />
                <div className="cf-settlements-actions">
                  <CfActionButton
                    variant="ghost"
                    disabled={submitting || !requestDraft.trim()}
                    onClick={handleSubmitRequest}
                  >
                    {submitting ? "Enviando…" : "Solicitar esclarecimento"}
                  </CfActionButton>
                </div>
              </CfSectionCard>

              <CfSectionCard
                title="Conversa sobre o documento"
                hint={CF_HELP.receivedDocuments.detailConversation}
              >
                <ReceivedConversationPanel
                  key={document.document_id}
                  period={period}
                  documentId={document.document_id}
                />
              </CfSectionCard>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
