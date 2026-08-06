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
  /** Rótulo do botão Voltar (default: Lista de Painéis). */
  backLabel?: string;
  /** Tooltip / aria do Voltar. */
  backHint?: string;
};

/** Voltar + Desfazer/refazer + Atualizar dados (quando a tela tem blocos de dados). */
export function DeckHistoryTabActions({ onBack, backLabel, backHint }: Props) {
  const history = useDeckEditorHistoryContext();
  const editor = useOptionalComunicadoEditor();
  const resolvedBackLabel = backLabel?.trim() || HEADER.backLabel;
  const resolvedBackHint = backHint?.trim() || HEADER.back;
  const hasDataBlocks = Boolean(
    editor?.config?.blocks?.some((block) => isFetchableDataBlockType(block.type)),
  );
  const refreshing = Boolean(
    editor?.dataPreviewLoading || (editor?.refreshingSourceIds?.length ?? 0) > 0,
  );
  /*
   * Slide custom: Desfazer/Refazer = pilha local imediata do editor.
   * Sem passo local (ex.: a IA criou/apagou slide), cai nos ponteiros de revisão
   * do deck — mesma precedência do teclado (comunicado 60 → deck 50).
   */
  const deckCanUndo = Boolean(history?.canUndo && !history.restoring);
  const deckCanRedo = Boolean(history?.canRedo && !history.restoring);
  const canUndo = editor ? Boolean(editor.canUndo) || deckCanUndo : deckCanUndo;
  const canRedo = editor ? Boolean(editor.canRedo) || deckCanRedo : deckCanRedo;

  if (!history && !onBack && !hasDataBlocks && !editor) return null;

  return (
    <div className="td-deck-chrome__history" role="group" aria-label="Ações do editor">
      {onBack ? (
        <HintAction hint={resolvedBackHint} ariaLabel={resolvedBackHint}>
          <button
            type="button"
            className="td-deck-chrome__history-btn td-deck-chrome__history-btn--back"
            onClick={onBack}
            aria-label={resolvedBackHint}
          >
            <ArrowLeft size={14} aria-hidden="true" />
            <span className="td-deck-chrome__history-btn-label">{resolvedBackLabel}</span>
          </button>
        </HintAction>
      ) : null}
      {history || editor ? (
        <>
          <ShortcutTip shortcutId="undo" placement="bottom" offsetX={-18}>
            <span>
              <HintAction hint={hintWithShortcut(H.undo, "undo")} ariaLabel="Desfazer">
                <button
                  type="button"
                  className="td-deck-chrome__history-btn"
                  disabled={!canUndo}
                  onClick={() => {
                    if (editor?.canUndo) {
                      editor.undo();
                      return;
                    }
                    void history?.undo();
                  }}
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
                  disabled={!canRedo}
                  onClick={() => {
                    if (editor?.canRedo) {
                      editor.redo();
                      return;
                    }
                    void history?.redo();
                  }}
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
