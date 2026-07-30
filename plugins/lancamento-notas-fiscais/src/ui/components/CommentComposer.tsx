import { searchDirectoryUsers, type DirectoryUser } from "../../data/api/directoryApi";
import {
  detectActiveMention,
  filterMentionCandidates,
  insertMentionToken,
  type ActiveMention,
} from "../../domain/commentMentions";
import { formatPersonName } from "../../domain/formatPersonName";
import { useEffect, useRef, useState } from "react";

export type MentionSelection = {
  id: string;
  name: string;
};

type Props = {
  value: string;
  onChange: (value: string) => void;
  mentions: MentionSelection[];
  onMentionsChange: (mentions: MentionSelection[]) => void;
  disabled?: boolean;
  "data-testid"?: string;
};

export function CommentComposer({
  value,
  onChange,
  mentions,
  onMentionsChange,
  disabled = false,
  "data-testid": testId,
}: Props) {
  const [activeMention, setActiveMention] = useState<ActiveMention | null>(null);
  const [mentionResults, setMentionResults] = useState<DirectoryUser[]>([]);
  const [mentionSearching, setMentionSearching] = useState(false);
  const [mentionIndex, setMentionIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

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

  const syncMentionFromCursor = (nextValue: string, cursor: number) => {
    setActiveMention(detectActiveMention(nextValue, cursor));
  };

  const applyMention = (user: DirectoryUser) => {
    if (!activeMention) return;
    const displayName = formatPersonName(user.name.trim() || user.email) || user.email;
    const { nextValue, nextCursor } = insertMentionToken(
      value,
      activeMention.end,
      activeMention.start,
      displayName,
    );
    onChange(nextValue);
    onMentionsChange(
      mentions.some((m) => m.id === user.id)
        ? mentions
        : [...mentions, { id: user.id, name: displayName }],
    );
    setActiveMention(null);
    setMentionResults([]);
    window.requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(nextCursor, nextCursor);
    });
  };

  const showMentionMenu =
    Boolean(activeMention) && (mentionSearching || mentionResults.length > 0);

  return (
    <div className="lnf-comment-composer">
      <span className="lnf-comment-composer__hint">
        Use @ para mencionar alguém do Minha Delpi
      </span>
      <div className="lnf-comment-composer__field">
        <textarea
          ref={textareaRef}
          aria-label="Novo comentário"
          rows={3}
          value={value}
          disabled={disabled}
          data-testid={testId}
          onChange={(e) => {
            const next = e.target.value;
            onChange(next);
            syncMentionFromCursor(next, e.target.selectionStart ?? next.length);
          }}
          onClick={(e) => {
            const target = e.currentTarget;
            syncMentionFromCursor(target.value, target.selectionStart ?? 0);
          }}
          onKeyUp={(e) => {
            const target = e.currentTarget;
            if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) {
              syncMentionFromCursor(target.value, target.selectionStart ?? 0);
            }
          }}
          onKeyDown={(e) => {
            if (!showMentionMenu || mentionResults.length === 0) return;
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setMentionIndex((index) => (index + 1) % mentionResults.length);
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setMentionIndex(
                (index) =>
                  (index - 1 + mentionResults.length) % mentionResults.length,
              );
            } else if (e.key === "Enter" || e.key === "Tab") {
              e.preventDefault();
              const selected = mentionResults[mentionIndex];
              if (selected) applyMention(selected);
            } else if (e.key === "Escape") {
              e.preventDefault();
              setActiveMention(null);
              setMentionResults([]);
            }
          }}
        />
        {showMentionMenu ? (
          <ul
            className="lnf-comment-mention-menu"
            role="listbox"
            aria-label="Usuários para mencionar"
          >
            {mentionSearching && mentionResults.length === 0 ? (
              <li className="lnf-comment-mention-empty">Buscando…</li>
            ) : (
              mentionResults.map((user, index) => {
                const label = formatPersonName(user.name) || user.email;
                return (
                  <li key={user.id}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={index === mentionIndex}
                      className={
                        index === mentionIndex
                          ? "lnf-comment-mention-option is-active"
                          : "lnf-comment-mention-option"
                      }
                      onMouseDown={(ev) => {
                        ev.preventDefault();
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
        <ul className="lnf-comment-mention-chips" aria-label="Pessoas mencionadas">
          {mentions.map((mention) => (
            <li key={mention.id}>
              <span>@{mention.name}</span>
              <button
                type="button"
                className="lnf-comment-mention-chip-remove"
                aria-label={`Remover menção de ${mention.name}`}
                onClick={() =>
                  onMentionsChange(mentions.filter((item) => item.id !== mention.id))
                }
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
