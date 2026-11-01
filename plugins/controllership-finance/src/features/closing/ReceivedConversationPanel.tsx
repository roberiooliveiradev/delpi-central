/**
 * Conversa compartilhada do documento liberado — experiência do
 * destinatário externo (DRE-019, doc 112 §54 N3).
 *
 * Espelha `DocumentConversationPanel` (U9) nos mesmos componentes do
 * kit, mas consome exclusivamente a projeção autorizada
 * `/closing/received-documents/*`:
 * - a superfície só transporta `audience=SHARED` — mensagens internas
 *   da Controladoria nunca chegam a esta experiência;
 * - a mensagem só aparece na tela APÓS confirmação do backend;
 * - retry reutiliza a mesma `idempotencyKey` enquanto o texto não
 *   mudar — o backend deduplica, nunca duplica;
 * - sem resolução de perfil de diretório: a identidade exibida é o
 *   `author_name` gravado pelo servidor (fallback «Participante») —
 *   o lookup de participantes é contrato interno (`.access`), fora do
 *   boundary do destinatário;
 * - uma mensagem não valida documento, não encerra solicitação de
 *   ajuste e não altera pacote nem fechamento.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ApiError } from "../../api/httpClient";
import {
  listReceivedDocumentMessages,
  postReceivedDocumentMessage,
  type ReceivedMessage,
} from "../../api/receivedDocumentsApi";
import { CfFeedbackMessage } from "../../app/cfFeedbackUi";
import {
  CF_PORTAL_SCOPE,
  CfMentionComposer,
  CfMessageThread,
} from "../../app/controllershipFinanceUi";
import { formatDateTime } from "../../utils/formatters";
import type { MessageThreadItem } from "@delpi/plugin-ui/index";

const COMPOSER_LABELS = {
  placeholder: "Escreva uma mensagem sobre este documento…",
  sendAriaLabel: "Enviar mensagem",
  attachAriaLabel: "Anexar arquivo",
  mentionListAriaLabel: "Sugestões de menção",
  mentionEmptyLabel: "Nenhuma sugestão encontrada",
  formatToggleAriaLabel: "Formatação",
  formatBoldAriaLabel: "Negrito",
  formatItalicAriaLabel: "Itálico",
  formatStrikeAriaLabel: "Tachado",
  formatUnderlineAriaLabel: "Sublinhado",
  formatListAriaLabel: "Lista",
  formatOrderedListAriaLabel: "Lista numerada",
  formatCodeAriaLabel: "Código",
  formatQuoteAriaLabel: "Citação",
  formatLinkAriaLabel: "Link",
  formatAlignLeftAriaLabel: "Alinhar à esquerda",
  formatAlignCenterAriaLabel: "Centralizar",
  formatAlignRightAriaLabel: "Alinhar à direita",
  formatAlignJustifyAriaLabel: "Justificar",
  formatFontSizeAriaLabel: "Tamanho da fonte",
  formatFontSizeDecreaseAriaLabel: "Diminuir fonte",
  formatFontSizeIncreaseAriaLabel: "Aumentar fonte",
  formatUndoAriaLabel: "Desfazer",
  formatRedoAriaLabel: "Refazer",
  formatEmojiAriaLabel: "Emoji",
  emojiMenuAriaLabel: "Inserir emoji",
};

const SEND_ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para escrever nesta conversa.",
  document_not_found:
    "Documento não encontrado ou não liberado para você.",
  invalid_message:
    "A mensagem deve ter entre 1 e 4000 caracteres.",
  idempotency_conflict:
    "Esta mensagem mudou desde a primeira tentativa — revise e envie novamente.",
};

function toSendError(error: unknown): string {
  if (error instanceof ApiError) {
    return (
      (error.code && SEND_ERROR_MESSAGES[error.code]) || error.message
    );
  }
  return "Falha ao enviar a mensagem. Tente novamente.";
}

function toThreadItem(message: ReceivedMessage): MessageThreadItem {
  return {
    id: message.message_id,
    kind: "text",
    bodyText: message.body,
    createdAtLabel: message.created_at
      ? formatDateTime(message.created_at)
      : "",
    // Nome gravado pelo servidor; identificação neutra quando ausente —
    // UUID nunca é exibido como nome (UX-014 fallback honesto).
    authorName: message.author_name?.trim() || "Participante",
    authorUserId: message.author_subject,
    authorSrc: null,
    mine: Boolean(message.mine),
  };
}

export function ReceivedConversationPanel({
  period,
  documentId,
}: {
  period: string;
  documentId: string;
}) {
  const [loaded, setLoaded] = useState<ReceivedMessage[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadNonce, setLoadNonce] = useState(0);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [sentFeedback, setSentFeedback] = useState<string | null>(null);
  /** Chave idempotente da tentativa em andamento — retry do mesmo
   * texto reutiliza a chave (o backend deduplica). */
  const attemptRef = useRef<{ key: string; text: string } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listReceivedDocumentMessages(
      period,
      documentId,
      {},
      { signal: controller.signal },
    )
      .then((result) => {
        if (controller.signal.aborted) return;
        setLoaded(result.messages);
        setLoadError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setLoaded(null);
        setLoadError(
          err instanceof ApiError
            ? err.message
            : "Falha ao carregar a conversa.",
        );
      });
    return () => controller.abort();
  }, [period, documentId, loadNonce]);

  const handleSend = useCallback(
    (markdown: string) => {
      const text = markdown.trim();
      if (!text || sending) return;
      const attempt =
        attemptRef.current && attemptRef.current.text === text
          ? attemptRef.current
          : { key: crypto.randomUUID(), text };
      attemptRef.current = attempt;
      setSending(true);
      setSendError(null);
      setSentFeedback(null);
      postReceivedDocumentMessage(period, documentId, {
        body: text,
        idempotencyKey: attempt.key,
      })
        .then((message) => {
          setSending(false);
          attemptRef.current = null;
          setDraft("");
          setSentFeedback("Mensagem enviada.");
          setLoaded((current) => {
            const base = current ?? [];
            return base.some(
              (item) => item.message_id === message.message_id,
            )
              ? base
              : [...base, message];
          });
        })
        .catch((err: unknown) => {
          setSending(false);
          setSendError(toSendError(err));
        });
    },
    [period, documentId, sending],
  );

  const threadItems = useMemo(
    () => (loaded ?? []).map(toThreadItem),
    [loaded],
  );

  return (
    <div className="cf-document-conversation">
      {loadError ? (
        <CfFeedbackMessage intent="error" title="Conversa">
          {loadError}{" "}
          <button
            type="button"
            className="cf-link-button"
            onClick={() => setLoadNonce((n) => n + 1)}
          >
            Tentar novamente
          </button>
        </CfFeedbackMessage>
      ) : null}

      {loaded === null && !loadError ? (
        <p aria-live="polite">Carregando conversa…</p>
      ) : null}

      {loaded !== null ? (
        <CfMessageThread
          messages={threadItems}
          listAriaLabel="Conversa sobre o documento"
          emptyLabel="Nenhuma mensagem ainda. Você pode iniciar a conversa sobre este documento."
          bodyMode="markdown"
          showMineIdentity
          portalScopeClassName={CF_PORTAL_SCOPE}
          fill
        />
      ) : null}

      {sendError ? (
        <CfFeedbackMessage intent="error" title="Mensagem">
          {sendError}
        </CfFeedbackMessage>
      ) : null}
      {sentFeedback ? (
        <p className="cf-sr-only" role="status">
          {sentFeedback}
        </p>
      ) : null}

      <CfMentionComposer
        value={draft}
        onChange={setDraft}
        onSubmit={handleSend}
        disabled={sending}
        submitting={sending}
        showAttach={false}
        submitOnEnter={false}
        rows={3}
        labels={COMPOSER_LABELS}
        portalScopeClassName={CF_PORTAL_SCOPE}
      />
    </div>
  );
}
