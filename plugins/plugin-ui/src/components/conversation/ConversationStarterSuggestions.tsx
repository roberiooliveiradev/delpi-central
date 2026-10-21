import { useId } from "react";
import type { ReactNode } from "react";
import { BarChart3, BookOpen, Database, Search } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { HelpTooltip } from "../help/HelpTooltip";

/**
 * ConversationStarterSuggestions — optional question starters rendered
 * inside an empty-conversation reception, between the reception copy
 * and the composer (doc 93 §§3–14).
 *
 * Render-only chrome: `items` arrive already admitted by the consumer;
 * `onSelect` is an intent callback the consumer turns into a draft
 * edit — the component never submits, never fetches, and carries no
 * Core/Keycloak/MCP/capability knowledge. Items are presentation
 * fixtures, not capability claims: `discovery != approval`.
 *
 * Presentation contract (doc 93 §13): `regular` cards in up to two
 * columns on wide containers, denser `compact`/`minimal` layouts via
 * container queries on narrow surfaces (Companion Dock, 320–420 px)
 * and viewport-height fallbacks that reduce to 1 or 0 cards before
 * ever competing with the composer.
 *
 * CSS: `styles/conversation-starter-suggestions.css`
 * (`.delpi-ui-starter-suggestions*`).
 */

/** Semantic-visual allowlist — never a dynamic/arbitrary icon load. */
export type ConversationStarterSuggestionIconKey =
  | "data"
  | "concept"
  | "sources"
  | "analysis";

export type ConversationStarterSuggestion = {
  /** Stable UI identity — used as React key. */
  id: string;
  /** Short admitted label — sufficient without an icon. */
  title: string;
  /** Optional short detail; may be visually hidden in minimal mode. */
  description?: string;
  /** Editable text the consumer inserts into the controlled draft. */
  draftText: string;
  iconKey?: ConversationStarterSuggestionIconKey;
  /** Per-item availability — a disabled card is never actionable. */
  disabled?: boolean;
};

export type ConversationStarterSuggestionsDensity =
  | "default"
  | "compact";

export type ConversationStarterSuggestionsProps = {
  items: readonly ConversationStarterSuggestion[];
  /** Selection intent only — consumers fill the draft and focus the
   *  composer; submitting is never this component's job. */
  onSelect?: (item: ConversationStarterSuggestion) => void;
  density?: ConversationStarterSuggestionsDensity;
  /** Whole-set availability, e.g. composer busy/submitting. */
  disabled?: boolean;
  /** Real loading only — never simulated discovery. */
  loading?: boolean;
  /** Section label; hidden automatically when there is nothing to show. */
  label?: string;
  /** Optional honest hint rendered as a polite status line (e.g. the
   *  consumer's "draft already has text" feedback). */
  note?: ReactNode;
  /** Presentation cap applied after the consumer's eligibility filter —
   *  never an authorization decision. Default 4 (spec §13). */
  maxVisible?: number;
  className?: string;
};

export const STARTER_SUGGESTIONS_DEFAULT_LABEL =
  "Explore algumas possibilidades para começar";
export const STARTER_SUGGESTIONS_MAX_VISIBLE = 4;

const STARTER_SUGGESTION_ICONS: Record<
  ConversationStarterSuggestionIconKey,
  LucideIcon
> = {
  data: Database,
  concept: BookOpen,
  sources: Search,
  analysis: BarChart3,
};

export function ConversationStarterSuggestions({
  items,
  onSelect,
  density = "default",
  disabled = false,
  loading = false,
  label = STARTER_SUGGESTIONS_DEFAULT_LABEL,
  note,
  maxVisible = STARTER_SUGGESTIONS_MAX_VISIBLE,
  className,
}: ConversationStarterSuggestionsProps) {
  const labelId = useId();
  const visibleItems = items.slice(0, Math.max(0, maxVisible));

  // `hidden`/`empty`: no honest item → no grid, no label, no leftover
  // space. The reception and composer keep working untouched.
  if (!loading && visibleItems.length === 0) return null;

  const densityClass =
    density === "compact"
      ? " delpi-ui-starter-suggestions--compact"
      : "";
  const selectable = onSelect != null && !disabled;

  return (
    <section
      className={`delpi-ui-starter-suggestions${densityClass}${
        className ? ` ${className}` : ""
      }`}
      aria-labelledby={labelId}
      aria-busy={loading || undefined}
    >
      <p id={labelId} className="delpi-ui-starter-suggestions__label">
        {label}
      </p>
      {loading ? (
        <ul
          className="delpi-ui-starter-suggestions__grid"
          role="list"
          aria-hidden="true"
        >
          {[0, 1].map((index) => (
            <li key={index} className="delpi-ui-starter-suggestions__item">
              <span className="delpi-ui-starter-suggestions__card delpi-ui-starter-suggestions__card--skeleton">
                <span className="delpi-ui-starter-suggestions__skeleton-line" />
                <span className="delpi-ui-starter-suggestions__skeleton-line delpi-ui-starter-suggestions__skeleton-line--short" />
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <ul className="delpi-ui-starter-suggestions__grid" role="list">
          {visibleItems.map((item) => {
            const Icon = item.iconKey
              ? STARTER_SUGGESTION_ICONS[item.iconKey]
              : null;
            const cardDisabled = !selectable || item.disabled === true;
            return (
              <li
                key={item.id}
                className="delpi-ui-starter-suggestions__item"
              >
                <HelpTooltip
                  wrap
                  content={`Insere esta pergunta no rascunho para você revisar e editar antes de enviar: “${item.draftText}”`}
                >
                  <button
                    type="button"
                    className="delpi-ui-starter-suggestions__card"
                    disabled={cardDisabled}
                    onClick={
                      cardDisabled ? undefined : () => onSelect?.(item)
                    }
                  >
                    {Icon ? (
                      <span
                        className="delpi-ui-starter-suggestions__icon"
                        aria-hidden="true"
                      >
                        <Icon size={16} />
                      </span>
                    ) : null}
                    <span className="delpi-ui-starter-suggestions__card-text">
                      <span className="delpi-ui-starter-suggestions__card-title">
                        {item.title}
                      </span>
                      {item.description ? (
                        <span className="delpi-ui-starter-suggestions__card-description">
                          {item.description}
                        </span>
                      ) : null}
                    </span>
                  </button>
                </HelpTooltip>
              </li>
            );
          })}
        </ul>
      )}
      {note ? (
        <p className="delpi-ui-starter-suggestions__note" role="status">
          {note}
        </p>
      ) : null}
    </section>
  );
}
