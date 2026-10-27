/**
 * Conversa documental (U9) — Plano 113 §21 / doc-112 §43.
 *
 * Mensagens reais persistidas pela `controllership-finance-api` no
 * contexto (competência + documento): a Controladoria autorizada inicia
 * a conversa sem solicitação prévia da DRE. O componente é montado por
 * documento (`key={document_id}` no pai) — nenhum estado de uma
 * conversa pode vazar para outro documento.
 *
 * - A mensagem só aparece na tela APÓS confirmação do backend
 *   (`postDocumentMessage` retorna a linha persistida).
 * - Retry reutiliza a mesma `idempotencyKey` enquanto o texto não
 *   mudar — o backend deduplica (replay → `deduplicated`), nunca
 *   duplica a mensagem.
 * - Texto é preservado em caso de falha; envio não valida documento,
 *   não encerra solicitação e não libera nada para a Contabilidade.
 * - Autor/data vêm do servidor; `author_name` NULL → «Participante»
 *   (UUID nunca é exibido como nome).
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
  listDocumentMessages,
  postDocumentMessage,
  type DocumentMessage,
} from "../../api/documentsApi";
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
  document_not_found: "Documento não encontrado ou fora do escopo.",
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

function toThreadItem(message: DocumentMessage): MessageThreadItem {
  return {
    id: message.message_id,
    kind: "text",
    bodyText: message.body,
    createdAtLabel: message.created_at
      ? formatDateTime(message.created_at)
      : "",
    authorName: message.author_name || "Participante",
    authorUserId: message.author_subject,
    mine: Boolean(message.mine),
  };
}

export function DocumentConversationPanel({
  period,
  documentId,
}: {
  period: string;
  documentId: string;
}) {
  const [loaded, setLoaded] = useState<DocumentMessage[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadNonce, setLoadNonce] = useState(0);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [sentFeedback, setSentFeedback] = useState<string | null>(null);
  /** Chave idempotente da tentativa em andamento — retry do mesmo texto
   * reutiliza a chave (o backend deduplica pelo par key+conteúdo). */
  const attemptRef = useRef<{ key: string; text: string } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listDocumentMessages(period, documentId, {}, {
      signal: controller.signal,
    })
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
      postDocumentMessage(period, documentId, {
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
          // Rascunho preservado; a mesma chave só vale para o mesmo
          // texto — edição gera chave nova na próxima tentativa.
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
