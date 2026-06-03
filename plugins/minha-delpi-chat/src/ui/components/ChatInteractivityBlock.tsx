import { useState } from "react";

import type { ChatMessageMetadata } from "../../data/api/chatTypes";
import { isExplainChartSuggestion, isExplainDashboardSuggestion } from "./chartExplain";
import { type ChatFollowUpSuggestion } from "./ChatFollowUpChips";
import type { TableRowMenuAction } from "./chatDrillDown";
import { ChatTableRowMenu } from "./ChatTableRowMenu";
import { menuAnchorRectFromElement, type MenuAnchorRect } from "./menuPositionUtils";

import "./ChatInteractivityBlock.css";
import "./ChatFollowUpChips.css";

type InteractivityPayload = NonNullable<ChatMessageMetadata["interactivity"]>;

type ChatInteractivityBlockProps = {
  interactivity: InteractivityPayload;
  onUseSuggestion?: (query: string) => void;
  onExplainChart?: () => void;
  onExplainDashboard?: () => void;
  onRecordClick?: (payload: { label: string; query: string; group?: string }) => void;
  /** Destaque suave quando há erro/vazio (Playbook 06 + 07). */
  variant?: "default" | "recovery";
};

const GROUP_LABELS: Record<string, string> = {
  consultar: "Consultar",
  visualizar: "Visualizar",
  exportar: "Exportar",
  formatar: "Formatar",
  corrigir: "Corrigir",
  ajuda: "Ajuda",
  web: "Web",
  lousa: "Lousa",
  recuperar: "Recuperar",
  anexo: "Anexo",
  apresentacao: "Apresentação",
};

function flattenMore(
  more: InteractivityPayload["moreSuggestions"],
): Array<ChatFollowUpSuggestion & { menuGroup?: string }> {
  if (!more) {
    return [];
  }

  const items: Array<ChatFollowUpSuggestion & { menuGroup?: string }> = [];

  for (const [group, suggestions] of Object.entries(more)) {
    for (const suggestion of suggestions || []) {
      items.push({ ...suggestion, menuGroup: GROUP_LABELS[group] ?? group });
    }
  }

  return items;
}

export function ChatInteractivityBlock({
  interactivity,
  onUseSuggestion,
  onExplainChart,
  onExplainDashboard,
  onRecordClick,
  variant = "default",
}: ChatInteractivityBlockProps) {
  const [menu, setMenu] = useState<{
    anchor: { rect: MenuAnchorRect };
    actions: TableRowMenuAction[];
  } | null>(null);

  const primary = (interactivity.suggestions ?? []) as ChatFollowUpSuggestion[];
  const overflow = flattenMore(interactivity.moreSuggestions);

  if (!onUseSuggestion || (primary.length === 0 && overflow.length === 0)) {
    return null;
  }

  function handleSelect(suggestion: ChatFollowUpSuggestion) {
    if (suggestion.disabledReason) {
      return;
    }

    const query = String(suggestion.query || "").trim();

    if (!query) {
      return;
    }

    if (suggestion.requiresConfirmation) {
      const ok = window.confirm(
        suggestion.confirmationMessage ??
          "Confirma que deseja executar esta ação?",
      );

      if (!ok) {
        return;
      }
    }

    onRecordClick?.({
      label: suggestion.label,
      query,
      group: suggestion.group,
    });

    if (isExplainChartSuggestion(suggestion) && onExplainChart) {
      onExplainChart();
      return;
    }

    if (isExplainDashboardSuggestion(suggestion) && onExplainDashboard) {
      onExplainDashboard();
      return;
    }

    onUseSuggestion(query);
  }

  return (
    <div
      className={[
        "mdc-chat-interactivity",
        "mdc-chat-follow-up",
        variant === "recovery" ? "mdc-chat-interactivity--recovery" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="group"
      aria-label="Ações sugeridas após a resposta"
    >
      {interactivity.contextBar?.summary ? (
        <p className="mdc-chat-interactivity__context" title="Contexto ativo">
          {interactivity.contextBar.summary}
        </p>
      ) : null}
      <p className="mdc-chat-follow-up__label">
        {variant === "recovery" ? "Recuperar consulta" : "Próximos passos"}
      </p>
      <div className="mdc-chat-follow-up__chips">
        {primary.map((suggestion) => {
          const disabled = Boolean(suggestion.disabledReason);

          return (
            <button
              key={suggestion.id ?? `${suggestion.label}-${suggestion.query}`}
              type="button"
              className={[
                "mdc-chat-follow-up__chip",
                suggestion.kind === "primary" ? "mdc-chat-follow-up__chip--primary" : "",
                disabled ? "mdc-chat-follow-up__chip--disabled" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              disabled={disabled}
              title={suggestion.disabledReason ?? suggestion.tooltip ?? suggestion.label}
              onClick={() => handleSelect(suggestion)}
            >
              {suggestion.label}
            </button>
          );
        })}

        {overflow.length ? (
          <button
            type="button"
            className="mdc-chat-follow-up__chip mdc-chat-follow-up__chip--more"
            onClick={(event) => {
              event.stopPropagation();
              setMenu({
                anchor: {
                  rect: menuAnchorRectFromElement(event.currentTarget),
                },
                actions: overflow.map(
                  (item): TableRowMenuAction => ({
                    id: item.id ?? item.query,
                    label: item.menuGroup
                      ? `${item.label} · ${item.menuGroup}`
                      : item.label,
                    query: item.query,
                  }),
                ),
              });
            }}
          >
            Mais opções
          </button>
        ) : null}
      </div>

      {menu ? (
        <ChatTableRowMenu
          actions={menu.actions}
          anchor={menu.anchor}
          onSelect={(query) => {
            const match = overflow.find((item) => item.query === query);

            if (match) {
              handleSelect(match);
            } else {
              onUseSuggestion(query);
            }

            setMenu(null);
          }}
          onClose={() => setMenu(null)}
          menuLabel="Mais opções de interatividade"
        />
      ) : null}
    </div>
  );
}
