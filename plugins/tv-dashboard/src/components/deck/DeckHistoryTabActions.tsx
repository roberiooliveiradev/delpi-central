import { HintAction } from "@delpi/plugin-ui/index";
import { isFetchableDataBlockType } from "@delpi/tv-dashboard-presentation";
import { ArrowLeft, Redo2, RefreshCw, Undo2 } from "lucide-react";

import { getKeyboardShortcut, formatShortcutKeys } from "../../content/keyboardShortcuts";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDeckEditorHistoryContext } from "../../context/deckEditorHistoryContext";
import { useOptionalComunicadoEditor } from "../comunicadoEditorContext";
import { ShortcutTip } from "../ShortcutTip";

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

/** Voltar + Desfazer/refazer + Atualizar dados (quando a tela tem blocos de dados). */
export function DeckHistoryTabActions({ onBack }: Props) {
  const history = useDeckEditorHistoryContext();
  const editor = useOptionalComunicadoEditor();
  const hasDataBlocks = Boolean(
    editor?.config?.blocks?.some((block) => isFetchableDataBlockType(block.type)),
  );
  const refreshing = Boolean(
    editor?.dataPreviewLoading || (editor?.refreshingSourceIds?.length ?? 0) > 0,
  );

  if (!history && !onBack && !hasDataBlocks) return null;

  return (
    <div className="td-deck-chrome__history" role="group" aria-label="Ações do editor">
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
        </>
      ) : null}
      {hasDataBlocks && editor ? (
        <HintAction hint={HEADER.refreshVisual} ariaLabel="Atualizar dados">
          <button
            type="button"
            className={[
              "td-deck-chrome__history-btn",
              refreshing ? "td-deck-chrome__history-btn--busy" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            disabled={refreshing}
            onClick={() => void editor.refreshDataPreview({ force: true })}
            aria-label="Atualizar dados"
            aria-busy={refreshing}
          >
            <RefreshCw size={14} aria-hidden="true" />
          </button>
        </HintAction>
      ) : null}
    </div>
  );
}
