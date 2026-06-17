import type { ChatContextChip } from "./ChatContextBar";
import type { TableRowMenuAction } from "../presentation/chatDrillDown";
import {
  inferContextChipOperationalRole,
  isPinnableContextKind,
} from "../../chatActiveContext";

const PRODUCT_CODE = "{{productCode}}";

export function buildContextChipQuery(chip: ChatContextChip): string | null {
  const value = String(chip.value ?? "").trim();

  if (!value) {
    return null;
  }

  const role = inferContextChipOperationalRole(chip);

  if (role === "product") {
    return `qual o estoque do produto ${PRODUCT_CODE}?`;
  }

  if (role === "branch") {
    return `filtre pela filial ${value}`;
  }

  if (role === "warehouse") {
    return `filtre pelo armazém ${value}`;
  }

  switch (chip.kind) {
    case "period":
      if (value === "last_30_days") {
        return "use os últimos 30 dias";
      }
      if (value === "last_7_days") {
        return "use os últimos 7 dias";
      }
      return `use o mesmo período (${value})`;
    case "canvas":
      return "corrija o texto da lousa";
    case "format":
      if (value === "table") {
        return "mostre em tabela";
      }

      return null;
    case "tone":
      if (value === "direct") {
        return "responda de forma mais direta";
      }

      if (value === "simple") {
        return "use linguagem mais simples";
      }

      if (value === "formal") {
        return "use tom formal";
      }

      return null;
    case "preference":
      if (value === "final_only") {
        return "entregue só a versão final, sem explicações longas";
      }

      return null;
    default:
      return null;
  }
}

/** Playbook interatividade — Fase 4: menu por chip de contexto. */
export function buildContextChipMenuActions(chip: ChatContextChip): TableRowMenuAction[] {
  const value = String(chip.value ?? "").trim();

  if (!value) {
    return [];
  }

  const actions: TableRowMenuAction[] = [];
  const primary = buildContextChipQuery(chip);

  if (primary) {
    actions.push({
      id: "primary",
      label: "Consultar",
      query: primary,
    });
  }

  const role = inferContextChipOperationalRole(chip);

  if (role === "product") {
    actions.push(
      {
        id: "stock",
        label: "Ver estoque",
        query: `qual o estoque do produto ${PRODUCT_CODE}?`,
      },
      {
        id: "suppliers",
        label: "Ver fornecedores",
        query: `liste os fornecedores do produto ${PRODUCT_CODE}`,
      },
      {
        id: "structure",
        label: "Ver estrutura",
        query: `mostre a estrutura do produto ${PRODUCT_CODE}`,
      },
      {
        id: "summary",
        label: "Resumo do produto",
        query: `resumo do produto ${PRODUCT_CODE}`,
      },
    );
  } else if (role === "branch") {
    actions.push(
      {
        id: "filter-branch",
        label: "Filtrar nesta filial",
        query: `filtre pela filial ${value}`,
      },
      {
        id: "stock-branch",
        label: "Estoque da filial",
        query: `qual o estoque total da filial ${value}?`,
      },
    );
  } else if (role === "warehouse") {
    actions.push(
      {
        id: "filter-warehouse",
        label: "Filtrar neste armazém",
        query: `filtre pelo armazém ${value}`,
      },
      {
        id: "stock-warehouse",
        label: "Estoque do armazém",
        query: `qual o estoque do armazém ${value}?`,
      },
    );
  }

  switch (chip.kind) {
    case "format":
      if (value === "table") {
        actions.push({
          id: "chart",
          label: "Ver como gráfico",
          query: "mostre o último resultado em gráfico",
        });
      } else if (value === "chart") {
        actions.push({
          id: "table",
          label: "Ver como tabela",
          query: "mostre o último resultado em tabela",
        });
      }
      break;
    case "period":
      actions.push({
        id: "same-period",
        label: "Mesmo período",
        query: buildContextChipQuery(chip) ?? "use o mesmo período",
      });
      break;
    case "canvas":
      actions.push(
        { id: "fix-canvas", label: "Corrigir lousa", query: "corrija o texto da lousa" },
        { id: "short-canvas", label: "Versão curta", query: "faça uma versão curta da lousa" },
      );
      break;
    case "preference":
    case "tone":
    case "format":
    case "email":
    case "textCorrection":
      actions.push({
        id: "edit-preference",
        label: "Editar preferência",
        query: "quais preferências estão ativas? quero alterar",
      });
      break;
    case "topic":
    case "task":
      actions.push({
        id: "continue-task",
        label: "Continuar tarefa",
        query: "continue de onde paramos",
      });
      break;
    default:
      break;
  }

  if (isPinnableContextKind(chip.kind)) {
    actions.push({
      id: "pin",
      label: "Fixar no contexto",
      query: `fixar ${chip.label} no contexto da sessão`,
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
