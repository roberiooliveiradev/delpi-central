import { useState } from "react";
import {
  Building2,
  CalendarRange,
  LayoutGrid,
  Layout,
  MessageSquare,
  Package,
  SlidersHorizontal,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { contextChipKey, contextChipKindClass } from "../chatActiveContext";
import {
  buildContextChipMenuActions,
  buildContextChipQuery,
} from "./chatContextChipActions";
import { ChatTableRowMenu } from "./ChatTableRowMenu";
import "./ChatContextBar.css";

export type ChatContextChip = {
  label: string;
  kind: string;
  value: string;
};

type ChatContextBarProps = {
  chips: ChatContextChip[];
  summary?: string | null;
  preferenceHint?: string | null;
  onClearContext?: () => void;
  onDismissChip?: (chip: ChatContextChip) => void;
  onChipAction?: (query: string) => void;
};

const CHIP_KIND_ICONS: Record<string, LucideIcon> = {
  product: Package,
  branch: Building2,
  warehouse: Building2,
  format: LayoutGrid,
  tone: MessageSquare,
  preference: SlidersHorizontal,
  period: CalendarRange,
  canvas: Layout,
  email: MessageSquare,
  textCorrection: SlidersHorizontal,
};

function chipIconForKind(kind: string): LucideIcon {
  return CHIP_KIND_ICONS[kind] ?? SlidersHorizontal;
}

export function ChatContextBar({
  chips,
  summary,
  preferenceHint,
  onClearContext,
  onDismissChip,
  onChipAction,
}: ChatContextBarProps) {
  const [chipMenu, setChipMenu] = useState<{
    anchor: { x: number; y: number };
    actions: ReturnType<typeof buildContextChipMenuActions>;
  } | null>(null);

  if (!chips.length) {
    return null;
  }

  const interactive = Boolean(onChipAction);
  const showClear = Boolean(onClearContext) && chips.length > 0;

  function openChipMenu(chip: ChatContextChip, clientX: number, clientY: number) {
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
      anchor: { x: clientX, y: clientY },
      actions,
    });
  }

  return (
    <div className="mdc-chat-context-bar" aria-label="Contexto ativo da conversa">
      <div className="mdc-chat-context-bar__heading">
        <span className="mdc-chat-context-bar__label">Contexto</span>
        {summary ? (
          <span className="mdc-chat-context-bar__summary" title={summary}>
            {summary}
          </span>
        ) : null}
      </div>
      {preferenceHint ? (
        <span className="mdc-chat-context-bar__preference" title={preferenceHint}>
          {preferenceHint}
        </span>
      ) : null}

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
                  onClick={(event) => openChipMenu(chip, event.clientX, event.clientY)}
                  onContextMenu={(event) => {
                    event.preventDefault();
                    openChipMenu(chip, event.clientX, event.clientY);
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

      {chipMenu && onChipAction ? (
        <ChatTableRowMenu
          actions={chipMenu.actions}
          anchor={chipMenu.anchor}
          onSelect={onChipAction}
          onClose={() => setChipMenu(null)}
          menuLabel="Ações do contexto"
        />
      ) : null}
    </div>
  );
}
