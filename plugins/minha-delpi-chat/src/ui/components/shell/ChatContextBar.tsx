import { useState } from "react";
import {
  CalendarRange,
  ClipboardList,
  Eye,
  FileText,
  Layers,
  LayoutGrid,
  Layout,
  MessageCircleQuestion,
  MessageSquare,
  Plus,
  Reply,
  SlidersHorizontal,
  Target,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { contextChipKey, contextChipKindClass } from "../../chatActiveContext";
import {
  buildContextChipMenuActions,
  buildContextChipQuery,
} from "./chatContextChipActions";
import { ChatTableRowMenu } from "../shared/menus/ChatTableRowMenu";
import { menuAnchorRectFromElement } from "../shared/overlay/menuPositionUtils";
import "./ChatContextBar.css";

export type ChatContextChip = {
  label: string;
  kind: string;
  value: string;
  /** ID do item em userContextItems (remover da sessão). */
  itemId?: string;
};

type ChatContextBarProps = {
  chips: ChatContextChip[];
  summary?: string | null;
  preferenceHint?: string | null;
  onClearContext?: () => void;
  onDismissChip?: (chip: ChatContextChip) => void;
  onChipAction?: (query: string) => void;
  onAddContext?: () => void;
  onViewMemory?: () => void;
  onPinChip?: (chip: ChatContextChip) => void;
};

const CHIP_KIND_ICONS: Record<string, LucideIcon> = {
  context: Layers,
  format: LayoutGrid,
  tone: MessageSquare,
  preference: SlidersHorizontal,
  period: CalendarRange,
  canvas: Layout,
  email: MessageSquare,
  textCorrection: SlidersHorizontal,
  topic: Target,
  task: ClipboardList,
  attachment: FileText,
  note: FileText,
  table: LayoutGrid,
  file: FileText,
  knowledge: FileText,
  question: MessageCircleQuestion,
  answer: Reply,
  turn: MessageSquare,
};

function chipIconForKind(kind: string): LucideIcon {
  const normalized = kind.trim().toLowerCase();

  if (
    normalized === "context" ||
    normalized === "product" ||
    normalized === "branch" ||
    normalized === "warehouse"
  ) {
    return Layers;
  }

  return CHIP_KIND_ICONS[normalized] ?? FileText;
}

export function ChatContextBar({
  chips,
  summary,
  preferenceHint,
  onClearContext,
  onDismissChip,
  onChipAction,
  onAddContext,
  onViewMemory,
  onPinChip,
}: ChatContextBarProps) {
  const [chipMenu, setChipMenu] = useState<{
    chip: ChatContextChip;
    anchor: { rect: ReturnType<typeof menuAnchorRectFromElement> };
    actions: ReturnType<typeof buildContextChipMenuActions>;
  } | null>(null);

  const hasContextContent =
    chips.length > 0 ||
    Boolean(summary?.trim()) ||
    Boolean(preferenceHint?.trim());

  if (!hasContextContent && !onAddContext && !onViewMemory) {
    return null;
  }

  const interactive = Boolean(onChipAction);
  const showClear = Boolean(onClearContext) && chips.length > 0;
  const showAdd = Boolean(onAddContext);
  const actionsOnly = !hasContextContent;

  function openChipMenu(chip: ChatContextChip, element: HTMLElement) {
    if (!onChipAction) {
      return;
    }

    const actions = buildContextChipMenuActions(chip);

    if (actions.length <= 1) {
      const query = buildContextChipQuery(chip);

      if (query) {
        onChipAction(query);
      }

      return;
    }

    setChipMenu({
      chip,
      anchor: { rect: menuAnchorRectFromElement(element) },
      actions,
    });
  }

  return (
    <div
      className={[
        "mdc-chat-context-bar",
        actionsOnly ? "mdc-chat-context-bar--actions-only" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Contexto ativo da conversa"
    >
      {hasContextContent ? (
        <div className="mdc-chat-context-bar__heading">
          <span className="mdc-chat-context-bar__label">Contexto</span>
          {summary ? (
            <span className="mdc-chat-context-bar__summary" title={summary}>
              {summary}
            </span>
          ) : null}
        </div>
      ) : null}
      {preferenceHint ? (
        <span className="mdc-chat-context-bar__preference" title={preferenceHint}>
          {preferenceHint}
        </span>
      ) : null}

      {hasContextContent ? (
      <div className="mdc-chat-context-bar__chips" role="list">
        {chips.map((chip) => {
          const key = contextChipKey(chip);
          const query = interactive ? buildContextChipQuery(chip) : null;
          const isActionable = interactive && Boolean(query);
          const Icon = chipIconForKind(chip.kind);
          const kindClass = contextChipKindClass(chip.kind);

          const chipBody = (
            <>
              <Icon size={12} aria-hidden="true" className="mdc-chat-context-bar__chip-icon" />
              <span className="mdc-chat-context-bar__chip-text">{chip.label}</span>
            </>
          );

          if (isActionable) {
            return (
              <span key={key} role="listitem" className="mdc-chat-context-bar__chip-wrap">
                <button
                  type="button"
                  className={[
                    "mdc-chat-context-bar__chip",
                    "mdc-chat-context-bar__chip--action",
                    kindClass,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  title={`${chip.label} — clique para ações`}
                  onClick={(event) => openChipMenu(chip, event.currentTarget)}
                  onContextMenu={(event) => {
                    event.preventDefault();
                    openChipMenu(chip, event.currentTarget);
                  }}
                >
                  {chipBody}
                </button>
                {onDismissChip ? (
                  <button
                    type="button"
                    className="mdc-chat-context-bar__chip-dismiss"
                    title={`Remover ${chip.label} do contexto`}
                    aria-label={`Remover ${chip.label}`}
                    onClick={() => onDismissChip(chip)}
                  >
                    <X size={12} aria-hidden="true" />
                  </button>
                ) : null}
              </span>
            );
          }

          return (
            <span key={key} role="listitem" className="mdc-chat-context-bar__chip-wrap">
              <span className={["mdc-chat-context-bar__chip", kindClass].filter(Boolean).join(" ")}>
                {chipBody}
              </span>
              {onDismissChip ? (
                <button
                  type="button"
                  className="mdc-chat-context-bar__chip-dismiss"
                  title={`Remover ${chip.label} do contexto`}
                  aria-label={`Remover ${chip.label}`}
                  onClick={() => onDismissChip(chip)}
                >
                  <X size={12} aria-hidden="true" />
                </button>
              ) : null}
            </span>
          );
        })}
      </div>
      ) : null}

      <div className="mdc-chat-context-bar__actions">
        {showClear ? (
          <button
            type="button"
            className="mdc-chat-context-bar__clear"
            onClick={onClearContext}
            title="Limpar todo o contexto"
            aria-label="Limpar todo o contexto"
          >
            <X size={14} aria-hidden="true" />
          </button>
        ) : null}

        {onViewMemory ? (
          <button
            type="button"
            className="mdc-chat-context-bar__view-memory"
            onClick={onViewMemory}
            title="Ver memória usada nesta conversa"
            aria-label="Ver memória usada"
          >
            <Eye size={14} aria-hidden="true" />
          </button>
        ) : null}

        {showAdd ? (
          <button
            type="button"
            className="mdc-chat-context-bar__add"
            onClick={onAddContext}
            title="Adicionar texto, tabela ou arquivo ao contexto"
            aria-label="Adicionar ao contexto"
          >
            <Plus size={14} aria-hidden="true" />
          </button>
        ) : null}
      </div>

      {chipMenu && onChipAction ? (
        <ChatTableRowMenu
          actions={chipMenu.actions}
          anchor={chipMenu.anchor}
          onSelect={(query) => {
            const action = chipMenu.actions.find((item) => item.query === query);

            if (action?.id === "pin" && onPinChip) {
              onPinChip(chipMenu.chip);
            } else if (onChipAction) {
              onChipAction(query);
            }

            setChipMenu(null);
          }}
          onClose={() => setChipMenu(null)}
          menuLabel="Ações do contexto"
        />
      ) : null}
    </div>
  );
}
