import { HintAction } from "@delpi/plugin-ui/index";
import { ArrowLeft, History, Redo2, Undo2 } from "lucide-react";
import { useState } from "react";

import { getKeyboardShortcut, formatShortcutKeys } from "../../content/keyboardShortcuts";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDeckEditorHistoryContext } from "../../context/deckEditorHistoryContext";
import { ShortcutTip } from "../ShortcutTip";
import { DeckRevisionHistoryPanel } from "./DeckRevisionHistoryPanel";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const HEADER = TV_DASHBOARD_HELP_TOOLTIPS.header;

function hintWithShortcut(base: string, shortcutId: string): string {
  const entry = getKeyboardShortcut(shortcutId);
  if (!entry) return base;
  const keys = formatShortcutKeys(entry.keys);
  if (base.includes(keys) || base.includes(entry.keys)) return base;
  return `${base} (${keys})`;
}

type Props = {
  /** Voltar à lista de programações — antes de Desfazer/Refazer. */
  onBack?: () => void;
};

/** Voltar + Desfazer/refazer global — ícones compactos na faixa de abas. */
export function DeckHistoryTabActions({ onBack }: Props) {
  const history = useDeckEditorHistoryContext();
  const [panelOpen, setPanelOpen] = useState(false);
  if (!history && !onBack) return null;

  return (
    <div className="td-deck-chrome__history" role="group" aria-label="Histórico">
      {onBack ? (
        <HintAction hint={HEADER.back} ariaLabel={HEADER.back}>
          <button
            type="button"
            className="td-deck-chrome__history-btn td-deck-chrome__history-btn--back"
            onClick={onBack}
            aria-label={HEADER.back}
          >
            <ArrowLeft size={14} aria-hidden="true" />
            <span className="td-deck-chrome__history-btn-label">{HEADER.backLabel}</span>
          </button>
        </HintAction>
      ) : null}
      {history ? (
        <>
          <ShortcutTip shortcutId="undo" placement="bottom" offsetX={-18}>
            <span>
              <HintAction hint={hintWithShortcut(H.undo, "undo")} ariaLabel="Desfazer">
                <button
                  type="button"
                  className="td-deck-chrome__history-btn"
                  disabled={!history.canUndo || history.restoring}
                  onClick={() => void history.undo()}
                  aria-label="Desfazer"
                >
                  <Undo2 size={14} aria-hidden="true" />
                </button>
              </HintAction>
            </span>
          </ShortcutTip>
          <ShortcutTip shortcutId="redo" placement="bottom" offsetX={18}>
            <span>
              <HintAction hint={hintWithShortcut(H.redo, "redo")} ariaLabel="Refazer">
                <button
                  type="button"
                  className="td-deck-chrome__history-btn"
                  disabled={!history.canRedo || history.restoring}
                  onClick={() => void history.redo()}
                  aria-label="Refazer"
                >
                  <Redo2 size={14} aria-hidden="true" />
                </button>
              </HintAction>
            </span>
          </ShortcutTip>
          <HintAction hint="Abrir histórico de revisões" ariaLabel="Abrir histórico de revisões">
            <button
              type="button"
              className="td-deck-chrome__history-btn"
              onClick={() => setPanelOpen(true)}
              aria-label="Abrir histórico de revisões"
            >
              <History size={14} aria-hidden="true" />
            </button>
          </HintAction>
          <DeckRevisionHistoryPanel
            open={panelOpen}
            playlistId={history.playlistId}
            onClose={() => setPanelOpen(false)}
          />
        </>
      ) : null}
    </div>
  );
}
