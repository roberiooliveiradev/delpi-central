import type { ChatToolCall } from "../../data/api/chatTypes";
import { getAvailableFormatsFromToolCalls } from "./chatPresentation";

export type AssistantMessageMenuAction = {
  id: string;
  label: string;
  query: string;
};

export function buildAssistantMessageMenuActions(
  toolCalls: ChatToolCall[],
): AssistantMessageMenuAction[] {
  const formats = new Set(getAvailableFormatsFromToolCalls(toolCalls));
  const actions: AssistantMessageMenuAction[] = [];

  if (formats.has("table")) {
    actions.push({
      id: "format-table",
      label: "Ver em tabela",
      query: "mostre o último resultado em tabela",
    });
  }

  if (formats.has("chart")) {
    actions.push({
      id: "format-chart",
      label: "Ver em gráfico",
      query: "mostre o último resultado em gráfico",
    });
  }

  if (formats.has("text")) {
    actions.push({
      id: "format-text",
      label: "Ver em texto",
      query: "mostre o último resultado em texto",
    });
  }

  if (formats.has("tree")) {
    actions.push({
      id: "format-tree",
      label: "Ver em árvore",
      query: "mostre o último resultado em árvore",
    });
  }

  if (formats.size >= 1) {
    actions.push({
      id: "canvas",
      label: "Colocar na lousa",
      query: "coloque o resultado acima na lousa",
    });
  }

  const seen = new Set<string>();

  return actions.filter((action) => {
    if (seen.has(action.query)) {
      return false;
    }

    seen.add(action.query);
    return true;
  });
}
