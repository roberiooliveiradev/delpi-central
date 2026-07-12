import { useEffect, useRef, useState } from "react";
import { MessageSquarePlus } from "lucide-react";

import { addNcAction } from "../api/audit5sApi";
import { searchDirectoryUsers, type DirectoryUser } from "../api/directoryApi";
import type { NcBoardItem } from "../types/ncManagement";
import { shiftLabel } from "../constants/audit5s";
import { formatDisplayDate } from "../utils/dates";
import { formatPersonName } from "../utils/formatPersonName";
import {
  detectActiveMention,
  filterMentionCandidates,
  insertMentionToken,
  type ActiveMention,
} from "../utils/ncNoteMentions";
import { useNcBoardItemDetail } from "../hooks/useNcBoardItemDetail";
import { NcBoardModalShell } from "./NcBoardModalShell";
import { NcNoteMentionText } from "./NcNoteMentionText";

type Props = {
  item: NcBoardItem | null;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
};

type MentionSelection = {
  id: string;
  name: string;
};

function formatActionTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NcBoardNotesModal({ item, open, onClose, onSaved }: Props) {
  const { loading, error, actions, reload } = useNcBoardItemDetail(item, open);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [mentions, setMentions] = useState<MentionSelection[]>([]);
  const [activeMention, setActiveMention] = useState<ActiveMention | null>(null);
  const [mentionResults, setMentionResults] = useState<DirectoryUser[]>([]);
  const [mentionSearching, setMentionSearching] = useState(false);
  const [mentionIndex, setMentionIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const canAddNote = Boolean(item?.is_registered);
  const trimmedNote = note.trim();

  useEffect(() => {
    if (!open) {
      setNote("");
      setMentions([]);
      setActiveMention(null);
      setMentionResults([]);
      setSubmitError(null);
    }
  }, [open, item?.id]);

  useEffect(() => {
    const query = activeMention?.query ?? "";
    if (!activeMention || query.trim().length < 1) {
      setMentionResults([]);
      setMentionSearching(false);
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setMentionSearching(true);
      void searchDirectoryUsers(query, 8, controller.signal, { minLength: 1 })
        .then((items) => {
          if (!controller.signal.aborted) {
            const excludeIds = new Set(mentions.map((m) => m.id));
            setMentionResults(
              filterMentionCandidates(items, query, excludeIds).map((item) => ({
                id: item.id,
                name: item.name,
                email: item.email,
              })),
            );
            setMentionIndex(0);
          }
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setMentionResults([]);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setMentionSearching(false);
          }
        });
    }, 220);

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [activeMention, mentions]);

  const syncMentionFromCursor = (value: string, cursor: number) => {
    setActiveMention(detectActiveMention(value, cursor));
  };

  const applyMention = (user: DirectoryUser) => {
    if (!activeMention) return;
    const displayName = formatPersonName(user.name.trim() || user.email) || user.email;
    const { nextValue, nextCursor } = insertMentionToken(
      note,
      activeMention.end,
      activeMention.start,
      displayName,
    );
    setNote(nextValue);
    setMentions((current) => {
      if (current.some((item) => item.id === user.id)) return current;
      return [...current, { id: user.id, name: displayName }];
    });
    setActiveMention(null);
    setMentionResults([]);
    window.requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(nextCursor, nextCursor);
    });
  };

  const handleSubmit = async () => {
    if (!item?.is_registered || trimmedNote.length < 3) return;

    setSaving(true);
    setSubmitError(null);
    try {
      await addNcAction(
        item.id,
        trimmedNote,
        mentions.map((mention) => mention.id),
      );
      setNote("");
      setMentions([]);
      setActiveMention(null);
      await reload();
      onSaved();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Erro ao registrar observação.");
    } finally {
      setSaving(false);
    }
  };

  if (!item) return null;

  const meta = `${item.audit_code} · ${item.area_name} · ${shiftLabel(item.shift)} · ${formatDisplayDate(item.audit_date)}`;
  const showMentionMenu = Boolean(activeMention) && (mentionSearching || mentionResults.length > 0);

  return (
    <NcBoardModalShell
      open={open}
      title="Notas da NC"
      titleId="a5s-nc-board-notes-title"
      meta={meta}
      icon={<MessageSquarePlus size={20} aria-hidden />}
      onClose={onClose}
      dialogClassName="a5s-nc-board-treat-dialog--notes"
      footer={
        <>
          <button type="button" className="a5s-btn a5s-btn--ghost" onClick={onClose}>
            Fechar
          </button>
          <button
            type="button"
            className="a5s-btn"
            disabled={!canAddNote || saving || trimmedNote.length < 3}
            onClick={() => {
              void handleSubmit();
            }}
          >
            {saving ? "Salvando…" : "Registrar nota"}
          </button>
        </>
      }
    >
      <div className="a5s-nc-board-treat-dialog__body">
        {!canAddNote ? (
          <div className="a5s-alert a5s-alert--warning">
            Registre o plano de ação em <strong>Atualizar</strong> antes de incluir observações no
            histórico.
          </div>
        ) : null}

        {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}
        {submitError ? <div className="a5s-alert a5s-alert--error">{submitError}</div> : null}

        <label className="a5s-nc-notes__composer">
          <span className="a5s-nc-notes__composer-label">Nova observação</span>
          <span className="a5s-nc-notes__composer-hint">
            Use @ para mencionar alguém — a pessoa recebe notificação com o texto da nota.
          </span>
          <div className="a5s-nc-notes__composer-field">
            <textarea
              ref={textareaRef}
              value={note}
              rows={4}
              disabled={!canAddNote || saving}
              placeholder="Descreva o andamento, decisão ou contexto que deve ficar no histórico da ficha… Use @nome para mencionar."
              onChange={(event) => {
                const next = event.target.value;
                setNote(next);
                syncMentionFromCursor(next, event.target.selectionStart ?? next.length);
              }}
              onClick={(event) => {
                syncMentionFromCursor(event.currentTarget.value, event.currentTarget.selectionStart);
              }}
              onKeyUp={(event) => {
                if (event.key === "Escape") {
                  setActiveMention(null);
                  return;
                }
                syncMentionFromCursor(event.currentTarget.value, event.currentTarget.selectionStart);
              }}
              onKeyDown={(event) => {
                if (!showMentionMenu || mentionResults.length === 0) return;
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setMentionIndex((index) => (index + 1) % mentionResults.length);
                } else if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setMentionIndex(
                    (index) => (index - 1 + mentionResults.length) % mentionResults.length,
                  );
                } else if (event.key === "Enter" || event.key === "Tab") {
                  event.preventDefault();
                  const selected = mentionResults[mentionIndex];
                  if (selected) applyMention(selected);
                } else if (event.key === "Escape") {
                  event.preventDefault();
                  setActiveMention(null);
                }
              }}
            />
            {showMentionMenu ? (
              <ul className="a5s-nc-notes__mention-menu" role="listbox" aria-label="Usuários para mencionar">
                {mentionSearching && mentionResults.length === 0 ? (
                  <li className="a5s-nc-notes__mention-empty">Buscando…</li>
                ) : (
                  mentionResults.map((user, index) => {
                    const label = formatPersonName(user.name) || user.name || user.email;
                    return (
                      <li key={user.id}>
                        <button
                          type="button"
                          role="option"
                          aria-selected={index === mentionIndex}
                          className={
                            index === mentionIndex
                              ? "a5s-nc-notes__mention-option is-active"
                              : "a5s-nc-notes__mention-option"
                          }
                          onMouseDown={(event) => {
                            event.preventDefault();
                            applyMention(user);
                          }}
                        >
                          <strong>{label}</strong>
                          <span>{user.email}</span>
                        </button>
                      </li>
                    );
                  })
                )}
              </ul>
            ) : null}
          </div>
          {mentions.length > 0 ? (
            <ul className="a5s-nc-notes__mention-chips" aria-label="Pessoas mencionadas">
              {mentions.map((mention) => (
                <li key={mention.id}>
                  <span>@{mention.name}</span>
                  <button
                    type="button"
                    className="a5s-nc-notes__mention-chip-remove"
                    aria-label={`Remover menção de ${mention.name}`}
                    onClick={() => {
                      setMentions((current) => current.filter((item) => item.id !== mention.id));
                    }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </label>

        <section className="a5s-nc-notes__history">
          <h3>Histórico</h3>
          {loading ? (
            <p className="a5s-nc-board-treat-dialog__loading">Carregando histórico…</p>
          ) : actions.length === 0 ? (
            <p className="a5s-nc-ficha__empty">Nenhuma observação registrada ainda.</p>
          ) : (
            <ol className="a5s-nc-ficha__history">
              {actions.map((action) => (
                <li key={action.id} className="a5s-nc-ficha__history-item">
                  <div className="a5s-nc-ficha__history-head">
                    <strong>
                      {formatPersonName(action.actor_display_name) || action.actor_display_name}
                    </strong>
                    <time dateTime={action.created_at}>{formatActionTimestamp(action.created_at)}</time>
                  </div>
                  <NcNoteMentionText text={action.description} />
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </NcBoardModalShell>
  );
}
