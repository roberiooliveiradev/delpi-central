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
 * A conversa livre do documento (U9) é persistida no backend — a
 * Controladoria inicia o fio sem solicitação prévia da DRE (Plano 113
 * §21). `ATTACHED != VALIDATED`: uma mensagem não valida o documento
 * nem encerra solicitação automaticamente.
 */
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
} from "react";

import {
  ConfirmModalPanel,
  FileDropzone,
  fileDropzoneBemClasses,
  FilePreviewView,
  useFilePreviewLoader,
  type TimelineItemModel,
} from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  getCompetenceItem,
  type CompetenceChecklistItemDetail,
} from "../../api/competencesApi";
import {
  cancelClosingDocument,
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
  CfDialog,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  CfTimeline,
  CfUnifiedAvatar,
  cfConfirmModalClassNames,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";
import { DocumentConversationPanel } from "./DocumentConversationPanel";
import { ItemValidationPanel } from "./ItemValidationPanel";
import {
  useParticipantProfiles,
  type ParticipantVisual,
} from "./useParticipantProfiles";

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
  file_missing:
    "O arquivo não está disponível no armazenamento — avise o suporte.",
  item_locked_by_submitted_package:
    "Este documento integra um conjunto já enviado — a correção exige nova versão do conjunto.",
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
  DOCUMENT_CANCELLED: "Documento removido",
  DOCUMENT_DOWNLOADED: "Download",
  EVIDENCE_ACCEPTED: "Evidência conferida",
  EVIDENCE_REJECTED: "Ajuste solicitado",
};

/** Tons do marcador por evento material — semântica visual do kit. */
const EVENT_TONES: Record<string, TimelineItemModel["tone"]> = {
  DOCUMENT_UPLOADED: "info",
  VERSION_ADDED: "info",
  DOCUMENT_CANCELLED: "danger",
  EVIDENCE_ACCEPTED: "success",
  EVIDENCE_REJECTED: "warning",
};

/** Eventos auditados que NÃO aparecem na linha do tempo operacional:
 * downloads são consultas de rotina e mensagens já vivem na conversa —
 * a trilha de auditoria U8 continua registrando ambos. */
const TIMELINE_HIDDEN_EVENTS = new Set([
  "DOCUMENT_DOWNLOADED",
  "DOCUMENT_MESSAGE_POSTED",
]);

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

/** Evento U8 → item de linha do tempo do kit (doc 112 §44):
 * título/data PT-BR, autor identificado pelo perfil oficial — UUID
 * nunca aparece na UI. */
function toTimelineItem(
  event: DocumentAuditEvent,
  profile: ParticipantVisual | undefined,
): TimelineItemModel {
  const actorName = profile?.displayName?.trim() || "Participante";
  const note = eventNote(event);
  return {
    id: event.event_id,
    title: EVENT_LABELS[event.event_type] ?? "Atualização no documento",
    occurredAt: event.created_at ?? undefined,
    timeLabel: event.created_at ? formatDateTime(event.created_at) : "",
    detail: note || undefined,
    meta: actorName,
    marker: (
      <CfUnifiedAvatar
        kind="person"
        label={actorName}
        imageUrl={profile?.photoUrl ?? null}
        fallbackText={actorName}
      />
    ),
    tone: EVENT_TONES[event.event_type] ?? "default",
  };
}

type DetailResult =
  | {
      kind: "item";
      item: CompetenceChecklistItemDetail;
      documents: ClosingDocument[];
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
  const [cancelTarget, setCancelTarget] = useState<ClosingDocument | null>(
    null,
  );
  const [selectedVersion, setSelectedVersion] = useState<{
    key: string;
    versionNo: number;
  } | null>(null);
  const [previewNonce, setPreviewNonce] = useState(0);
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
  const timelineEvents = (eventList ?? []).filter(
    (event) => !TIMELINE_HIDDEN_EVENTS.has(event.event_type),
  );
  const eventProfiles = useParticipantProfiles(
    timelineEvents.map((event) => event.actor_subject),
  );
  const timelineItems = timelineEvents.map((event) =>
    toTimelineItem(event, eventProfiles.get(event.actor_subject)),
  );

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
          const docs = await listClosingDocuments(
            period,
            { snapshotItemId: item.snapshot_item_id },
            { signal: controller.signal },
          );
          if (!alive()) return;
          setResult({
            key,
            data: {
              kind: "item",
              item,
              documents: docs.documents.filter(
                (d) => d.state !== "CANCELLED",
              ),
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

  // Versão exibida na prévia/download — a seleção é «carimbada» com o id
  // do documento, então trocar de documento nunca mostra versão antiga.
  const effectiveVersionNo =
    selectedDoc && selectedVersion?.key === selectedDoc.document_id
      ? selectedVersion.versionNo
      : (selectedDoc?.current_version_no ?? 0);

  // Prévia via contrato de download autenticado (falha de prévia nunca
  // bloqueia o download). `source` DEVE ter identidade estável: uma
  // closure nova por render refaz o fetch a cada render — loop infinito
  // de spinner + enxurrada de eventos DOCUMENT_DOWNLOADED no backend.
  // Ela só muda com período/documento/versão ou retry explícito (nonce).
  const previewDocId = selectedDoc?.document_id ?? null;
  const previewSource = useCallback(() => {
    // `previewNonce` só entra na identidade: incrementá-lo força refetch
    // (retry explícito) sem precisar de canal lateral no hook do kit.
    void previewNonce;
    return previewDocId
      ? downloadClosingDocument(period, previewDocId, effectiveVersionNo)
      : Promise.reject(new Error("Sem documento."));
  }, [period, previewDocId, effectiveVersionNo, previewNonce]);
  const preview = useFilePreviewLoader({
    source: previewDocId ? previewSource : null,
    mimeType: selectedDoc?.mime_type ?? null,
    fileName: selectedDoc?.original_name ?? null,
    enabled: Boolean(selectedDoc),
  });
  const retryPreview = useCallback(
    () => setPreviewNonce((n) => n + 1),
    [],
  );

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
    downloadClosingDocument(period, doc.document_id, effectiveVersionNo)
      .then((blob) =>
        saveDocumentBlob(blob, doc.original_name ?? "documento"),
      )
      .catch((err: unknown) => {
        setFeedback({
          intent: "error",
          message: toPanelError(err, "Falha ao baixar o arquivo.").message,
        });
      });
  }, [period, selectedDoc, effectiveVersionNo]);

  // U7 — remoção lógica: o documento sai da lista ativa; versões e
  // histórico permanecem. Remover o arquivo NÃO cancela a exigência.
  const confirmCancel = useCallback(() => {
    const doc = cancelTarget;
    if (!doc) return;
    setUploading(true);
    cancelClosingDocument(period, doc.document_id, {
      revision: doc.revision,
    })
      .then(() => {
        setUploading(false);
        setCancelTarget(null);
        if (data?.kind === "document") {
          // Documento adicional removido: sai da lista ativa — voltar.
          onBack();
        } else {
          setFeedback({
            intent: "success",
            message:
              "Documento removido. As versões e o histórico foram preservados.",
          });
          refresh();
        }
      })
      .catch((err: unknown) => {
        setUploading(false);
        setCancelTarget(null);
        setFeedback({
          intent: "error",
          message: toPanelError(err, "Falha ao remover o documento.")
            .message,
        });
        if (err instanceof ApiError && err.code === "stale_revision") {
          refresh();
        }
      });
  }, [period, cancelTarget, data, onBack, refresh]);

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
                  {preview.error ? (
                    <CfActionButton
                      variant="ghost"
                      onClick={retryPreview}
                    >
                      Tentar novamente
                    </CfActionButton>
                  ) : null}
                  <p className="cf-document-detail__meta">
                    {selectedDoc.original_name ?? "arquivo"}
                    {selectedDoc.size_bytes
                      ? ` · ${formatBytes(selectedDoc.size_bytes)}`
                      : ""}
                    {` · v${effectiveVersionNo}`}
                    {effectiveVersionNo !== selectedDoc.current_version_no
                      ? " (versão anterior)"
                      : ""}
                  </p>
                  {versionList && versionList.length > 0 ? (
                    <ul className="cf-document-detail__versions">
                      {versionList.map((version) => (
                        <li key={version.document_version_id}>
                          <button
                            type="button"
                            className="cf-document-detail__docpick"
                            aria-pressed={
                              version.version_no === effectiveVersionNo
                            }
                            onClick={() =>
                              setSelectedVersion({
                                key: selectedDoc.document_id,
                                versionNo: version.version_no,
                              })
                            }
                          >
                            v{version.version_no} —{" "}
                            {version.state === "ATTACHED"
                              ? "atual"
                              : "substituída"}
                            {version.created_at
                              ? ` · ${formatDateTime(version.created_at)}`
                              : ""}
                          </button>
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
                    {selectedDoc.state === "ATTACHED" ? (
                      <CfActionButton
                        variant="ghost"
                        disabled={uploading}
                        onClick={() => setCancelTarget(selectedDoc)}
                      >
                        Remover documento
                      </CfActionButton>
                    ) : null}
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

            <div className="cf-document-detail__side">
              {data.kind === "item" ? (
                <CfSectionCard
                  title="Validação do documento"
                  hint={CF_HELP.monthlyClosing.detailInteractions}
                >
                  <ItemValidationPanel
                    period={period}
                    item={data.item}
                    onChanged={refresh}
                  />
                </CfSectionCard>
              ) : null}

              <CfSectionCard
                title="Conversa sobre o documento"
                hint={CF_HELP.monthlyClosing.detailConversation}
              >
                {selectedDoc ? (
                  <DocumentConversationPanel
                    key={selectedDoc.document_id}
                    period={period}
                    documentId={selectedDoc.document_id}
                  />
                ) : (
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Anexe um documento para conversar sobre ele."
                  />
                )}
              </CfSectionCard>
            </div>
          </div>

          <CfSectionCard
            title="Histórico"
            hint={CF_HELP.monthlyClosing.detailHistory}
          >
            {selectedDoc && eventList ? (
              <CfTimeline
                items={timelineItems}
                aria-label="Histórico do documento"
                emptyMessage="Ainda não há alterações registradas neste documento."
              />
            ) : (
              <CfEmptyState
                classNames={cfEmptyStateClassNames}
                defaultMessage="Ainda não há alterações registradas neste documento."
              />
            )}
            {selectedDoc ? (
              <p className="cf-document-detail__meta">
                Downloads e mensagens da conversa ficam fora desta linha
                do tempo — a trilha de auditoria completa permanece
                registrada.
              </p>
            ) : null}
          </CfSectionCard>

          {cancelTarget ? (
            <CfDialog
              open
              title="Remover documento"
              onClose={() => {
                if (!uploading) setCancelTarget(null);
              }}
              closeAriaLabel="Fechar confirmação de remoção"
            >
              <ConfirmModalPanel
                message={
                  <>
                    Remover «
                    {cancelTarget.original_name ?? title}
                    »? O documento sai da lista, mas as versões e o
                    histórico ficam preservados.
                    {data?.kind === "item"
                      ? " A exigência deste documento continua valendo."
                      : ""}
                  </>
                }
                confirmLabel="Remover documento"
                cancelLabel="Voltar"
                variant="danger"
                confirmBusy={uploading}
                confirmBusyLabel="Removendo…"
                onConfirm={confirmCancel}
                onCancel={() => setCancelTarget(null)}
                classNames={cfConfirmModalClassNames}
              />
            </CfDialog>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
